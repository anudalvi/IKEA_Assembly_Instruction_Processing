import pyarrow as pa
from haystack import component, Document
from typing import Optional, Dict, Any
from config.log_config import LoggerConfig
import json

# Python type casters keyed by pyarrow type name prefix
_PA_TYPE_CASTERS = {
    "int":   lambda v: int(v) if v is not None else 0,
    "float": lambda v: float(v) if v is not None else 0.0,
    "str":   lambda v: str(v) if v is not None else "",
}

def _cast_meta_value(value: Any, pa_type_str: str) -> Any:
    """Cast a meta value to the Python type matching the declared pyarrow type."""
    for prefix, caster in _PA_TYPE_CASTERS.items():
        if pa_type_str.startswith(prefix):
            try:
                return caster(value)
            except (ValueError, TypeError):
                return caster(None)
    return value  # fallback: return as-is for unknown types


@component
class DataChunkToDocumentConversion:
    def __init__(self, datasource_config):
        self.logger = LoggerConfig().get_logger()
        self.datasource_config = datasource_config

    @component.output_types(document=Optional[Dict[str, Any]])
    def run(self, table_data, table_def_config):
        documents = []
        try:
            self.logger.info("Processing data chunk for haystack document conversion...")
            meta_fields: Dict[str, str] = table_def_config["meta_fields"]  # {col_name: pa_type_str}
            for chunk in table_data[table_def_config["table_name"]]:
                meta = {}
                for field_name, pa_type_str in meta_fields.items():
                    raw_value = chunk.get(field_name)
                    meta[field_name] = _cast_meta_value(raw_value, pa_type_str)
                content = ". ".join([str(chunk[col]) for col in table_def_config["embedding_columns"]])
                if isinstance(table_def_config["document_id"],list):
                    document_id = " - ".join([str(chunk[col]) for col in table_def_config["document_id"]])
                else:
                    document_id = str(chunk[table_def_config["document_id"]])
                documents.append(
                    Document(
                        id=document_id,
                        content=content,
                        meta=meta,
                    )
                )
            return {table_def_config["table_name"]: documents}
        except Exception as e:
            self.logger.error(f"Error in DataChunkToDocumentConversion: {e}", exc_info=True)
            return {table_def_config["table_name"]: []}