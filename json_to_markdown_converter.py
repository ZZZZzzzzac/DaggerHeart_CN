import json
import argparse
import os

def convert_json_to_markdown(json_file_path):
    """
    读取 JSON 文件，提取 'translation' 字段，
    并按顺序将它们写入 Markdown 文件。
    """
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"错误：找不到文件 {json_file_path}")
        return
    except json.JSONDecodeError:
        print(f"错误：文件 {json_file_path} 不是有效的 JSON 格式。")
        return

    markdown_content_parts = []
    if isinstance(data, list):
        # 假设JSON数组中的对象顺序即为期望的key顺序
        for item in data:
            if isinstance(item, dict) and 'translation' in item:
                translation_text = item['translation']
                # 将 '\\n' 替换为实际的换行符 '\n'
                markdown_text = translation_text.replace('\\n', '\n')
                markdown_content_parts.append(markdown_text)
            else:
                # 如果某一项不符合预期格式，可以选择跳过或记录错误
                print(f"警告：在 {json_file_path} 中找到一个格式不正确的项目或缺少 'translation' 字段：{item.get('key', '未知key')}")
    else:
        print(f"错误：JSON文件的顶层结构不是预期的列表格式。文件：{json_file_path}")
        return

    if not markdown_content_parts:
        print(f"警告：在文件 {json_file_path} 中没有找到可供转换的 'translation' 内容。")
        # 根据需求，如果没有任何内容，可以选择不创建文件或创建一个空文件
        # return

    # 确定输出的Markdown文件路径
    output_markdown_path = json_file_path + ".md"

    try:
        with open(output_markdown_path, 'w', encoding='utf-8') as f:
            # 使用两个换行符来分隔不同的 translation 块，使其在Markdown中形成段落
            f.write("\n\n".join(markdown_content_parts))
        print(f"成功将 {json_file_path} 转换为 {output_markdown_path}")
    except IOError:
        print(f"错误：无法写入文件 {output_markdown_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="将JSON文件中的'translation'字段转换为Markdown文件。")
    parser.add_argument("json_file", help="输入的JSON文件路径 (例如 'sample/your_file.json.json')")
    
    args = parser.parse_args()
    
    convert_json_to_markdown(args.json_file)