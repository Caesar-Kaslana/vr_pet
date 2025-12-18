# app.py
import os
import json
import requests
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

import gradio as gr
from pet import VirtualPet
from openai import OpenAI

# API
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

SERP_API_KEY = os.getenv("SERPAPI_API_KEY")

# 宠物
pet = VirtualPet(pet_type="猫")

# 搜索
def web_search(query):
    if not SERP_API_KEY:
        return ""
    try:
        r = requests.get(
            "https://serpapi.com/search",
            params={
                "q": query,
                "engine": "google",
                "api_key": SERP_API_KEY,
                "num": 5
            },
            timeout=10
        )
        data = r.json()
        results = []
        for item in data.get("organic_results", []):
            results.append(f"{item.get('title','')}: {item.get('snippet','')}")
        return "\n".join(results[:3])
    except Exception:
        return ""

# 表情 & 心情颜色 
def get_pet_image():
    return {
        "开心": "images/happy.png",
        "兴奋": "images/excited.png",
        "满意": "images/satisfied.png",
        "中性": "images/neutral.png",
        "难过": "images/sad.png",
        "生气": "images/angry.png",
        "害怕": "images/scared.png"
    }.get(pet.mood, "images/neutral.png")

def get_mood_color():
    return {
        "开心": "#FFF0F5",
        "兴奋": "#FFE4B5",
        "满意": "#E6F2FF",
        "中性": "#F5F5F5",
        "难过": "#E0F0FF",
        "生气": "#FFE4E1",
        "害怕": "#EFE6FF"
    }.get(pet.mood, "#FFFFFF")

# 聊天气泡
def build_chat_bubble(history):
    bubbles = ""

    for e in history:
        align = "right" if e["role"] == "user" else "left"
        bg = "#90EE90" if e["role"] == "user" else "#FFB6C1"

        bubbles += f"""
        <div style="clear:both;text-align:{align};margin:8px 0;">
            <div style="
                display:inline-block;
                background:{bg};
                padding:8px 12px;
                border-radius:12px;
                max-width:80%;
                word-break:break-word;
            ">
                {e['content']}
            </div>
        </div>
        """

    return f"""
    <div style="
        background-color:{get_mood_color()};
        padding:12px;
        border-radius:12px;
        min-height:400px;
    ">
        {bubbles}
    </div>
    """

# 核心逻辑 
def chat_with_pet(user_input, pet_type, action, food_type, chat_history):
    pet.type = pet_type
    pet.personality = pet.set_personality()
    today = datetime.now().strftime("%Y年%m月%d日")

    if action == "情绪":
        pet.update_mood(user_input)
        chat_history.append({
            "role": "pet",
            "content": f"奶龙现在是【{pet.mood}】心情～"
        })

    elif action == "喂食":
        msg = pet.feed_pet(food_type)
        chat_history.append({"role": "pet", "content": msg})

    elif user_input.strip():
        chat_history.append({"role": "user", "content": user_input})

        emotion = pet.analyze_user_emotion(user_input)
        pet.update_mood(emotion)

        search_result = web_search(user_input) if pet.need_search(user_input) else ""
        system_prompt = pet.build_system_prompt(today, search_result)

        resp = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ]
        )

        reply = resp.choices[0].message.content.strip()
        pet.update_short_term_memory(user_input, reply)
        chat_history.append({"role": "pet", "content": reply})

    html = build_chat_bubble(chat_history)
    return html, get_pet_image(), pet.get_status(), chat_history, ""

# 清空聊天 
def clear_chat():
    return "", get_pet_image(), pet.get_status(), [], ""

# 导出聊天记录 
def export_chat(chat_history):
    path = "chat_history.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(chat_history, f, ensure_ascii=False, indent=2)
    return path

# 导入聊天记录 
def import_chat(file):
    if file is None:
        return "", get_pet_image(), pet.get_status(), [], ""

    with open(file.name, "r", encoding="utf-8") as f:
        history = json.load(f)

    html = build_chat_bubble(history)
    return html, get_pet_image(), pet.get_status(), history, ""

# UI 
with gr.Blocks() as iface:
    gr.Markdown("<h1 style='text-align:center;color:#FF69B4'>🐾 奶龙 AI 虚拟宠物 🐾</h1>")

    chat_history = gr.State([])

    with gr.Row():
        with gr.Column(scale=2):
            txt_input = gr.Textbox(label="输入消息", placeholder="和奶龙聊聊天吧～")
            btn_send = gr.Button("发送")
            btn_clear = gr.Button("清空聊天记录")

            with gr.Row():
                btn_export = gr.Button("📤 导出聊天记录")
                file_import = gr.File(label="📥 导入聊天记录", file_types=[".json"])

            chat_output = gr.HTML()

        with gr.Column(scale=1):
            pet_img = gr.Image(value=get_pet_image(), show_label=False)
            pet_status = gr.Textbox(value=pet.get_status(), label="状态", interactive=False)
            pet_selector = gr.Dropdown(["猫", "狗"], value="猫", label="宠物类型")
            food_selector = gr.Dropdown(["小鱼干", "猫粮", "糖果", "骨头"], label="食物")
            btn_feed = gr.Button("🍖 喂食")

            gr.Markdown("### 🎭 情绪演示")
            for mood in ["开心", "兴奋", "满意", "中性", "难过", "生气", "害怕"]:
                gr.Button(mood).click(
                    chat_with_pet,
                    inputs=[gr.State(mood), pet_selector, gr.State("情绪"), food_selector, chat_history],
                    outputs=[chat_output, pet_img, pet_status, chat_history, txt_input]
                )

    btn_send.click(
        chat_with_pet,
        inputs=[txt_input, pet_selector, gr.State("聊天"), food_selector, chat_history],
        outputs=[chat_output, pet_img, pet_status, chat_history, txt_input]
    )

    txt_input.submit(
        chat_with_pet,
        inputs=[txt_input, pet_selector, gr.State("聊天"), food_selector, chat_history],
        outputs=[chat_output, pet_img, pet_status, chat_history, txt_input]
    )

    btn_feed.click(
        chat_with_pet,
        inputs=[gr.State(""), pet_selector, gr.State("喂食"), food_selector, chat_history],
        outputs=[chat_output, pet_img, pet_status, chat_history, txt_input]
    )

    btn_clear.click(
        clear_chat,
        outputs=[chat_output, pet_img, pet_status, chat_history, txt_input]
    )

    btn_export.click(
        export_chat,
        inputs=[chat_history],
        outputs=gr.File()
    )

    file_import.change(
        import_chat,
        inputs=[file_import],
        outputs=[chat_output, pet_img, pet_status, chat_history, txt_input]
    )

iface.launch()
