"""
FixedLanceDBDocumentStore
~~~~~~~~~~~~~~~~~~~~~~~~~
Drop-in subclass of LanceDBDocumentStore that fixes the pyo3_async_runtimes.RustPanic
triggered by DuplicatePolicy.OVERWRITE (and DuplicatePolicy.NONE).

Root cause
----------
lancedb_haystack's write_documents passes a list of raw Python dicts to
``table.merge_insert(...).execute(doc_dicts)``.  LanceDB's Rust layer
(arrow-array) infers the Arrow schema from those dicts on the fly, and
when the table has nested struct columns (especially the ``_isempty``
sub-structs inside ``meta``), the inferred schema doesn't match the
table's actual schema, causing a struct-array cast panic:

    thread 'tokio-runtime-worker' panicked at arrow-array-57.x.x/src/cast.rs:...:
    struct array

Fix
---
Before calling ``merge_insert``, convert the list of dicts into a
``pa.Table`` using the table's *exact* schema via
``pa.Table.from_pylist(..., schema=table.schema)``.  This ensures the
Rust layer receives data that is already typed correctly.
"""
from typing import List

import pyarrow as pa
from haystack import Document
from haystack.document_stores.types import DuplicatePolicy
from lancedb_haystack import LanceDBDocumentStore
from lancedb_haystack.conversion.python_to_lancedb import convert_document_to_lancedb
from lancedb_haystack.filters import in_
from haystack.document_stores.errors import DuplicateDocumentError


class FixedLanceDBDocumentStore(LanceDBDocumentStore):
    """LanceDBDocumentStore with a working DuplicatePolicy.OVERWRITE.

    All other methods (filter_documents, perform_query, delete_documents, …)
    are inherited unchanged from LanceDBDocumentStore.
    """

    def write_documents(self, documents: List[Document], policy: DuplicatePolicy = DuplicatePolicy.NONE) -> int:
        """Write documents with schema-safe merge_insert for OVERWRITE policy.

        Identical to the parent implementation except that for OVERWRITE (and
        NONE) the list of dicts is cast to a ``pa.Table`` with the table's
        exact schema before being passed to ``merge_insert``.  This prevents
        the Rust arrow-array struct-cast panic.
        """
        if not documents:
            return 0

        # Resolve existing table or create it
        if self.table_exists():
            table = self.db.open_table(self._table_name)
            schema = table.schema
        else:
            from lancedb_haystack.document_store import _create_schema  # noqa: PLC0415
            schema = _create_schema(self._metadata_schema, self._embedding_dims)
            table = self.db.create_table(name=self._table_name, schema=schema, on_bad_vectors="fill", fill_value=0)

        # Convert Haystack Documents → dicts (same as parent)
        doc_dicts = [convert_document_to_lancedb(doc, schema) for doc in documents]

        # ------------------------------------------------------------------ #
        # Cast to a pa.Table with the *exact* table schema.                  #
        # This is the critical fix: without this cast, LanceDB's Rust layer  #
        # infers the schema from the dicts and panics on struct mismatches.   #
        # ------------------------------------------------------------------ #
        arrow_table = pa.Table.from_pylist(doc_dicts, schema=schema)

        if policy in (DuplicatePolicy.OVERWRITE, DuplicatePolicy.NONE):
            table.merge_insert("id").when_matched_update_all().when_not_matched_insert_all().execute(arrow_table)
            num_modified = len({doc["id"] for doc in doc_dicts})

        elif policy == DuplicatePolicy.SKIP:
            unique_new_ids = {doc["id"] for doc in doc_dicts}
            existing_ids = {
                res["id"]
                for res in table.search().where(in_("id", list(unique_new_ids))).select(["id"]).to_list()
            }
            num_modified = len(unique_new_ids - existing_ids)
            # SKIP still needs a schema-safe table for the merge path
            table.merge_insert("id").when_not_matched_insert_all().execute(arrow_table)

        elif policy == DuplicatePolicy.FAIL:
            unique_new_ids = {doc["id"] for doc in doc_dicts}
            existing_ids = {
                res["id"]
                for res in table.search().where(in_("id", list(unique_new_ids))).select(["id"]).to_list()
            }
            if existing_ids:
                raise DuplicateDocumentError()
            table.merge_insert("id").when_not_matched_insert_all().execute(arrow_table)
            num_modified = len(unique_new_ids)

        else:
            num_modified = 0

        table.create_fts_index("content", replace=True)
        return num_modified
