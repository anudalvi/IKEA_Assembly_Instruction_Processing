import os

str = "/home/anu/RAG_AI_ML_Projects/IKEA_Assembly_Instruction_Processing/data/markdown_files/billy-bookcase-black-oak-effect__AA-2292949-2-1/billy-bookcase-black-oak-effect__AA-2292949-2-1_6_10_artifacts/image_000004_f4016abb7e5197d68a76c4588cb41396b7eb17d5d85042f63b8bfc525d545621.png"
image_file_name = str.split('/')[-1]
artifact_folder_name = str.split('/')[-2]
print(image_file_name)
print(artifact_folder_name)
chunk_folder_path = '/'.join(str.split('/')[:-2])
print(chunk_folder_path)
os.makedirs(os.path.join(chunk_folder_path, artifact_folder_name.replace('_artifacts', '_image_desc')), exist_ok=True)
image_file_name_arr = image_file_name.split('_')
img_json_file_name = '_'.join(image_file_name_arr[0:2]) + '.json'
print(img_json_file_name)
print(os.path.join(chunk_folder_path, artifact_folder_name.replace('_artifacts', '_image_desc'), img_json_file_name))
image_json_file_path = os.path.join(chunk_folder_path, artifact_folder_name.replace('_artifacts', '_image_desc'), img_json_file_name)
print(image_json_file_path)
