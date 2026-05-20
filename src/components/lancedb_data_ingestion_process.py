from lancedb_haystack import LanceDBDocumentStore
from lancedb.index import Bitmap,BTree,IvfFlat,IvfPq,IvfRq,IvfSq,IvfHnswPq,IvfHnswSq
from lancedb.common import VECTOR_COLUMN_NAME
from haystack.document_stores.types import DuplicatePolicy
from typing import Optional, Dict, Any, List, cast
from config.log_config import LoggerConfig
from haystack import component,Document
import json
import pyarrow as pa
from lancedb_haystack import LanceDBEmbeddingRetriever,LanceDBFTSRetriever
#from src.components.fixed_lancedb_document_store import FixedLanceDBDocumentStore
import lancedb
from src.components.data_chunk_to_document_conversion import DataChunkToDocumentConversion
from haystack.components.embedders import SentenceTransformersDocumentEmbedder
from haystack.components.writers import DocumentWriter

@component
class LanceDBDataIngestionProcess:
    def __init__(self,datasource_config,ikea_config,lancedb_config,doc_converter:DataChunkToDocumentConversion):
        self.datasource_config = datasource_config
        self.ikea_config = ikea_config
        self.lancedb_config = lancedb_config
        self.logger = LoggerConfig().get_logger()
        self.doc_converter = doc_converter
    
    @component.output_types(table_data=Optional[Dict[str, Any]])
    def run(self,input,table_data):
        results = {}
        datatypes = {
                "string":pa.string(),
                "int32":pa.int32(),
                "float16":pa.float16(),
                "float32":pa.float32(),
                "float64":pa.float64()}
        try:
            self.logger.info(f"Product table Count: {len(table_data['Product'])} and {len(table_data['assembly_steps_details'])}")
            table_def_lancedb_config = self.__get_table_definition_details()
            embedding_columns = []
            if "embedding_columns" in table_def_lancedb_config:
                embedding_columns = table_def_lancedb_config["embedding_columns"]
            for table_def_config in table_def_lancedb_config.get("table_definition",[]):
                columns_arr = []
                documents = self.doc_converter.run(table_data,table_def_config)
                documents_data = documents.get(table_def_config.get("table_name",""),[])
                self.logger.info(f"Total documents data generated for table {table_def_config.get('table_name','')} : {len(documents_data)}")
                self.logger.info(f"Documents data: {documents_data[3]}")
                self.logger.info(f"Processing table schema for table {table_def_config.get('table_name','')}...")
                for column_name,column_datatype in table_def_config["meta_fields"].items():
                    columns_arr.append((column_name, datatypes[column_datatype]))
                meta_schema = pa.struct(columns_arr)
                table_name = table_def_config.get('table_name', '')
                #lancedb_document_store = FixedLanceDBDocumentStore(database=self.lancedb_config.uri,table_name=table_name,
                #                metadata_schema = meta_schema,embedding_dims=table_def_config["embedding_dimension"])
                lancedb_document_store = LanceDBDocumentStore(database=self.lancedb_config.uri,table_name=table_name,
                                metadata_schema = meta_schema,embedding_dims=table_def_config["embedding_dimension"])
                #embedding_model_local_path = str(self.lancedb_config.embedding_model_save_path)
                document_embedder = SentenceTransformersDocumentEmbedder(
                    model=self.lancedb_config.embedding_model,
                    local_files_only=True,
                    device=None                    
                )
                document_embedder.warm_up()
                docs_with_embeddings = document_embedder.run(documents=documents_data)
                self.logger.info(f"Documents with embeddings: {docs_with_embeddings['documents'][0]}")
                # Upsert: pre-delete matching IDs then add with SKIP policy.DuplicatePolicy.OVERWRITE triggers merge_insert which panics in the
                # Rust arrow-array struct cast (lancedb_haystack bug). This pattern is semantically equivalent and uses the safe add() path instead.
                lancedb_db = lancedb.connect(self.lancedb_config.uri)
                if table_name in lancedb_db.table_names():
                    lancedb_table_pre = lancedb_db.open_table(table_name)
                    new_doc_ids = [doc.id for doc in docs_with_embeddings["documents"] if doc.id]
                    if new_doc_ids:
                        batch_size = 100  # avoid overly long SQL filter strings
                        for i in range(0, len(new_doc_ids), batch_size):
                            batch = new_doc_ids[i:i + batch_size]
                            #ids_filter = " OR ".join([f"id = '{doc_id}'" for doc_id in batch])
                            # Use SQL-style IN clause (cleaner & more efficient than OR)
                            ids_filter = f"id IN ({', '.join(repr(did) for did in batch)})"
                            self.logger.info(f"Deleting documents from table {table_name} with IDs filter: {ids_filter}")
                            try:
                                lancedb_table_pre.delete(ids_filter)
                            except Exception as del_ex:
                                self.logger.warning(f"Ignored error during pre-delete upsert in '{table_name}': {del_ex}")
                        self.logger.info(f"Pre-deleted {len(new_doc_ids)} existing docs from '{table_name}' for upsert")
                writer = DocumentWriter(document_store=lancedb_document_store, policy=DuplicatePolicy.SKIP)
                #writer = DocumentWriter(document_store=lancedb_document_store, policy=DuplicatePolicy.OVERWRITE)
                writer.run(documents=docs_with_embeddings["documents"])
                self.logger.info(f"Successfully wrote {lancedb_document_store.count_documents()} documents to table {table_name}")
                lancedb_table = lancedb_document_store.db.open_table(lancedb_document_store._table_name)
                #self.logger.info(f"Table schema: {lancedb_table.schema}")
                print("✅ Your Actual Metadata Schema:")
                for field in lancedb_table.schema.field("meta").type:
                    if not field.name.startswith("_"):  # Skip internal LanceDB fields
                        print(f"  • {field.name:35s} → {field.type}")
                vector_idx_created = False
                if "index_config" in table_def_config:
                    self.create_index_table(lancedb_document_store,table_def_config["index_config"],lancedb_document_store.count_documents(),table_def_config["embedding_dimension"])
                    # Only wait if any vector_index entry exists in the index config
                    vector_idx_created = "vector_index" in table_def_config["index_config"]
                if vector_idx_created:
                    try:
                        lancedb_table.wait_for_index(["vector_idx"])
                    except RuntimeError as wait_err:
                        self.logger.warning(f"wait_for_index timed out for table {table_name} (index may still be building in background): {wait_err}")
                lancedb_table = lancedb.connect(self.lancedb_config.uri)
                lancedb_table = lancedb_table.open_table(table_name)
                lancedb_table.optimize()
                self.logger.info(f"List Indexes: \n {lancedb_table.list_indices()}")
                self.logger.info(f"Table count: {lancedb_table.count_rows()}")
                results[table_name] = lancedb_table.count_rows()
            return results
        except Exception as e:
            self.logger.error(f"Error in LanceDBDataIngestionProcess: {e}",exc_info=True)
            return results
    

    def __get_table_definition_details(self):
        try:
            column_mapping_cfg = {}
            with open(self.datasource_config.table_definition_lancedb_filepath, 'r') as f:
                column_mapping_cfg = json.load(f)
            return column_mapping_cfg
        except Exception as e:
            self.logger.error(f"Error getting column mapping details: {e}",exc_info=True)
            return {}


    def create_index_table(self,lancedb_document_store,index_config,num_rows,embedding_dimension):
        try:
            self.logger.info(f"Creating index for table {lancedb_document_store._table_name}...")
            table = lancedb_document_store.db.open_table(lancedb_document_store._table_name)
            for idx_type, index_columns in index_config.items():
                if idx_type == "FTS":
                    for index_col in index_columns:
                        table.create_fts_index(index_col, replace = True)
                elif idx_type == "BTREE":
                    for index_col in index_columns:
                        table.create_scalar_index(index_col, index_type="BTREE", replace=True)
                elif idx_type == "Bitmap":
                    for index_col in index_columns:
                        table.create_scalar_index(index_col, index_type="BITMAP", replace=True)
                elif idx_type == "vector_index":
                    for idx_cfg in index_columns:
                        if idx_cfg['index_type'] == 'IVF_PQ':
                            num_partitions = idx_cfg["num_partitions"] if "num_partitions" in idx_cfg else 8 if num_rows > 100 and num_rows < 100000 else max(16, int(num_rows//4096))
                            table.create_index(vector_column_name=idx_cfg["column_name"], index_type=idx_cfg['index_type'], metric=idx_cfg.get("metric", "l2"), num_partitions=num_partitions, num_sub_vectors=int(embedding_dimension//8), replace=True)
                        elif idx_cfg['index_type'] == 'IVF_RQ':
                            num_partitions = idx_cfg["num_partitions"] if "num_partitions" in idx_cfg else 8 if num_rows > 100 and num_rows < 100000 else max(16, int(num_rows//4096))
                            #table.create_index(idx_cfg["column_name"],config=IvfRq(distance_type=idx_cfg.get('metric',"l2"),num_partitions=max(16,(int(num_rows//4096)))))
                            table.create_index(vector_column_name=idx_cfg["column_name"], index_type=idx_cfg['index_type'], metric=idx_cfg.get("metric", "l2"), num_partitions=num_partitions, replace=True)
                        elif idx_cfg['index_type'] == 'IVF_HNSW_FLAT':
                            num_partitions = idx_cfg["num_partitions"] if "num_partitions" in idx_cfg else 8 if num_rows > 100 and num_rows < 100000 else max(16, int(num_rows//1048576))
                            #table.create_index(idx_cfg["column_name"],config=IvfFlat(distance_type=idx_cfg.get('metric',"l2"),num_partitions=max(16,(int(num_rows//1048576)))))
                            table.create_index(vector_column_name=idx_cfg["column_name"], index_type=idx_cfg['index_type'], metric=idx_cfg.get("metric", "l2"), num_partitions=num_partitions, replace=True)
                        elif idx_cfg['index_type'] == 'IVF_HNSW_PQ':
                            num_partitions = idx_cfg["num_partitions"] if "num_partitions" in idx_cfg else 8 if num_rows > 100 and num_rows < 100000 else max(16, int(num_rows//1048576))
                            #table.create_index(idx_cfg["column_name"],config=IvfHnswPq(distance_type=idx_cfg.get('metric',"l2"),num_partitions=max(16,int(num_rows//1048576))))
                            table.create_index(vector_column_name=idx_cfg["column_name"], index_type=idx_cfg['index_type'], metric=idx_cfg.get("metric", "l2"), num_partitions=num_partitions, num_sub_vectors=int(embedding_dimension//8), replace=True)
                        elif idx_cfg['index_type'] == 'IVF_HNSW_RQ':
                            num_partitions = idx_cfg["num_partitions"] if "num_partitions" in idx_cfg else 8 if num_rows > 100 and num_rows < 100000 else max(16, int(num_rows//1048576))
                            #table.create_index(idx_cfg["column_name"],config=IvfHnswSq(distance_type=idx_cfg.get('metric',"l2"),num_partitions=max(16,int(num_rows//1048576))))
                            table.create_index(vector_column_name=idx_cfg["column_name"], index_type=idx_cfg['index_type'], metric=idx_cfg.get("metric", "l2"), num_partitions=num_partitions, replace=True)
                        elif idx_cfg['index_type'] == 'IVF_SQ':
                            num_partitions = idx_cfg["num_partitions"] if "num_partitions" in idx_cfg else 8 if num_rows > 100 and num_rows < 100000 else max(16, int(num_rows//4096))
                            #table.create_index(idx_cfg['column_name'], config= IvfSq(distance_type=idx_cfg.get('metric',"l2"),num_partitions=max(16,int(num_rows//4096))))
                            table.create_index(vector_column_name=idx_cfg["column_name"], index_type=idx_cfg['index_type'], metric=idx_cfg.get("metric", "l2"), num_partitions=num_partitions, replace=True)
            self.logger.info(f"Index created successfully for table {lancedb_document_store._table_name}")
        except Exception as e:
            self.logger.error(f"Error creating index for table {lancedb_document_store._table_name}: {e}",exc_info=True)