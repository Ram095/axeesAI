import json
import os

def convert_json_to_txt(json_file, output_txt_file):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, json_file)
    project_root = os.path.abspath(os.path.join(script_dir, "../../../"))
    data_dir = os.path.join(project_root, "data")    
    output_path = os.path.join(data_dir, output_txt_file)
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for index, item in enumerate(data, start=1):
            f.write(f"Section {index}: {item.get('principle', 'Unknown Principle')}")
            f.write("\n" + "=" * 50 + "\n\n")
            
            if 'brief' in item and item['brief'] is not None and 'description' in item['brief']:                
                data = item['brief']['description']
                data = data.replace("\n\n", ": ")                
                data = data.replace("\n", "\n\t- ")                
                f.write(data + "\n\n")
                
            if 'success-criterion' in item and item['success-criterion'] is not None and 'description' in item['success-criterion']:                
                data = item['success-criterion']['description']
                data = data.replace("\n\n", ": ")                
                data = data.replace("\n", "\n\t- ")                
                f.write(data + "\n\n")
                
            if 'intent' in item and item['intent'] is not None and 'description' in item['intent']:            
                data = item['intent']['description']
                data = data.replace("\n\n", ": ")                
                data = data.replace("\n", "\n\t- ")                
                f.write(data + "\n\n")
                
            if 'techniques' in item and item['techniques'] is not None and 'description' in item['techniques']:                
                data = item['techniques']['description']
                data = data.replace("\n\n", ": ")                
                data = data.replace("\n", "\n\t- ")                
                f.write(data + "\n\n")
                
            if 'techniques' in item and item['techniques'] is not None and 'links' in item['techniques'] and item['techniques']['links'] is not None:                
                for link in item['techniques']['links']:
                    link_text = link.get('text', 'No text provided')                    
                    f.write(f"- {link_text}\n")
                f.write("\n\n")
                
            f.write("\n" + "-" * 50 + "\n\n")

# Example usage:
convert_json_to_txt("technique_links.json", "output.txt")
