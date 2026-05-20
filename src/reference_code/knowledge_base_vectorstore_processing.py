from sys import exc_info
import os
import json
from falkordb import FalkorDB
from config.log_config import LoggerConfig
from config.config_settings import ConfigSettings
#from src.assembly_instruction_data_process import AssemblyInstructionDataExtractor
from pathlib import Path
from src.graph_query_generation import GraphQueryGeneration

#docker run -d -p 6379:6379 --name IKEA_Catalog -v /home/anu/falkor_data:/data falkordb/falkordb:latest
#docker run -d -p 3000:3000 --name IKEA_UI falkordb/falkordb-browser:latest
#ls -lh /home/anu/falkor_data
class KnowledgeBaseVectorstoreProcessing(GraphQueryGeneration):
    '''def __init__(self,logger:LoggerConfig=None ,settings: ConfigSettings = None):
        self.logger = LoggerConfig().get_logger() if logger is None else logger
        self.settings = ConfigSettings() if settings is None else settings
        #self.falkordb = FalkorDB(host=self.settings.falkordb_config.falkor_host, port=self.settings.falkordb_config.falkor_port)
        self.graph_query_generation = GraphQueryGeneration(logger,settings)'''
    def __init__(self):
        self.settings = ConfigSettings()
        self.logger = LoggerConfig().get_logger()
        super().__init__(self.logger,self.settings)
        '''self.assembly_process = AssemblyInstructionDataExtractor(logger,settings)
        self.product_details_node = {}
        self.markdown_chunk_nodes = []
        self.image_json_node_arr = []
        self.instruction_manual_node = []
        self.markdown_file_chunk_nodes = []'''
    

    async def generate_graph_nodes_relationships(self,source_data,input):
        try:
            
            for json_file_path in Path(self.settings.falkordb_config.falkor_ddl_json_files).glob('*.json'):
                with open(json_file_path, 'r') as f:
                    node_ddl = json.load(f)
                graph = self.falkordb.select_graph(node_ddl.get("graph_dbname"))    
                self.logger.info(f"DDL json file under process: {json_file_path.name}")
                for node in node_ddl['nodes']:
                    node_array_name = node['node_array_name'].split('.')[0] if '.' in node['node_array_name'] else node['node_array_name']
                    sub_node_array_name = node['node_array_name'].split('.')[1] if '.' in node['node_array_name'] else None
                    
                    #print(f"{node_array_name}: {len(source_data[node_array_name])}")
                    if len(source_data[node_array_name]) == 1 :
                        node_data = await self.get_node_source_data(node,source_data[node_array_name])
                        query_stmt,params = await self.create_single_node_graph_query(node,node_data)
                        self.logger.info(f"Single node graph query statement: {query_stmt}")
                        self.logger.info(f"Single node graph query parameters: {params}")
                        self.logger.info(f"Node data: {node_data}")
                        result = graph.query(query_stmt, params)
                        self.logger.info(f"Single node graph query result: {result.nodes_created}")            
                    else:
                        if sub_node_array_name:
                            for node_data in source_data[node_array_name]:
                                self.logger.info(f"Query for sub node array name: {node_array_name}.{sub_node_array_name}\n")
                                sub_node_data = node_data[sub_node_array_name]
                                query_stmt = await self.create_multiple_node_graph_query(node,sub_node_data,node_array_name,sub_node_array_name)
                                self.logger.info(f"Multiple node graph query statement: {query_stmt}")
                                sub_node_data = await self.get_node_source_data(node,sub_node_data) 
                                self.logger.info(f"Sub node data: {sub_node_data}")   
                                result = graph.query(query_stmt,{'sub_node_data':sub_node_data})
                                self.logger.info(f"Multiple node graph query result: {result.result_set[0][0]}")
                        else:
                            node_data = source_data[node_array_name]
                            self.logger.info(f"Query for node array name: {node_array_name}\n")
                            query_stmt = await self.create_multiple_node_graph_query(node,node_data,node_array_name)
                            self.logger.info(f"Multiple node graph query statement: {query_stmt}")
                            node_data = await self.get_node_source_data(node,node_data)
                            self.logger.info(f"Node data: {node_data}")
                            result = graph.query(query_stmt,{'node_data':node_data})
                            self.logger.info(f"Multiple node graph query result: {result.result_set[0][0]}")
                    for index_column in node.get('index_columns',[]):
                        query_stmt = await self.create_node_index_query(node,index_column,node.get('entity_name'),node.get('entity_alias'),node_ddl.get("graph_dbname"))
                        self.logger.info(f"Node index query statement: {query_stmt}")  
                        if query_stmt:
                            result = graph.query(query_stmt)
                            if result.indices_created == 1:
                                self.logger.info(f"Success: Index created!")
                            else:
                                self.logger.info(f"Failed: Index not created! OR Index already exists!")
            for json_file_path in Path(self.settings.falkordb_config.falkor_ddl_json_files).glob('*.json'):
                self.logger.info(f"DDL json file under process for creating relationships: {json_file_path.name}")
                with open(json_file_path, 'r') as f:
                    node_ddl = json.load(f)
                if 'relationships' in node_ddl: 
                    for relationship in node_ddl.get('relationships',[]): 
                        query_stmt = await self.create_relationship_graph_query(relationship,node_ddl.get("graph_dbname"))
                        self.logger.info(f"Relationship graph query statement: {query_stmt}")
                        result = graph.query(query_stmt)
                        self.logger.info(f"Relationship graph query result: {result.relationships_created}")
                        if result.relationships_created != 0:
                            self.logger.info(f"Success: Relationship created!")
                        else:
                            self.logger.info(f"Failed: Relationship not created! OR Relationship already exists!")

            self.falkordb.execute_command("SAVE")
            self.logger.info(f"Graph nodes relationships created successfully!")
        except Exception as e:
            self.logger.error(f"Error generating graph nodes relationships: {e}", exc_info=True)
            return None 

        



    '''async def vector_graph_store_process_old(self,result):
        try:
            graph = self.falkordb.select_graph("IKEA_CatalogDB")
            self.logger.info(f"Create Product nodes in IKEA_CatalogDB graph.")
            graph.query("""
            MERGE (p:Product {product_id: $product_id})
            SET p.product_name = $product_name,
                p.product_color = $product_color,
                p.product_dimension = $product_dimension,
                p.product_category = $product_category,
                p.instruction_type = $instruction_type,
                p.assembly_instruction_file_path = $assembly_instruction_file_path,
                p.assembly_instruction_filename = $assembly_instruction_filename,
                p.assembly_manual_id = $assembly_manual_id,
                p.product_details = $product_details,
                p.extra_information = $good_to_know,
                p.product_material = $product_material,
                p.care_instruction = $care_info,
                p.safety_and_compliance = $safety_info
            """,
            {
                'product_id':self.product_details_node.get('Article Number'),
                'product_name':self.product_details_node.get('product_name'),
                'product_color':self.product_details_node.get('product_color'),
                'product_dimension':self.product_details_node.get('product_dimension'),
                'product_category':self.product_details_node.get('product_category'),
                'instruction_type':self.product_details_node.get('instruction_type'),
                'assembly_instruction_file_path':self.product_details_node.get('assembly_instruction_file_path'),
                'assembly_instruction_filename':self.product_details_node.get('assembly_instruction_filename'),
                'assembly_manual_id':self.product_details_node.get('assembly_manual_id'),
                'product_details':self.product_details_node.get('Product details'),
                'good_to_know':self.product_details_node.get('Good to know'),
                'product_material':self.product_details_node.get('Material'),
                'care_info':self.product_details_node.get('Care'),
                'safety_info':self.product_details_node.get('Safety and compliance')
            }
            )
            self.logger.info(f"Product node created for product_id {self.product_details_node.get('Article Number')} and product_name {self.product_details_node.get('product_name')}")
            self.logger.info(f"Create graph node for markdown chunk and the corresponding relationships...")
            count = 0
            for markdown_chunk in self.markdown_chunk_nodes:
                if markdown_chunk.get('image_node_arr'):
                    #for image_node in markdown_chunk.get('image_node_arr',[]):
                    markdown_chunk_image_node_arr = markdown_chunk['image_node_arr']
                    create_markdown_chunk_image_node_query = """
                    UNWIND $markdown_chunk_image_node_arr as image_node
                    MERGE (mi:MarkdownAssemblyImage{markdown_file_name:image_node['markdown_file_name'],pdf_file_name:image_node['pdf_file_name'],page_number:image_node['page_number'],image_id:image_node['image_id'],type:image_node['type']})
                    SET mi.image_path = image_node['image_path'],
                    mi.content = image_node['content'],
                    mi.image_hex_name = image_node['image_hex_name']
                    """
                    graph.query(create_markdown_chunk_image_node_query,{'markdown_chunk_image_node_arr':markdown_chunk_image_node_arr})
                if markdown_chunk.get('language_warning_node_arr'):
                    language_warning_markdown_node_arr = markdown_chunk['language_warning_node_arr']
                    create_lang_warning_markdown_node_query = """
                    UNWIND $language_warning_markdown_node_arr as language_warning_markdown_node
                    MERGE(lwm:MarkdownLanguageWarning{markdown_file_name:language_warning_markdown_node['markdown_file_name'],pdf_file_name:language_warning_markdown_node['pdf_file_name'],page_number:language_warning_markdown_node['page_number'],language_warning:language_warning_markdown_node['language_warning'],type:language_warning_markdown_node['type']})
                    SET lwm.content = language_warning_markdown_node['content']
                    """
                    graph.query(create_lang_warning_markdown_node_query,{'language_warning_markdown_node_arr':language_warning_markdown_node_arr})
                if markdown_chunk.get('text_node_arr'):
                    markdown_text_node_arr = markdown_chunk['text_node_arr']
                    create_markdown_text_node_query = """
                    UNWIND $markdown_text_node_arr as markdown_text_node
                    MERGE(mt:MarkdownText{markdown_file_name:markdown_text_node['markdown_file_name'],pdf_file_name:markdown_text_node['pdf_file_name'],page_number:markdown_text_node['page_number'],type:markdown_text_node['type']})
                    SET mt.content = markdown_text_node['content']
                    """
                    graph.query(create_markdown_text_node_query,{'markdown_text_node_arr':markdown_text_node_arr})
            #Product Node Indexes
            graph.query("CREATE INDEX FOR (p:Product) ON (p.product_id)")
            graph.query("CREATE INDEX FOR (p:Product) ON (p.assembly_instruction_filename)")
            #Markdown Assembly Image Node Indexes
            graph.query("CREATE INDEX FOR (mi:MarkdownAssemblyImage) ON (mi.markdown_file_name)")
            graph.query("CREATE INDEX FOR (mi:MarkdownAssemblyImage) ON (mi.pdf_file_name)")
            graph.query("CREATE INDEX FOR (mi:MarkdownAssemblyImage) ON (mi.page_number)")
            graph.query("CREATE INDEX FOR (mi:MarkdownAssemblyImage) ON (mi.image_id)")
            #Markdown Language Warning Node Indexes
            graph.query("CREATE INDEX FOR (lwm:MarkdownLanguageWarning) ON (lwm.markdown_file_name)")
            graph.query("CREATE INDEX FOR (lwm:MarkdownLanguageWarning) ON (lwm.pdf_file_name)")
            graph.query("CREATE INDEX FOR (lwm:MarkdownLanguageWarning) ON (lwm.page_number)")
            graph.query("CREATE INDEX FOR (lwm:MarkdownLanguageWarning) ON (lwm.language_warning)")
            #Markdown Text Node Indexes
            graph.query("CREATE INDEX FOR (mt:MarkdownText) ON (mt.markdown_file_name)")
            graph.query("CREATE INDEX FOR (mt:MarkdownText) ON (mt.pdf_file_name)")
            graph.query("CREATE INDEX FOR (mt:MarkdownText) ON (mt.page_number)")   

            self.falkordb.execute_command("SAVE")
            
        except Exception as e:
            self.logger.error(f"Error processing data for knowledge base vector: {e}", exc_info=True)'''

  
        