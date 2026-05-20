'''from config.config_settings import ConfigSettings

d = {"folder_path":"datasource_config.markdown_files_path"}
settings = ConfigSettings()
obj = settings
#str = getattr(settings,d["folder_path"])
s = d["folder_path"]
for i in s.split('.'):
    obj = getattr(obj,i,None)
print(obj)
c = {
    **d,"new_key":"new_value"
}
print(c)
d1 = [1,2,3,4,5]
d2=[*d1,6,7,8,9,10]
print(d2)

def modify(n):
    n +=1        # creates a NEW int object, doesn't affect original


x = 10
#modify(x)
modify(x)
print(x)

def modify1(n):
    n[0] = n[0] + 1   # mutate the list in-place

x = [10]        # wrap int in a list
modify1(x)
print(x[0])  


d = {"type_conditions":[
                     "language_warning_text",
                     "image",
                     "text"
                  ]}
l1= d["type_conditions"]
print([l1.index(t1) for t1 in l1])

field_schema_config = {
    "main_field":"classification",
    "field_validation":
        {"assembly": ["classification","step_name","action","parts","tools","difficulty"],
        "guidance": ["classification","content_type","description","key_info","guidance"]}
    }

classification = None
if classification is not None and classification.lower() in field_schema_config["field_validation"]:
    print("found")
else:
    print("not found")'''
'''import os
import json

str = '![Image](/home/anu/RAG_AI_ML_Projects/IKEA_Assembly_Instruction_Processing/data/markdown_files/oxberg-door-black-oak-effect__AA-1003268-8-2/oxberg-door-black-oak-effect__AA-1003268-8-2_6_10_artifacts/image_000009_03a88ef5700a9fbfa1f5215dde675402c6de0a6397cc79c94c9921a8ad9de9a9.png)'
image_file_path = str.split('\n')[0].replace("![Image](","").replace(")","")
image_file_name = image_file_path.split("/")[-1]
print("Image file name:", image_file_name)
image_json_file_name = "_".join(image_file_name.split("_")[0:2]) + ".json"
image_desc_folder_path = "/".join(image_file_path.split("/")[:-1]).replace("_artifacts","_image_desc")
print(type(image_desc_folder_path))
print("Image folder path:", image_desc_folder_path)
image_desc_file_path = os.path.join(image_desc_folder_path,image_json_file_name)
print("Image desc file path:", image_desc_file_path)
with open(image_desc_file_path,'r',encoding='utf-8') as f:
    image_desc = json.load(f)    
print("File content:",image_desc)
'''
input = {'Product Details': [
 {'header': 'Product details', 'text': 'BILLY is a versatile bookcase that works just as good as a storage unit and is suitable to use in many different ways at home. \n The extra depth and adjustable shelves help you customise your bookcase and create space for larger books and objects. \n Behind the panel doors you can keep your belongings hidden and free from dust. \n BILLY has a simple and timeless design that is easy to personalise by adding boxes, lighting and your favourite items. \n The wooden expression with a tactile wood texture brings a warm and natural feel into your home and adds a\xa0beautiful and vibrant look to the room. \n This bookcase has a height extension unit, allowing you to make the most of the wall area. \n The back panel fixes in place with snap fittings – making BILLY easy to assemble and disassemble, so you can bring it when moving instead of buying a new one. \n Adjustable hinges allow you to adjust the door horizontally and vertically.'}, 
 {'header': 'Good to know', 'text': '1 fixed shelf and 4 adjustable shelves included. \n Keep in mind that you need enough space between the top of the furniture and the ceiling to be able to anchor the product to the wall. \n May be completed with extra shelves to add storage space. \n IKEA of Sweden AB SE-343 81 Älmhult, IKEA.com'}, 
 {'header': 'Material', 'text': 'Bookcase \n Basematerial/ Side panel: \n Particleboard, Paper foil, Plastic edging \n Plinth front: \n Particleboard, Paper foil \n Back: \n Fibreboard, Paint, Paper foil \n Height extension unit \n Top panel: \n Particleboard, Paper foil, Plastic edging, Plastic edging, Paper foil \n Side panel: \n Particleboard, Paper foil, Plastic edging, Plastic edging, Paper foil, Paper edging \n Back: \n Particleboard, Paper foil, Acrylic paint \n Door \n Stile: \n Fibreboard, Paper foil, Plastic edging, Paper foil, Plastic edging \n Rail/ Door panel: \n Fibreboard, Paper foil'}, 
 {'header': 'Care', 'text': 'Bookcase/height extension unit \n Wipe clean with a cloth dampened in a mild cleaner. \n Wipe dry with a clean cloth.'}, 
 {'header': 'Safety and compliance', 'text': 'WARNING! Tipping hazard – this product must be securely anchored.  Use suitable screws and plugs for your home. If you are uncertain, seek professional advice.'}, {'header': 'Assembly instructions', 'text': 'BILLY Bookcase \n BILLY Bookcase \n BILLY Height extension unit \n OXBERG Door', 'instruction_pdf': ['https://www.ikea.com/nl/en/assembly_instructions/billy-bookcase-black-oak-effect__AA-2292949-2-1.pdf', 'https://www.ikea.com/nl/en/assembly_instructions/billy-bookcase-black-oak-effect__AA-2545155-1-100.pdf', 'https://www.ikea.com/nl/en/assembly_instructions/billy-height-extension-unit-black-oak-effect__AA-2545353-3-100.pdf', 'https://www.ikea.com/nl/en/assembly_instructions/oxberg-door-black-oak-effect__AA-1003268-8-2.pdf']}, 
 {'header': 'Advice and care instructions', 'text': 'BILLY Bookcase \n BILLY Height extension unit \n OXBERG Door', 'instruction_pdf': ['https://www.ikea.com/nl/en/manuals/billy-bookcase-black-oak-effect__AA-2180177-2-2.pdf', 'https://www.ikea.com/nl/en/manuals/billy-height-extension-unit-black-oak-effect__AA-2180177-2-2.pdf', 'https://www.ikea.com/nl/en/manuals/oxberg-door-black-oak-effect__AA-2180177-2-2.pdf']}, 
 {'header': 'Article Number', 'text': '104.773.65'}, 
 {'header': 'product_name', 'text': 'BILLY / OXBERG Bookcase w doors/extension unit, black oak effect, 80x41x237 cm'}, 
 {'header': 'product_category', 'text': 'Bookcases & shelving units'}], 
 'PDF File Details': [
 {'pdf_file_path': '/home/anu/RAG_AI_ML_Projects/IKEA_Assembly_Instruction_Processing/data/pdf_files/Assembly instructions/billy-bookcase-black-oak-effect__AA-2292949-2-1.pdf', 'pdf_file_name': 'billy-bookcase-black-oak-effect__AA-2292949-2-1.pdf', 'pdf_file_size': '0.73 MB', 'pdf_file_url': 'https://www.ikea.com/nl/en/assembly_instructions/billy-bookcase-black-oak-effect__AA-2292949-2-1.pdf', 'product_link': 'https://www.ikea.com/nl/en/p/billy-oxberg-bookcase-w-doors-extension-unit-black-oak-effect-s89562964/', 'product_category': 'Bookcases & shelving units', 'product_name': 'BILLY / OXBERG Bookcase w doors/extension unit, black oak effect, 80x41x237 cm', 'pdf_type': 'Assembly instructions', 'Download Status': 'Success'}, 
 {'pdf_file_path': '/home/anu/RAG_AI_ML_Projects/IKEA_Assembly_Instruction_Processing/data/pdf_files/Assembly instructions/billy-bookcase-black-oak-effect__AA-2545155-1-100.pdf', 'pdf_file_name': 'billy-bookcase-black-oak-effect__AA-2545155-1-100.pdf', 'pdf_file_size': '1.75 MB', 'pdf_file_url': 'https://www.ikea.com/nl/en/assembly_instructions/billy-bookcase-black-oak-effect__AA-2545155-1-100.pdf', 'product_link': 'https://www.ikea.com/nl/en/p/billy-oxberg-bookcase-w-doors-extension-unit-black-oak-effect-s89562964/', 'product_category': 'Bookcases & shelving units', 'product_name': 'BILLY / OXBERG Bookcase w doors/extension unit, black oak effect, 80x41x237 cm', 'pdf_type': 'Assembly instructions', 'Download Status': 'Success'}, 
 {'pdf_file_path': '/home/anu/RAG_AI_ML_Projects/IKEA_Assembly_Instruction_Processing/data/pdf_files/Assembly instructions/billy-height-extension-unit-black-oak-effect__AA-2545353-3-100.pdf', 'pdf_file_name': 'billy-height-extension-unit-black-oak-effect__AA-2545353-3-100.pdf', 'pdf_file_size': '1.52 MB', 'pdf_file_url': 'https://www.ikea.com/nl/en/assembly_instructions/billy-height-extension-unit-black-oak-effect__AA-2545353-3-100.pdf', 'product_link': 'https://www.ikea.com/nl/en/p/billy-oxberg-bookcase-w-doors-extension-unit-black-oak-effect-s89562964/', 'product_category': 'Bookcases & shelving units', 'product_name': 'BILLY / OXBERG Bookcase w doors/extension unit, black oak effect, 80x41x237 cm', 'pdf_type': 'Assembly instructions', 'Download Status': 'Success'}, 
 {'pdf_file_path': '/home/anu/RAG_AI_ML_Projects/IKEA_Assembly_Instruction_Processing/data/pdf_files/Assembly instructions/oxberg-door-black-oak-effect__AA-1003268-8-2.pdf', 'pdf_file_name': 'oxberg-door-black-oak-effect__AA-1003268-8-2.pdf', 'pdf_file_size': '1.41 MB', 'pdf_file_url': 'https://www.ikea.com/nl/en/assembly_instructions/oxberg-door-black-oak-effect__AA-1003268-8-2.pdf', 'product_link': 'https://www.ikea.com/nl/en/p/billy-oxberg-bookcase-w-doors-extension-unit-black-oak-effect-s89562964/', 'product_category': 'Bookcases & shelving units', 'product_name': 'BILLY / OXBERG Bookcase w doors/extension unit, black oak effect, 80x41x237 cm', 'pdf_type': 'Assembly instructions', 'Download Status': 'Success'}, 
 {'pdf_file_path': '/home/anu/RAG_AI_ML_Projects/IKEA_Assembly_Instruction_Processing/data/pdf_files/Advice and care instructions/billy-bookcase-black-oak-effect__AA-2180177-2-2.pdf', 'pdf_file_name': 'billy-bookcase-black-oak-effect__AA-2180177-2-2.pdf', 'pdf_file_size': '0.79 MB', 'pdf_file_url': 'https://www.ikea.com/nl/en/manuals/billy-bookcase-black-oak-effect__AA-2180177-2-2.pdf', 'product_link': 'https://www.ikea.com/nl/en/p/billy-oxberg-bookcase-w-doors-extension-unit-black-oak-effect-s89562964/', 'product_category': 'Bookcases & shelving units', 'product_name': 'BILLY / OXBERG Bookcase w doors/extension unit, black oak effect, 80x41x237 cm', 'pdf_type': 'Advice and care instructions', 'Download Status': 'Success'}, 
 {'pdf_file_path': '/home/anu/RAG_AI_ML_Projects/IKEA_Assembly_Instruction_Processing/data/pdf_files/Advice and care instructions/billy-height-extension-unit-black-oak-effect__AA-2180177-2-2.pdf', 'pdf_file_name': 'billy-height-extension-unit-black-oak-effect__AA-2180177-2-2.pdf', 'pdf_file_size': '0.79 MB', 'pdf_file_url': 'https://www.ikea.com/nl/en/manuals/billy-height-extension-unit-black-oak-effect__AA-2180177-2-2.pdf', 'product_link': 'https://www.ikea.com/nl/en/p/billy-oxberg-bookcase-w-doors-extension-unit-black-oak-effect-s89562964/', 'product_category': 'Bookcases & shelving units', 'product_name': 'BILLY / OXBERG Bookcase w doors/extension unit, black oak effect, 80x41x237 cm', 'pdf_type': 'Advice and care instructions', 'Download Status': 'Success'}, 
 {'pdf_file_path': '/home/anu/RAG_AI_ML_Projects/IKEA_Assembly_Instruction_Processing/data/pdf_files/Advice and care instructions/oxberg-door-black-oak-effect__AA-2180177-2-2.pdf', 'pdf_file_name': 'oxberg-door-black-oak-effect__AA-2180177-2-2.pdf', 'pdf_file_size': '0.79 MB', 'pdf_file_url': 'https://www.ikea.com/nl/en/manuals/oxberg-door-black-oak-effect__AA-2180177-2-2.pdf', 'product_link': 'https://www.ikea.com/nl/en/p/billy-oxberg-bookcase-w-doors-extension-unit-black-oak-effect-s89562964/', 'product_category': 'Bookcases & shelving units', 'product_name': 'BILLY / OXBERG Bookcase w doors/extension unit, black oak effect, 80x41x237 cm', 'pdf_type': 'Advice and care instructions', 'Download Status': 'Success'}
 ]}

'''
product_details_arr = []
instruction_pdf_arr = list(map(lambda pdf_list: [f.split('/')[-1] for f in pdf_list['instruction_pdf']],filter(lambda item:item["header"]=="Assembly instructions",input['Product Details'])))[0]
print(instruction_pdf_arr)
#instruction_pdf_arr = list(map(lambda pdf_list: [f.split('/')[-1] for f in pdf_list['instruction_pdf']],filter(lambda item:item["header"]=="Assembly instructions",input['Product Details'])))[0]
for pdf_file in instruction_pdf_arr:
    product_details = {}
    product_details['assembly_instruction_file_name'] = pdf_file
    product_details['product_details'] = (" ".join(map(lambda item: item['text'],filter(lambda item:item["header"]=="Product details",input['Product Details'])))).strip()
    product_details['Good to know']=(" ".join(map(lambda item: item['text'],filter(lambda item:item["header"]=="Good to know", input["Product Details"])))).strip()
    product_details['Material']=(" ".join(map(lambda item: item['text'],filter(lambda item:item["header"]=="Material", input["Product Details"])))).strip()
    product_details['Care Instructions']=(" ".join(map(lambda item: item['text'],filter(lambda item:item["header"]=="Care", input["Product Details"])))).strip()
    product_details['Safety and compliance']=(" ".join(map(lambda item: item['text'],filter(lambda item:item["header"]=="Safety and compliance", input["Product Details"])))).strip()
    product_details['Product_id']=(" ".join(map(lambda item: item['text'],filter(lambda item:item["header"]=="Article Number", input["Product Details"])))).strip()
    product_details['product_name']=(" ".join(map(lambda item: item['text'],filter(lambda item:item["header"]=="product_name", input["Product Details"])))).strip().split(",")[0].strip()
    product_details['product_color']=(" ".join(map(lambda item: item['text'],filter(lambda item:item["header"]=="product_name", input["Product Details"])))).strip().split(",")[1].strip()
    product_details['product_dimensions']=(" ".join(map(lambda item: item['text'],filter(lambda item:item["header"]=="product_name", input["Product Details"])))).strip().split(",")[2].strip()
    product_details['product_category']=(" ".join(map(lambda item: item['text'],filter(lambda item:item["header"]=="product_category", input["Product Details"])))).strip()
    product_details_arr.append(product_details)

print(product_details_arr)'''

'''input = {'Product Details': [{'header': 'Product details', 'text': 'BILLY is a versatile bookcase that works just as good as a storage unit and is suitable to use in many different ways at home. \n The extra depth and adjustable shelves help you customise your bookcase and create space for larger books and objects. \n Behind the panel doors you can keep your belongings hidden and free from dust. \n BILLY has a simple and timeless design that is easy to personalise by adding boxes, lighting and your favourite items. \n The wooden expression with a tactile wood texture brings a warm and natural feel into your home and adds a\xa0beautiful and vibrant look to the room. \n This bookcase has a height extension unit, allowing you to make the most of the wall area. \n The back panel fixes in place with snap fittings – making BILLY easy to assemble and disassemble, so you can bring it when moving instead of buying a new one. \n Adjustable hinges allow you to adjust the door horizontally and vertically.'}, {'header': 'Good to know', 'text': '1 fixed shelf and 4 adjustable shelves included. \n Keep in mind that you need enough space between the top of the furniture and the ceiling to be able to anchor the product to the wall. \n May be completed with extra shelves to add storage space. \n IKEA of Sweden AB SE-343 81 Älmhult, IKEA.com'}, {'header': 'Material', 'text': 'Bookcase \n Basematerial/ Side panel: \n Particleboard, Paper foil, Plastic edging \n Plinth front: \n Particleboard, Paper foil \n Back: \n Fibreboard, Paint, Paper foil \n Height extension unit \n Top panel: \n Particleboard, Paper foil, Plastic edging, Plastic edging, Paper foil \n Side panel: \n Particleboard, Paper foil, Plastic edging, Plastic edging, Paper foil, Paper edging \n Back: \n Particleboard, Paper foil, Acrylic paint \n Door \n Stile: \n Fibreboard, Paper foil, Plastic edging, Paper foil, Plastic edging \n Rail/ Door panel: \n Fibreboard, Paper foil'}, {'header': 'Care', 'text': 'Bookcase/height extension unit \n Wipe clean with a cloth dampened in a mild cleaner. \n Wipe dry with a clean cloth.'}, {'header': 'Safety and compliance', 'text': 'WARNING! Tipping hazard – this product must be securely anchored.  Use suitable screws and plugs for your home. If you are uncertain, seek professional advice.'}, {'header': 'Assembly instructions', 'text': 'BILLY Bookcase \n BILLY Bookcase \n BILLY Height extension unit \n OXBERG Door', 'instruction_pdf': ['https://www.ikea.com/nl/en/assembly_instructions/billy-bookcase-black-oak-effect__AA-2292949-2-1.pdf', 'https://www.ikea.com/nl/en/assembly_instructions/billy-bookcase-black-oak-effect__AA-2545155-1-100.pdf', 'https://www.ikea.com/nl/en/assembly_instructions/billy-height-extension-unit-black-oak-effect__AA-2545353-3-100.pdf', 'https://www.ikea.com/nl/en/assembly_instructions/oxberg-door-black-oak-effect__AA-1003268-8-2.pdf']}, {'header': 'Advice and care instructions', 'text': 'BILLY Bookcase \n BILLY Height extension unit \n OXBERG Door', 'instruction_pdf': ['https://www.ikea.com/nl/en/manuals/billy-bookcase-black-oak-effect__AA-2180177-2-2.pdf', 'https://www.ikea.com/nl/en/manuals/billy-height-extension-unit-black-oak-effect__AA-2180177-2-2.pdf', 'https://www.ikea.com/nl/en/manuals/oxberg-door-black-oak-effect__AA-2180177-2-2.pdf']}, {'header': 'Article Number', 'text': '104.773.65'}, {'header': 'product_name', 'text': 'BILLY / OXBERG Bookcase w doors/extension unit, black oak effect, 80x41x237 cm'}, {'header': 'product_category', 'text': 'Bookcases & shelving units'}], 'PDF File Details': [{'pdf_file_path': '/home/anu/RAG_AI_ML_Projects/IKEA_Assembly_Instruction_Processing/data/pdf_files/Assembly instructions/billy-bookcase-black-oak-effect__AA-2292949-2-1.pdf', 'pdf_file_name': 'billy-bookcase-black-oak-effect__AA-2292949-2-1.pdf', 'pdf_file_size': '0.73 MB', 'pdf_file_url': 'https://www.ikea.com/nl/en/assembly_instructions/billy-bookcase-black-oak-effect__AA-2292949-2-1.pdf', 'product_link': 'https://www.ikea.com/nl/en/p/billy-oxberg-bookcase-w-doors-extension-unit-black-oak-effect-s89562964/', 'product_category': 'Bookcases & shelving units', 'product_name': 'BILLY / OXBERG Bookcase w doors/extension unit, black oak effect, 80x41x237 cm', 'pdf_type': 'Assembly instructions', 'Download Status': 'Success'}, {'pdf_file_path': '/home/anu/RAG_AI_ML_Projects/IKEA_Assembly_Instruction_Processing/data/pdf_files/Assembly instructions/billy-bookcase-black-oak-effect__AA-2545155-1-100.pdf', 'pdf_file_name': 'billy-bookcase-black-oak-effect__AA-2545155-1-100.pdf', 'pdf_file_size': '1.75 MB', 'pdf_file_url': 'https://www.ikea.com/nl/en/assembly_instructions/billy-bookcase-black-oak-effect__AA-2545155-1-100.pdf', 'product_link': 'https://www.ikea.com/nl/en/p/billy-oxberg-bookcase-w-doors-extension-unit-black-oak-effect-s89562964/', 'product_category': 'Bookcases & shelving units', 'product_name': 'BILLY / OXBERG Bookcase w doors/extension unit, black oak effect, 80x41x237 cm', 'pdf_type': 'Assembly instructions', 'Download Status': 'Success'}, {'pdf_file_path': '/home/anu/RAG_AI_ML_Projects/IKEA_Assembly_Instruction_Processing/data/pdf_files/Assembly instructions/billy-height-extension-unit-black-oak-effect__AA-2545353-3-100.pdf', 'pdf_file_name': 'billy-height-extension-unit-black-oak-effect__AA-2545353-3-100.pdf', 'pdf_file_size': '1.52 MB', 'pdf_file_url': 'https://www.ikea.com/nl/en/assembly_instructions/billy-height-extension-unit-black-oak-effect__AA-2545353-3-100.pdf', 'product_link': 'https://www.ikea.com/nl/en/p/billy-oxberg-bookcase-w-doors-extension-unit-black-oak-effect-s89562964/', 'product_category': 'Bookcases & shelving units', 'product_name': 'BILLY / OXBERG Bookcase w doors/extension unit, black oak effect, 80x41x237 cm', 'pdf_type': 'Assembly instructions', 'Download Status': 'Success'}, {'pdf_file_path': '/home/anu/RAG_AI_ML_Projects/IKEA_Assembly_Instruction_Processing/data/pdf_files/Assembly instructions/oxberg-door-black-oak-effect__AA-1003268-8-2.pdf', 'pdf_file_name': 'oxberg-door-black-oak-effect__AA-1003268-8-2.pdf', 'pdf_file_size': '1.41 MB', 'pdf_file_url': 'https://www.ikea.com/nl/en/assembly_instructions/oxberg-door-black-oak-effect__AA-1003268-8-2.pdf', 'product_link': 'https://www.ikea.com/nl/en/p/billy-oxberg-bookcase-w-doors-extension-unit-black-oak-effect-s89562964/', 'product_category': 'Bookcases & shelving units', 'product_name': 'BILLY / OXBERG Bookcase w doors/extension unit, black oak effect, 80x41x237 cm', 'pdf_type': 'Assembly instructions', 'Download Status': 'Success'}, {'pdf_file_path': '/home/anu/RAG_AI_ML_Projects/IKEA_Assembly_Instruction_Processing/data/pdf_files/Advice and care instructions/billy-bookcase-black-oak-effect__AA-2180177-2-2.pdf', 'pdf_file_name': 'billy-bookcase-black-oak-effect__AA-2180177-2-2.pdf', 'pdf_file_size': '0.79 MB', 'pdf_file_url': 'https://www.ikea.com/nl/en/manuals/billy-bookcase-black-oak-effect__AA-2180177-2-2.pdf', 'product_link': 'https://www.ikea.com/nl/en/p/billy-oxberg-bookcase-w-doors-extension-unit-black-oak-effect-s89562964/', 'product_category': 'Bookcases & shelving units', 'product_name': 'BILLY / OXBERG Bookcase w doors/extension unit, black oak effect, 80x41x237 cm', 'pdf_type': 'Advice and care instructions', 'Download Status': 'Success'}, {'pdf_file_path': '/home/anu/RAG_AI_ML_Projects/IKEA_Assembly_Instruction_Processing/data/pdf_files/Advice and care instructions/billy-height-extension-unit-black-oak-effect__AA-2180177-2-2.pdf', 'pdf_file_name': 'billy-height-extension-unit-black-oak-effect__AA-2180177-2-2.pdf', 'pdf_file_size': '0.79 MB', 'pdf_file_url': 'https://www.ikea.com/nl/en/manuals/billy-height-extension-unit-black-oak-effect__AA-2180177-2-2.pdf', 'product_link': 'https://www.ikea.com/nl/en/p/billy-oxberg-bookcase-w-doors-extension-unit-black-oak-effect-s89562964/', 'product_category': 'Bookcases & shelving units', 'product_name': 'BILLY / OXBERG Bookcase w doors/extension unit, black oak effect, 80x41x237 cm', 'pdf_type': 'Advice and care instructions', 'Download Status': 'Success'}, {'pdf_file_path': '/home/anu/RAG_AI_ML_Projects/IKEA_Assembly_Instruction_Processing/data/pdf_files/Advice and care instructions/oxberg-door-black-oak-effect__AA-2180177-2-2.pdf', 'pdf_file_name': 'oxberg-door-black-oak-effect__AA-2180177-2-2.pdf', 'pdf_file_size': '0.79 MB', 'pdf_file_url': 'https://www.ikea.com/nl/en/manuals/oxberg-door-black-oak-effect__AA-2180177-2-2.pdf', 'product_link': 'https://www.ikea.com/nl/en/p/billy-oxberg-bookcase-w-doors-extension-unit-black-oak-effect-s89562964/', 'product_category': 'Bookcases & shelving units', 'product_name': 'BILLY / OXBERG Bookcase w doors/extension unit, black oak effect, 80x41x237 cm', 'pdf_type': 'Advice and care instructions', 'Download Status': 'Success'}]}
files_to_process = [item['pdf_file_name'] for item in input['PDF File Details'] if 'Assembly' in item.get('pdf_type', '')]
print(files_to_process)
arr = list(map(lambda item:item["pdf_file_name"],filter(lambda item:item["pdf_type"].find("Assembly")!=-1,input['PDF File Details'])))
print("Map function output:",arr)'''


'''data = {"conditional_field":"classification",
                        "cases":{
                           "Assembly":"safety",
                           "Guidance":"guidance"
                        }
                     }  
print(list(data["cases"].keys())[0])
print(list(data["cases"].values())[0])'''

data = {"embedding_columns":[{"embed_text":"float32"},{"embed_text_2":"float64"},{"embed_text_3":"float16"}]}
q = "embed_text"
print(next((d[q] for d in data["embedding_columns"] if q in d),None))
    
    
    