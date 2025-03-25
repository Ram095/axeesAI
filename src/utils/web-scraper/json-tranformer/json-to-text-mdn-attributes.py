import json
import os

def convert_aria_json_to_txt(json_file, output_txt_file):
    # Get the script directory and construct the file path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, json_file)   
    
    project_root = os.path.abspath(os.path.join(script_dir, "../../../"))
    data_dir = os.path.join(project_root, "data")    
    output_path = os.path.join(data_dir, output_txt_file)
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for index, item in enumerate(data, start=1):            
            # Process description object if it exists
            if 'description' in item and item['description'] is not None:
                desc = item['description']
                
                # Write name
                if 'name' in desc:
                    f.write(f"ARIA role/attribute name: {desc['name']}\n\n")
                
                # Write ARIA title
                if 'aria_title' in desc:
                    f.write(f"{desc['aria_title']}\n\n")
                
                # Write description
                if 'description' in desc:
                    description_text = desc['description']                      
                    description_text = description_text.replace(".\n\n", ".\n")
                    #description_text = description_text.replace("\n\n", "\n\t")
                    f.write(f"{description_text}")
            f.write("\n" + "-" * 50 + "\n\n")    

if __name__ == "__main__":    
    convert_aria_json_to_txt("attributes.json", "mdn_aria_attributes.txt")
    convert_aria_json_to_txt("roles.json", "mdn_aria_roles.txt")