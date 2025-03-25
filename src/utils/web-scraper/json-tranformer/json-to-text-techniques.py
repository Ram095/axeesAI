import json
import os

def convert_json_to_txt(output_txt_file):
    script_dir = os.path.dirname(os.path.abspath(__file__))        
    
    project_root = os.path.abspath(os.path.join(script_dir, "../../../"))
    data_dir = os.path.join(project_root, "data")    
    output_path = os.path.join(data_dir, output_txt_file)
    
    json_files = [f for f in os.listdir(data_dir) if f.endswith('.json')]
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for json_file in json_files:
            file_path = os.path.join(data_dir, json_file)
            
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            
            if not data:
                print(f"Skipping empty or invalid file: {json_file}")
                continue
            
            f.write(f"File: {json_file}\n")
            f.write("=" * 50 + "\n\n")
            
            # Handle both single object and array of objects
            items = data if isinstance(data, list) else [data]
            
            for index, item in enumerate(items):
                if index > 0:
                    f.write("\n" + "-" * 30 + "\n\n")  # Separator between items in same file
                
                # Process technique section
                if 'technique' in item and item['technique'] is not None:
                    if 'description' in item['technique']:
                        desc = item['technique']['description'].replace("\n\n", " : ").replace("\n", "\n\t- ")
                        f.write(desc + "\n\n")
                
                # Process description section
                if 'description' in item and item['description'] is not None:
                    if 'description' in item['description']:
                        desc = item['description']['description'].replace("\n\n", " : ").replace("\n", "\n\t- ")
                        f.write(desc + "\n\n")
                
                # Process examples section
                if 'examples' in item and item['examples'] is not None:
                    if 'description' in item['examples']:
                        desc = item['examples']['description']
                        f.write(desc + "\n\n")
                
                # Process related links section
                if 'related' in item and item['related'] is not None and 'links' in item['related'] and item['related']['links'] is not None:
                    f.write("Related techniques:\n")
                    for link in item['related']['links']:
                        if link.get('text') and link.get('url'):
                            f.write(f"- {link['text']}\n")
                    f.write("\n")
            
            f.write("-" * 50 + "\n\n")

# Example usage:
convert_json_to_txt("output.txt")
