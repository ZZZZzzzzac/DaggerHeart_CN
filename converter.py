# converter.py
import argparse
import json
import re
import os
from tqdm import tqdm # 用于显示进度条
import sys # 用于在 API Key 未设置时退出 (llm.py 中会处理)
import llm # 导入新的 llm 模块
from collections import deque # 用于 summary_context

def load_terms_from_json(json_filepath):
    """
    从指定的 JSON 文件加载术语表。
    JSON 文件应该是一个对象列表，每个对象包含 "term" 和 "translation" 键。
    """
    glossary = {}
    try:
        with open(json_filepath, 'r', encoding='utf-8') as f:
            terms_data = json.load(f)
        if isinstance(terms_data, list):
            for item in terms_data:
                if isinstance(item, dict) and "term" in item and "translation" in item:
                    glossary[item["term"]] = item["translation"]
                else:
                    print(f"警告: 在 {json_filepath} 中找到格式不正确或缺少键的术语条目: {item}")
        else:
            print(f"错误: {json_filepath} 的顶层结构不是预期的列表格式。")
    except FileNotFoundError:
        print(f"错误: 术语文件未找到于 {json_filepath}")
    except json.JSONDecodeError:
        print(f"错误: 术语文件 {json_filepath} 不是有效的 JSON 格式。")
    except Exception as e:
        print(f"加载术语文件 {json_filepath} 时出错: {e}")
    return glossary
# --- 常量定义 ---
MAX_SUMMARY_CONTEXT_ITEMS = 3 # summary_prompt 保留最近 X 次翻译的原文数量
TERMS_GLOSSARY = load_terms_from_json('sample/terms-14448.json') # terms_prompt 的固定术语表

# --- 从 markdown_to_json_converter.py 复制的函数 ---

def md2json(markdown_filepath, translate=False):
    """
    读取 Markdown 文件，按标题分割其内容，并将其构造成一个字典列表。
    如果启用了翻译功能，则会尝试翻译每个片段的原始内容，并利用上下文信息。

    每个字典代表一个以标题开头的片段，并包含：
    - key: 片段的唯一标识符 (例如, "SECTION_1")。
    - original: 片段的完整原始 Markdown 内容，包括标题。
    - translation: 如果启用了翻译并且成功，则为翻译后的内容；否则为空字符串。
    - context: 一个空字符串，用于上下文的占位符。(此字段在此版本中未被积极使用，但保留结构)

    参数:
        markdown_filepath (str): 输入的 Markdown 文件路径。
        translate (bool): 如果为 True，则启用翻译功能。

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
    header_pattern = re.compile(r"^(#{1,6}\s+.*)$", re.MULTILINE)
    matches = list(header_pattern.finditer(content))

    # 根据是否启用翻译来确定迭代器和描述
    iterable_desc = "处理并翻译片段" if translate else "处理片段"
    iterable = tqdm(enumerate(matches), total=len(matches), desc=iterable_desc) if matches else enumerate(matches)

    current_title_hierarchy = [""] * 6 # 用于 title_context, 索引 0-5 对应 H1-H6
    recent_translation_pairs = deque(maxlen=MAX_SUMMARY_CONTEXT_ITEMS) # 用于 summary_context，存储 {"原文": "...", "译文": "..."}
    terms_context_str = json.dumps(TERMS_GLOSSARY, ensure_ascii=False) # terms_prompt

    for i, match in iterable:
        section_key = f"SECTION_{i + 1}"
        current_header_line = match.group(1).strip()
        header_level = current_header_line.count('#') # 1-based (1 to 6)
        
        # 更新当前级别的标题
        current_title_hierarchy[header_level - 1] = current_header_line
       

        title_context_str = "\n".join(current_title_hierarchy[:header_level])

        start_index = match.start()
        if i + 1 < len(matches):
            end_index = matches[i + 1].start()
        else:
            end_index = len(content)

        original_content_for_section = content[start_index:end_index].strip()
        translated_text = ""

        if translate:
            if not original_content_for_section.strip():
                print(f"警告: 片段 '{section_key}' 内容为空，跳过翻译。")
            else:
                # 构建 summary_context 的 JSON 字符串
                summary_list_for_context = list(recent_translation_pairs)
                summary_context_str = json.dumps(summary_list_for_context, ensure_ascii=False) if summary_list_for_context else "[]"

                translated_text = llm.translate_text(
                    text_to_translate=original_content_for_section,
                    # to_lang 默认为 "简体中文" 在 llm.py 中处理
                    title_context=title_context_str,
                    summary_context=summary_context_str,
                    terms_context=terms_context_str
                )
                
                if not translated_text:
                     print(f"信息: 片段 '{section_key}' 未能成功翻译或返回空结果。")
                
                # 更新最近翻译对列表
                # 即使翻译失败，translated_text 也会是空字符串，符合预期
                recent_translation_pairs.append({"原文": original_content_for_section, "译文": translated_text if translated_text else ""})

        sections.append({
            "key": section_key,
            "original": original_content_for_section,
            "translation": translated_text,
            "context": "" # 保留字段
        })

    if translate and not matches:
        print("没有找到可供翻译的 Markdown 片段。")
    elif not matches:
        print("没有找到 Markdown 片段。")

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
        description="根据文件扩展名将 Markdown 文件转换为 JSON 或将 JSON 文件转换为 Markdown。可选翻译功能。"
    )
    parser.add_argument(
        "input_file",
        help="输入的 Markdown (.md) 或 JSON (.json) 文件路径。"
    )
    parser.add_argument(
        "--translate",
        action="store_true",
        help="启用翻译功能 (仅当输入为 .md 文件时有效)。"
    )
    args = parser.parse_args()

    input_filepath = args.input_file
    base_filename, extension = os.path.splitext(input_filepath)
    extension = extension.lower() # 统一转为小写以进行比较

    if extension == ".md":
        # Markdown 到 JSON 的转换
        output_json_filepath = input_filepath + ".json"
        processed_data = md2json(input_filepath, translate=args.translate)

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