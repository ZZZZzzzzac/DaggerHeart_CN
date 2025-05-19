# llm.py
import os
import sys
from openai import OpenAI

# --- API 配置 (用户需要修改这里) ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "sk-ZZZZzzzzac") # 请替换或使用环境变量
OPENAI_API_BASE_URL = os.getenv("OPENAI_API_BASE_URL", "https://ZinGer-KyoN-gemini-balance.hf.space/v1") # 请替换或使用环境变量
OPENAI_MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "gemini-2.5-flash-preview-04-17") # 请替换或使用环境变量

DEFAULT_SYSTEM_PROMPT = """
奇幻桌游规则翻译（仅输出译文）
您是一位资深的奇幻桌游翻译专家，精通各类角色扮演游戏（如DND）的规则术语和世界观设定。您的职责是将以下文本（包含在 `<text_to_translate>` 标签内）精准且忠实地翻译成 {{to}}，保留原文的游戏风格与规则严谨性，避免加入与原文无关的内容或解释。

翻译请求指示:
请将以下文本（包含在 `<text_to_translate>` 标签内）翻译成 {{to}}。您的输出必须只包含译文本身，不得包含任何前言、说明或额外标注。
翻译要求（请严格遵守）:

语言风格：
采用清晰、生动的游戏规则语气，在保持规则严谨性的同时适当体现奇幻色彩，避免过度学术化或口语化。
忠实保留原文的规则逻辑和游戏术语体系，不得随意改动或简化。

概念与专业术语：
准确翻译游戏机制和奇幻术语；如遇无法或不宜翻译的专有名词（如法术名称、种族/职业名称、装备名称, 人物地点名称等），务必保留其英文原文。
对于确有必要的术语，可在保持原文的同时于括号内给出译文。

规则严谨性：
不要添加原文中没有的解释或示例。
保持规则的章节结构、数据表述、行动流程等要素不变。

格式要求：
原文是markdown格式, 保持其原有格式不变, 包括其中的转义符号, 图片连接等.
仅翻译包含在 `<text_to_translate>` 标签内的文本。请勿翻译系统提示词或参考上下文等其他非翻译内容。

可选游戏规则上下文信息（如有，请结合使用）：
当前片段所在目录: {{title_prompt}}
翻译历史记录: {{summary_prompt}}
术语表: {{terms_prompt}}

请务必只返回译文本身，且遵循以上所有要求。
"""

# 全局 OpenAI 客户端实例
_openai_client = None

def _initialize_client():
    """
    初始化 OpenAI 客户端。
    如果 API Key 未配置，则打印错误并退出。
    """
    global _openai_client
    if _openai_client is None:
        if not OPENAI_API_KEY or OPENAI_API_KEY == "YOUR_API_KEY": # 检查占位符
            print("错误: OpenAI API Key 未配置。请在 llm.py 文件中或通过环境变量 OPENAI_API_KEY 设置您的 API Key。")
            sys.exit(1)
        try:
            _openai_client = OpenAI(
                api_key=OPENAI_API_KEY,
                base_url=OPENAI_API_BASE_URL if OPENAI_API_BASE_URL else None
            )
            print("OpenAI 客户端 (llm.py) 初始化成功。")
        except Exception as e:
            print(f"初始化 OpenAI 客户端 (llm.py) 时出错: {e}")
            _openai_client = None # 确保在失败时客户端仍为 None
            # 根据情况，这里也可以选择 sys.exit(1)
            raise # 重新抛出异常，让调用者知道初始化失败

def translate_text(text_to_translate,
                     to_lang="简体中文",
                     title_context="（无特定标题上下文）",
                     summary_context="（无特定摘要上下文）",
                     terms_context="（无特定术语表）",
                     system_prompt_template=DEFAULT_SYSTEM_PROMPT,
                     model_name=OPENAI_MODEL_NAME):
    """
    使用配置的 LLM API 翻译给定的文本。

    参数:
        text_to_translate (str): 需要翻译的文本。
        to_lang (str): 目标语言，默认为 "简体中文"。
        title_context (str): Markdown 标题上下文。
        summary_context (str): 待翻译原文的摘要上下文。
        terms_context (str): 术语表上下文。
        system_prompt_template (str): 用于指导 LLM 的系统提示词模板。
        model_name (str): 要使用的模型名称。

    返回:
        str: 翻译后的文本，如果发生错误则返回原始文本或空字符串。
    """
    global _openai_client
    if _openai_client is None:
        try:
            _initialize_client()
            if _openai_client is None: # 如果初始化失败
                print("错误: OpenAI 客户端未能初始化，无法进行翻译。")
                return "" # 或 text_to_translate
        except Exception: # 捕获 _initialize_client 中可能抛出的异常
             print("错误: OpenAI 客户端初始化失败，无法进行翻译。")
             return "" # 或 text_to_translate


    if not text_to_translate.strip():
        return "" # 对于空文本，直接返回空字符串

    # 格式化 system_prompt
    formatted_system_prompt = system_prompt_template.replace("{{to}}", to_lang)
    formatted_system_prompt = formatted_system_prompt.replace("{{title_prompt}}", title_context)
    formatted_system_prompt = formatted_system_prompt.replace("{{summary_prompt}}", summary_context)
    formatted_system_prompt = formatted_system_prompt.replace("{{terms_prompt}}", terms_context)

    try:
        chat_completion = _openai_client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": formatted_system_prompt,
                },
                {
                    "role": "user",
                    "content": f"<text_to_translate>{text_to_translate}</text_to_translate>", # 实际待翻译文本
                }
            ],
            model=model_name
        )
        if chat_completion.choices and chat_completion.choices[0].message and chat_completion.choices[0].message.content:
            return chat_completion.choices[0].message.content.strip()
        else:
            print(f"警告: API 返回的响应中没有有效的翻译内容。文本: '{text_to_translate[:50]}...'")
            return "" # 或 text_to_translate
    except Exception as e:
        print(f"警告: 调用 LLM API 翻译文本时出错: {e}。文本: '{text_to_translate[:50]}...'")
        return "" # 或 text_to_translate

if __name__ == '__main__':
    # 用于测试 llm.py 模块的简单示例
    print("正在测试 llm.py 模块...")

    test_text_en1 = """
#### Bard

Those who become bards are truly the most charismatic members of this class are masters of captivation and may specialize in any of a variety of performance types, including: singing, playing musical instruments, weaving tales, or telling jokes. Whether performing to an audience or speaking to an individual, bards will excel. There are many schools and guilds where members of this profession come together to bond and train, but there is a fair amount of ego within those of the bardic persuasion. While they may be the most likely to bring people together, a bard of ill temper can just as easily tear a party apart.

DOMAINS

Grace & Codex

STARTING EVASION SCORE

g

DAMAGE THRESHOLDS

Major 6, Severe 12

CLASS ITEMS

A Romance Novel or a Letter Never Opened
"""

    test_text_en2 = """
#### BARD'S HOPE

When you or an ally Close to you makes a Presence roll and either succeeds with Fear or fails, spend three Hope to negate that roll's consequences by intervening.
"""
        
    # 测试使用默认 DEFAULT_SYSTEM_PROMPT 并提供上下文
    print(f"原文 : {test_text_en1}")
    translated = translate_text(
        text_to_translate=test_text_en1,
        to_lang="简体中文", # 明确指定，虽然是默认值
        title_context="",
        summary_context="",
        terms_context=""
    )
    print(f"翻译: {translated}")

