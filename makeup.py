import re
import argparse
import os

def add_image_filename(markdown_text):
    """将 ![](_filename.ext) 转换为 ![_filename.ext](_filename.ext)"""
    # 任务 1: 修复图片语法
    modified_text = re.sub(r'!\[\]\((.*?)\)', r'![\1](\1)', markdown_text)
    return modified_text

def add_heading_markers(markdown_text, level_threshold=3):
    """
    寻找 Markdown 标题 (例如 ## ABC)，并在其后添加标记 ((++ABC))。
    '+' 的数量等于 '#' 的数量。
    仅当标题级别低于或等于 level_threshold 时应用。
    """
    # 正则表达式匹配以 # 开头的行 (Markdown 标题)
    # ^(#+) : 匹配行首的一个或多个 # (捕获组1: #号本身)
    # \s+ : 匹配一个或多个空格
    # (.+) : 匹配标题的其余部分 (捕获组2: 标题文本)
    # $ : 匹配行尾
    match = re.match(r"^(#{1,6})\s+(.*)$", markdown_text)
    if match:
        heading_hashes = match.group(1)
        heading_level = len(heading_hashes)-1
        title_text = match.group(2).strip()

        if heading_level <= level_threshold:
            # 构建标记，例如 ((++Title)) for H2
            marker_plus = '+' * heading_level
            marker = f"(({marker_plus}{title_text}))"
            return f"{markdown_text} {marker}"
    return markdown_text

makeup_list = [
    add_image_filename,
    add_heading_markers, # 添加新函数到列表
]

def process_markdown_file(input_filepath):
    """
    读取指定的 Markdown 文件，对每段文本应用 makeup_list 中的所有函数，
    然后将结果写入新的 Markdown 文件。
    """
    if not os.path.exists(input_filepath):
        print(f"错误：文件 '{input_filepath}' 不存在。")
        return

    try:
        with open(input_filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"读取文件 '{input_filepath}' 时出错: {e}")
        return

    # 按空行分割文本段落
    paragraphs = content.split('\n\n')
    processed_paragraphs = []

    for paragraph in paragraphs:
        processed_paragraph = paragraph
        for func in makeup_list:
            processed_paragraph = func(processed_paragraph) # 默认阈值
        processed_paragraphs.append(processed_paragraph)

    processed_content = '\n\n'.join(processed_paragraphs)

    base, ext = os.path.splitext(input_filepath)
    output_filepath = f"{base}_makeup{ext}"

    try:
        with open(output_filepath, 'w', encoding='utf-8') as f:
            f.write(processed_content)
        print(f"处理完成，结果已写入 '{output_filepath}'")
    except Exception as e:
        print(f"写入文件 '{output_filepath}' 时出错: {e}")

def main():
    parser = argparse.ArgumentParser(description="处理 Markdown 文件，应用一系列转换函数。")
    parser.add_argument("input_file", help="要处理的 Markdown 文件的路径。")
    # 可以选择性地添加一个参数来控制标题级别阈值
    # parser.add_argument("--heading_threshold", type=int, default=3, help="处理标题的最大级别 (默认为 3)。")
    args = parser.parse_args()

    # 如果添加了 heading_threshold 参数，可以在这里传递给 process_markdown_file
    # 然后 process_markdown_file 需要修改以接受并传递它给 add_heading_markers
    process_markdown_file(args.input_file)

if __name__ == "__main__":
    main()
