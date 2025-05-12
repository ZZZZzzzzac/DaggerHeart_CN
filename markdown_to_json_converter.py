import argparse
import json
import re
import os

def parse_markdown_to_json(markdown_filepath):
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
    # 每个匹配对象包含标题行的开始和结束位置。
    matches = list(header_pattern.finditer(content))

    # 遍历找到的标题以定义片段。
    for i, match in enumerate(matches):
        section_key = f"SECTION_{i + 1}"
        
        # 当前片段的开始索引是其标题的开始位置。
        start_index = match.start()

        # 确定当前片段的结束索引。
        # 它是下一个标题的开始位置，如果这是最后一个标题，则是文件的末尾。
        if i + 1 < len(matches):
            end_index = matches[i + 1].start()
        else:
            end_index = len(content)

        # 提取片段的原始内容。
        # 这包括标题和所有文本，直到下一个标题或文件末尾。
        # 保留原始 Markdown 格式。
        original_content_for_section = content[start_index:end_index]
        
        # 片段在下一个标题之前以换行符结束是很常见的。
        # 为了确保数据整洁，特别是如果最后一个片段可能在文件末尾有尾随空格，
        # 我们可以对内容进行 rstrip 操作。
        # 然而，"保持原始 Markdown 格式" 的要求建议进行最少的更改。
        # 切片到下一个标题的 `end_index` (不包括) 应该是精确的。
        # 为安全起见，我们将不对 `original_content_for_section` 进行 stripping。

        sections.append({
            "key": section_key,
            "original": original_content_for_section,
            "translation": "",
            "context": ""
        })

    return sections

def main():
    """
    主函数，用于解析命令行参数，处理 Markdown 文件，
    并将输出保存为 JSON 文件。
    """
    parser = argparse.ArgumentParser(
        description="将按标题分段的 Markdown 文件转换为结构化的 JSON 文件。"
    )
    parser.add_argument(
        "markdown_file", 
        help="输入的 Markdown 文件路径。"
    )
    args = parser.parse_args()

    markdown_filepath = args.markdown_file
    
    # 通过将 .md 扩展名替换为 .json 来确定输出 JSON 文件路径。
    base_filename, _ = os.path.splitext(markdown_filepath)
    output_json_filepath = base_filename + ".json"

    processed_data = parse_markdown_to_json(markdown_filepath)

    if processed_data is not None:
        try:
            with open(output_json_filepath, 'w', encoding='utf-8') as f:
                # 以缩进格式写入 JSON 数据以提高可读性，并设置 ensure_ascii=False
                # 以正确处理非 ASCII 字符。
                json.dump(processed_data, f, ensure_ascii=False, indent=2)
            print(f"成功将 '{markdown_filepath}' 转换为 '{output_json_filepath}'")
        except Exception as e:
            print(f"将 JSON 写入文件 {output_json_filepath} 时出错: {e}")

if __name__ == "__main__":
    main()