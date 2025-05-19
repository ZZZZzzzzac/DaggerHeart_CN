# converter.py
import argparse
import json
import re
import os

# --- 从 markdown_to_json_converter.py 复制的函数 ---

def md2json(markdown_filepath):
    """
    读取 Markdown 文件，按标题分割其内容，并将其构造成一个字典列表。

    每个字典代表一个以标题开头的片段，并包含：
    - key: 片段的唯一标识符 (例如, "SECTION_1")。
    - original: 片段的完整原始 Markdown 内容，包括标题。
    - translation: 一个空字符串，用于翻译的占位符。
    - context: 一个空字符串，用于上下文的占位符。

    参数:
        markdown_filepath (str): 输入的 Markdown 文件路径。

    返回:
        list: 代表这些片段的字典列表，如果发生错误则返回 None。
    """
    try:
        with open(markdown_filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"错误: 文件未找到于 {markdown_filepath}")
        return None
    except Exception as e:
        print(f"读取文件 {markdown_filepath} 时出错: {e}")
        return None

    sections = []
    # 用于查找 markdown 标题的正则表达式 (例如, # 标题, ## 子标题)。
    # 它匹配以 1 到 6 个 '#' 字符开头，后跟一个空格和文本的行。
    header_pattern = re.compile(r"^(#{1,6}\s+.*)$", re.MULTILINE)

    # 在内容中查找所有标题匹配项。
    matches = list(header_pattern.finditer(content))

    # 遍历找到的标题以定义片段。
    for i, match in enumerate(matches):
        section_key = f"SECTION_{i + 1}"
        start_index = match.start()

        # 确定当前片段的结束索引。
        if i + 1 < len(matches):
            end_index = matches[i + 1].start()
        else:
            end_index = len(content)

        # 提取片段的原始内容。
        original_content_for_section = content[start_index:end_index]

        sections.append({
            "key": section_key,
            "original": original_content_for_section.strip(), # 去除末尾可能多余的空白
            "translation": "",
            "context": ""
        })

    return sections

# --- 从 json_to_markdown_converter.py 复制并修改的函数 ---

def json2md(json_file_path):
    """
    读取 JSON 文件，提取 'translation' 字段，并将它们组合成一个 Markdown 字符串。

    参数:
        json_file_path (str): 输入的 JSON 文件路径。

    返回:
        str: 组合后的 Markdown 内容字符串，如果出错则返回 None。
    """
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"错误：找不到文件 {json_file_path}")
        return None
    except json.JSONDecodeError:
        print(f"错误：文件 {json_file_path} 不是有效的 JSON 格式。")
        return None

    markdown_content_parts = []
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict) and 'translation' in item:
                translation_text = item.get('translation', '') # 使用 get 以防万一
                # 将 '\\n' 替换为实际的换行符 '\n'
                markdown_text = translation_text.replace('\\n', '\n')
                markdown_content_parts.append(markdown_text)
            else:
                print(f"警告：在 {json_file_path} 中找到一个格式不正确的项目或缺少 'translation' 字段：{item.get('key', '未知key')}")
    else:
        print(f"错误：JSON文件的顶层结构不是预期的列表格式。文件：{json_file_path}")
        return None

    if not markdown_content_parts:
        print(f"警告：在文件 {json_file_path} 中没有找到可供转换的 'translation' 内容。")
        # 返回空字符串，让调用者决定如何处理
        return ""

    # 使用两个换行符来分隔不同的 translation 块
    return "\n\n".join(markdown_content_parts)

# --- 主逻辑 ---

def main():
    """
    主函数，用于解析命令行参数，根据文件类型调用相应的转换函数，
    并将输出保存到新文件中。
    """
    parser = argparse.ArgumentParser(
        description="根据文件扩展名将 Markdown 文件转换为 JSON 或将 JSON 文件转换为 Markdown。"
    )
    parser.add_argument(
        "input_file",
        help="输入的 Markdown (.md) 或 JSON (.json) 文件路径。"
    )
    args = parser.parse_args()

    input_filepath = args.input_file
    base_filename, extension = os.path.splitext(input_filepath)
    extension = extension.lower() # 统一转为小写以进行比较

    if extension == ".md":
        # Markdown 到 JSON 的转换
        output_json_filepath = input_filepath + ".json"
        processed_data = md2json(input_filepath)

        if processed_data is not None:
            try:
                with open(output_json_filepath, 'w', encoding='utf-8') as f:
                    json.dump(processed_data, f, ensure_ascii=False, indent=2)
                print(f"成功将 '{input_filepath}' 转换为 '{output_json_filepath}'")
            except Exception as e:
                print(f"将 JSON 写入文件 {output_json_filepath} 时出错: {e}")
        else:
            print(f"未能处理 Markdown 文件: {input_filepath}")

    elif extension == ".json":
        # JSON 到 Markdown 的转换
        output_markdown_filepath = input_filepath + ".md" # 输出文件名基于输入的基本名
        markdown_content = json2md(input_filepath)

        if markdown_content is not None:
            try:
                with open(output_markdown_filepath, 'w', encoding='utf-8') as f:
                    f.write(markdown_content)
                # 即使内容为空也报告成功，因为文件已创建
                print(f"成功将 '{input_filepath}' 转换为 '{output_markdown_filepath}'")
            except IOError as e:
                print(f"错误：无法写入文件 {output_markdown_filepath}: {e}")
        else:
             print(f"未能处理 JSON 文件: {input_filepath}")

    else:
        print(f"错误: 不支持的文件类型 '{extension}'。请输入 .md 或 .json 文件。")

if __name__ == "__main__":
    main()