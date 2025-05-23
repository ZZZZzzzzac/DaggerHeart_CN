import re
import json
import pandas as pd
import argparse
import os

fixed_widths = {
    "名称": 100,
    "检定": 40,
    "属性": 40,
    "范围": 50,
    "伤害": 40,
    "负荷": 40,
    "护甲值": 40,
    "阈值": 100,
    "roll": 30   
}

def extract_json_from_js(js_content):
    """
    Extracts variable names and their corresponding JSON array strings from JS content.
    Finds all occurrences of 'const variableName = [...]'.
    """
    # Regex to find 'const variableName = [...]'
    # It captures the variable name and the array content.
    # Handles potential semicolons at the end of the declaration.
    # [\s\S] is used to match any character including newlines within the array.
    regex = r"const\s+([a-zA-Z0-9_]+)\s*=\s*(\[[\s\S]*?\]);"
    
    matches = re.findall(regex, js_content)
    
    extracted_data = []
    for match in matches:
        var_name = match[0]
        json_str = match[1]
        try:
            # Validate and parse the JSON string
            json_data = json.loads(json_str)
            if isinstance(json_data, list):
                extracted_data.append({"name": var_name, "data": json_data})
            else:
                print(f"Warning: Variable '{var_name}' is not a list. Skipping.")
        except json.JSONDecodeError as e:
            print(f"Warning: Could not decode JSON for variable '{var_name}'. Error: {e}. Skipping.")
            # Attempt to clean up common JS-specific syntax issues like trailing commas
            # This is a basic attempt and might not cover all cases.
            cleaned_json_str = re.sub(r',\s*([\}\]])', r'\1', json_str) # Remove trailing commas before ] or }
            cleaned_json_str = re.sub(r';\s*$', '', cleaned_json_str) # Remove trailing semicolon if regex didn't catch it
            try:
                json_data = json.loads(cleaned_json_str)
                if isinstance(json_data, list):
                    extracted_data.append({"name": var_name, "data": json_data})
                else:
                    print(f"Warning: Variable '{var_name}' (after cleaning) is not a list. Skipping.")
            except json.JSONDecodeError as e_cleaned:
                 print(f"Warning: Still could not decode JSON for variable '{var_name}' after cleaning. Error: {e_cleaned}. Skipping.")

    return extracted_data

def to_markdown_table(data_list, table_name):
    """
    Converts a list of dictionaries (JSON array items) to a Markdown table.
    Applies fixed widths to columns specified in the fixed_widths dictionary.
    Example fixed_widths: {"名称": 100, "描述": 250}
    """
    if not data_list:
        return f"##### Table {table_name}\n\n_No data to display._\n"



    df = pd.DataFrame(data_list)
    if df.empty:
        return f"##### Table {table_name}\n\n_No data to display or data is not in the expected format._\n"

    all_keys = []
    for item in data_list:
        if isinstance(item, dict):
            for key in item.keys():
                if key not in all_keys:
                    all_keys.append(key)
    
    df = df.reindex(columns=all_keys)
    df = df.loc[:, df.columns != "原名"]
    df = df.loc[:, df.columns != "属性"]
    df.rename(columns={"检定": "属性"}, inplace=True)

    if df.empty: # Check again after removing "原名"
        return f"##### Table {table_name}\n\n_No data to display after filtering columns._\n"

    # Generate the table using pandas
    raw_markdown_table = df.to_markdown(index=False)
    
    # Split the raw markdown table into lines
    lines = raw_markdown_table.split('\n')
    
    if len(lines) < 2: # Not enough lines for header and separator
        return f"##### Table {table_name}\n{raw_markdown_table}\n"

    # Construct the new header with fixed widths from the dictionary
    new_header_parts = []
    for column_name in df.columns: # Iterate in DataFrame's column order
        col_name_str = str(column_name)
        if col_name_str in fixed_widths:
            width = fixed_widths[col_name_str]
            new_header_parts.append(f'<div style="width:{width}px">{col_name_str}</div>')
        else:
            new_header_parts.append(col_name_str)
            
    new_header_line = "| " + " | ".join(new_header_parts) + " |"
    
    # Replace the old header line with the new one
    lines[0] = new_header_line
    
    # Reconstruct the table
    modified_markdown_table = "\n".join(lines)
    
    final_table = f"##### Table {table_name}\n"
    final_table += modified_markdown_table
    final_table += "\n"
    
    return final_table

def js_to_markdown_tables(js_file_path):
    """
    Reads a JS file, extracts JSON arrays, and converts them to Markdown tables.
    """
    try:
        with open(js_file_path, 'r', encoding='utf-8') as f:
            js_content = f.read()
    except FileNotFoundError:
        return f"Error: File not found at {js_file_path}"
    except Exception as e:
        return f"Error reading file {js_file_path}: {e}"

    extracted_jsons = extract_json_from_js(js_content)
    
    if not extracted_jsons:
        return "No suitable 'const xxx = []' structures found in the JS file."

    all_markdown_tables = []
    for item in extracted_jsons:
        table_name = item["name"]
        json_data = item["data"]
        markdown_output = to_markdown_table(json_data, table_name)
        all_markdown_tables.append(markdown_output)
        
    return "\n\n".join(all_markdown_tables)

if __name__ == "__main__":
    filepath = [
        r"E:\zac_personal\DaggerHeart_Character\character_creator\data\equipment_data.js",
        r"E:\zac_personal\DaggerHeart_Character\character_creator\data\consumables_data.js",
        r"E:\zac_personal\DaggerHeart_Character\character_creator\data\items_data.js"
    ]

    output_path = r"release/Daggerheart_Core_Rulebook-5-20-2025"
    for js_file in filepath:
        markdown_result = js_to_markdown_tables(js_file)
        output_file = os.path.join(output_path, os.path.basename(js_file).replace('.js', '.md'))
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(markdown_result)

    # parser = argparse.ArgumentParser(description="Convert JSON arrays in a JS file to Markdown tables.")
    # parser.add_argument("js_file", help="Path to the input JavaScript file.")
    # parser.add_argument("-o", "--output_file", help="Path to the output Markdown file (optional). Prints to console if not provided.")
    
    # args = parser.parse_args()
    
    # markdown_result = js_to_markdown_tables(args.js_file)
    
    # if args.output_file:
    #     try:
    #         with open(args.output_file, 'w', encoding='utf-8') as f:
    #             f.write(markdown_result)
    #         print(f"Markdown tables successfully written to {args.output_file}")
    #     except Exception as e:
    #         print(f"Error writing to output file {args.output_file}: {e}")
    # else:
    #     print(markdown_result)