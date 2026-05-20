import os
import json
from falkordb import FalkorDB

def create_single_node_graph_query(product_data,json_file_path):
    pk_str = ''
    set_clauses = []
    params = {}
    try:
        with open(json_file_path, 'r') as f:
            product_ddl = json.load(f)
    
        query_stmt = f"MERGE({product_ddl['entity_alias']}:{product_ddl['entity_name']}"
        for pk_col in product_ddl['key_column']:
            pk_str = pk_str + f"{pk_col}:${pk_col},"
        for k,v in product_ddl['Column_Mapping'].items():
            set_clauses.append(f"{product_ddl['entity_alias']}.{k} = ${k}")
            params[k] = product_data.get(v)
        query_stmt = f"MERGE ({product_ddl['entity_alias']}:{product_ddl['entity_name']}{{{pk_str[:-1]}}})" + "\nSET " + ", \n".join(set_clauses)
        return query_stmt,params
    except Exception as e:
        print(f"Error occured while creating single node graph query statement: {e}")
        return None, None

def create_multiple_node_graph_query(json_file_path,node_array_name:str):
    pk_str = ''
    set_clauses = []
    try:
        with open(json_file_path, 'r') as f:
            node_ddl = json.load(f)
        query_stmt = f"UNWIND ${node_array_name} as node_data \n" 
        for pk_col in node_ddl['key_column']:
            pk_str = pk_str + f"{pk_col}:node_data['{pk_col}'],"
        for k,v in node_ddl['Column_Mapping'].items():
            set_clauses.append(f"{node_ddl['entity_alias']}.{k} = node_data['{k}']")
        query_stmt = query_stmt + f"MERGE ({node_ddl['entity_alias']}:{node_ddl['entity_name']}{{{pk_str[:-1]}}})" + "\nSET " + ", \n".join(set_clauses)
        return query_stmt
    except Exception as e:
        print(f"Error occured while creating multiple node graph query statement: {e}")
        return None

#product_data = {'product_name': 'LACK Wall shelf unit', 'product_color': ' black-blue', 'product_dimension': ' 30x190 cm', 'assembly_instruction_file_path': '/home/anu/RAG_AI_ML_Projects/IKEA_Assembly_Instruction_Processing/data/pdf_files/Assembly instructions/lack-wall-shelf-unit-black-blue__AA-2699149-1-100.pdf', 'product_category': 'Bookcases & shelving units', 'instruction_type': 'Assembly instructions', 'assembly_instruction_filename': 'lack-wall-shelf-unit-black-blue__AA-2699149-1-100', 'assembly_manual_id': 'AA-2699149-1-100', 'Product details': 'Shallow shelves help you to use the walls in your home efficiently. They hold a lot of things without taking up much space in the room. \n Choose if you want to mount the shelf horizontally or vertically on the wall. \n Designer \n C Halskov/H Dalsgaard', 'Good to know': 'When the wall shelf unit is hung in a horizontal position the total max. load is 25 kg. When hung in a vertical position the max. load is 3 kg per shelf. \n Combines with other products in the LACK series. \n Screws for wall mounting sold separately. \n IKEA of Sweden AB SE-343 81 Älmhult, IKEA.com', 'Material': 'Particleboard, Honeycomb structure paper filling (100% recycled), Fibreboard, Plastic edging, Acrylic paint', 'Care': 'Wipe clean with a cloth dampened in a mild cleaner. \n Wipe dry with a clean cloth.', 'Safety and compliance': 'WARNING! Falling hazard – to reduce the risk of this product falling down, it must be securely anchored. Use suitable screws and plugs for your home. If you are uncertain, seek professional advice.', 'Article Number': '005.928.70'}
#json_file_path = "/home/anu/RAG_AI_ML_Projects/IKEA_Assembly_Instruction_Processing/data/graph_vector_metadata/product_ddl.json"
markdown_chunk_data = [{
'image_node_arr': [{'pdf_file_name': 'lack-wall-shelf-unit-black-blue__AA-2699149-1-100', 'markdown_file_name': 'lack-wall-shelf-unit-black-blue__AA-2699149-1-100_1_5.md', 'page_number': 1, 'image_id': 'image_000001', 'image_path': '/home/anu/RAG_AI_ML_Projects/IKEA_Assembly_Instruction_Processing/data/markdown_files/lack-wall-shelf-unit-black-blue__AA-2699149-1-100/lack-wall-shelf-unit-black-blue__AA-2699149-1-100_1_5/lack-wall-shelf-unit-black-blue__AA-2699149-1-100_1_5_artifacts/image_000001_3304209eda31021aa1cc594c6fdd820d08dd6079147f2adabd7d2e7d1682d708.png', 'content': '![Image](/home/anu/RAG_AI_ML_Projects/IKEA_Assembly_Instruction_Processing/data/markdown_files/lack-wall-shelf-unit-black-blue__AA-2699149-1-100/lack-wall-shelf-unit-black-blue__AA-2699149-1-100_1_5/lack-wall-shelf-unit-black-blue__AA-2699149-1-100_1_5_artifacts/image_000001_3304209eda31021aa1cc594c6fdd820d08dd6079147f2adabd7d2e7d1682d708.png)', 'image_hex_name': 'image_000001_3304209eda31021aa1cc594c6fdd820d08dd6079147f2adabd7d2e7d1682d708', 'type': 'image'}, 
{'pdf_file_name': 'lack-wall-shelf-unit-black-blue__AA-2699149-1-100', 'markdown_file_name': 'lack-wall-shelf-unit-black-blue__AA-2699149-1-100_1_5.md', 'page_number': 2, 'image_id': 'image_000002', 'image_path': '/home/anu/RAG_AI_ML_Projects/IKEA_Assembly_Instruction_Processing/data/markdown_files/lack-wall-shelf-unit-black-blue__AA-2699149-1-100/lack-wall-shelf-unit-black-blue__AA-2699149-1-100_1_5/lack-wall-shelf-unit-black-blue__AA-2699149-1-100_1_5_artifacts/image_000002_e9204915b9c1895107107f1fadc0fe1b5cd566c90a22a063dc7756d91b126557.png', 'content': '![Image](/home/anu/RAG_AI_ML_Projects/IKEA_Assembly_Instruction_Processing/data/markdown_files/lack-wall-shelf-unit-black-blue__AA-2699149-1-100/lack-wall-shelf-unit-black-blue__AA-2699149-1-100_1_5/lack-wall-shelf-unit-black-blue__AA-2699149-1-100_1_5_artifacts/image_000002_e9204915b9c1895107107f1fadc0fe1b5cd566c90a22a063dc7756d91b126557.png)', 'image_hex_name': 'image_000002_e9204915b9c1895107107f1fadc0fe1b5cd566c90a22a063dc7756d91b126557', 'type': 'image'}, 
{'pdf_file_name': 'lack-wall-shelf-unit-black-blue__AA-2699149-1-100', 'markdown_file_name': 'lack-wall-shelf-unit-black-blue__AA-2699149-1-100_1_5.md', 'page_number': 3, 'image_id': 'image_000003', 'image_path': '/home/anu/RAG_AI_ML_Projects/IKEA_Assembly_Instruction_Processing/data/markdown_files/lack-wall-shelf-unit-black-blue__AA-2699149-1-100/lack-wall-shelf-unit-black-blue__AA-2699149-1-100_1_5/lack-wall-shelf-unit-black-blue__AA-2699149-1-100_1_5_artifacts/image_000003_18e1c22aefdf92251634dd3bf42b23eb6d2977969242d87ea77e617a594746ce.png', 'content': '![Image](/home/anu/RAG_AI_ML_Projects/IKEA_Assembly_Instruction_Processing/data/markdown_files/lack-wall-shelf-unit-black-blue__AA-2699149-1-100/lack-wall-shelf-unit-black-blue__AA-2699149-1-100_1_5/lack-wall-shelf-unit-black-blue__AA-2699149-1-100_1_5_artifacts/image_000003_18e1c22aefdf92251634dd3bf42b23eb6d2977969242d87ea77e617a594746ce.png)', 'image_hex_name': 'image_000003_18e1c22aefdf92251634dd3bf42b23eb6d2977969242d87ea77e617a594746ce', 'type': 'image'},
{'pdf_file_name': 'lack-wall-shelf-unit-black-blue__AA-2699149-1-100', 'markdown_file_name': 'lack-wall-shelf-unit-black-blue__AA-2699149-1-100_1_5.md', 'page_number': 4, 'image_id': 'image_000005', 'image_path': '/home/anu/RAG_AI_ML_Projects/IKEA_Assembly_Instruction_Processing/data/markdown_files/lack-wall-shelf-unit-black-blue__AA-2699149-1-100/lack-wall-shelf-unit-black-blue__AA-2699149-1-100_1_5/lack-wall-shelf-unit-black-blue__AA-2699149-1-100_1_5_artifacts/image_000005_2e8ef2b22b49da3d217c298d8d097fe6274e4646a1c40e2bb04623c1679ecfb8.png', 'content': '![Image](/home/anu/RAG_AI_ML_Projects/IKEA_Assembly_Instruction_Processing/data/markdown_files/lack-wall-shelf-unit-black-blue__AA-2699149-1-100/lack-wall-shelf-unit-black-blue__AA-2699149-1-100_1_5/lack-wall-shelf-unit-black-blue__AA-2699149-1-100_1_5_artifacts/image_000005_2e8ef2b22b49da3d217c298d8d097fe6274e4646a1c40e2bb04623c1679ecfb8.png)', 'image_hex_name': 'image_000005_2e8ef2b22b49da3d217c298d8d097fe6274e4646a1c40e2bb04623c1679ecfb8', 'type': 'image'},
{'pdf_file_name': 'lack-wall-shelf-unit-black-blue__AA-2699149-1-100', 'markdown_file_name': 'lack-wall-shelf-unit-black-blue__AA-2699149-1-100_1_5.md', 'page_number': 4, 'image_id': 'image_000004', 'image_path': '/home/anu/RAG_AI_ML_Projects/IKEA_Assembly_Instruction_Processing/data/markdown_files/lack-wall-shelf-unit-black-blue__AA-2699149-1-100/lack-wall-shelf-unit-black-blue__AA-2699149-1-100_1_5/lack-wall-shelf-unit-black-blue__AA-2699149-1-100_1_5_artifacts/image_000004_52d981256d6dd3b2bd39aa9637884c481255c286e44607ab33a1c71a0d495c04.png', 'content': '![Image](/home/anu/RAG_AI_ML_Projects/IKEA_Assembly_Instruction_Processing/data/markdown_files/lack-wall-shelf-unit-black-blue__AA-2699149-1-100/lack-wall-shelf-unit-black-blue__AA-2699149-1-100_1_5/lack-wall-shelf-unit-black-blue__AA-2699149-1-100_1_5_artifacts/image_000004_52d981256d6dd3b2bd39aa9637884c481255c286e44607ab33a1c71a0d495c04.png)', 'image_hex_name': 'image_000004_52d981256d6dd3b2bd39aa9637884c481255c286e44607ab33a1c71a0d495c04', 'type': 'image'}]}]

json_file_path = "/home/anu/RAG_AI_ML_Projects/IKEA_Assembly_Instruction_Processing/data/graph_vector_metadata/MarkdownAssemblyImage_ddl.json"
falkordb = FalkorDB(host="localhost", port=6379)
graph = falkordb.select_graph("Demo_Graph1")
#query_stmt,params = create_single_node_graph_query(product_data,json_file_path)
key_name = 'image_node_arr'
query_stmt = create_multiple_node_graph_query(json_file_path,key_name)
print(query_stmt)
for markdown_chunk in markdown_chunk_data:
    if markdown_chunk.get(key_name):
        graph.query(query_stmt,{key_name:markdown_chunk[key_name]})