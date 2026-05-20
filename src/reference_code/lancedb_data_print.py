import lancedb
import pandas as pd
import json

pd.set_option('display.max_colwidth', None)

db = lancedb.connect("/home/anu/RAG_AI_ML_Projects/IKEA_Assembly_Instruction_Processing/data/LanceDB_data/IKEA_Catalog")
table = db.open_table("assembly_steps_details")
print(table.count_rows())

df=table.to_pandas()
print(df["vector"].head(10))
print(table.list_indices())

'''df = table.to_pandas()
print(df.head(5))
'''