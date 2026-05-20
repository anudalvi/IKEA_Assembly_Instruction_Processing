import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.knowledge_base_vectorstore_processing import KnowledgeBaseVectorstoreProcessing
from config.log_config import LoggerConfig
from config.config_settings import ConfigSettings

async def test_query_generation():
    processor = KnowledgeBaseVectorstoreProcessing()
    
    # Mock node DDL
    node_ddl = {
        "entity_name": "Product",
        "entity_alias": "p",
        "node_array_name": "product_details_node",
        "mapping_details": {
            "Column_Mapping": {
                "product_id": "Article Number",
                "product_name": "product_name"
            },
            "key_column": {
                "product_id": "product_id"
            }
        }
    }
    
    # Mock source data
    source_data = [
        {
            "Article Number": "123.456.78",
            "product_name": "TEST_PRODUCT",
            "product_id": "12345678"
        }
    ]
    
    print("Testing create_single_node_graph_query...")
    try:
        # Parent method expects list for single node if called like this:
        query, params = await processor.create_single_node_graph_query(node_ddl, source_data)
        print(f"Query: {query}")
        print(f"Params: {params}")
        assert query is not None
        assert params is not None
        print("Single node query generation successful!")
    except Exception as e:
        print(f"Single node query generation failed: {e}")
        import traceback
        traceback.print_exc()

    print("\nTesting create_multiple_node_graph_query...")
    try:
        query = await processor.create_multiple_node_graph_query(node_ddl, source_data, "product_details_node")
        print(f"Query: {query}")
        assert query is not None
        assert "UNWIND $node_data as node_data" in query
        print("Multiple node query generation successful!")
    except Exception as e:
        print(f"Multiple node query generation failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_query_generation())
