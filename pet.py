# pet.py
from textblob import TextBlob
import random
import json
import os

class VirtualPet:
    def __init__(self, pet_type="猫"):
        self.name = "奶龙"
        self.type = pet_type
        self.mood = "中性"
        self.exp = 0
        self.level = 1
        self.feed_count = 0
        self.max_feed = 5
        self.personality = self.set_personality()

        self.short_term_memory = []
        self.long_term_memory = {"user_likes": [], "pet_habits": {}}
        self.memory_file = "nailong_memory.json"
        self.load_memory()

    def set_personality(self):
        return "可爱黏人" if self.type == "猫" else "热情活泼"

    # 搜索判断 
    def need_search(self, text):
        keywords = ["今天", "几号", "现在", "最新", "新闻", "时间", "发生"]
        return any(k in text for k in keywords)

    # 情绪 
    def analyze_user_emotion(self, text):
        text = text.lower()

        positive = [
            "开心", "高兴", "快乐", "不错", "很好", "喜欢", "幸福", "爽", "棒"
        ]
        excited = [
            "太好了", "激动", "兴奋", "爽爆", "开心死了"
        ]
        negative = [
            "难过", "伤心", "心情不好", "不开心", "郁闷", "倒霉", "烦", "崩溃"
        ]
        angry = [
            "生气", "愤怒", "气死", "讨厌", "烦死了", "受不了"
        ]
        scared = [
            "害怕", "恐惧", "担心", "焦虑", "紧张", "怕"
        ]

        if any(w in text for w in excited):
            return "兴奋"
        if any(w in text for w in positive):
            return "开心"
        if any(w in text for w in angry):
            return "生气"
        if any(w in text for w in scared):
            return "害怕"
        if any(w in text for w in negative):
            return "难过"

        return "中性"


    def update_mood(self, mood):
        self.mood = mood
        self.exp += 2 if mood in ["开心", "兴奋", "满意"] else 1
        self.level = 1 + self.exp // 10
        self.save_memory()

    # 投喂 
    def feed_pet(self, food):
        if self.feed_count >= self.max_feed:
            return "奶龙今天已经吃饱啦～"

        effects = {
            "小鱼干": (5, "开心"),
            "猫粮": (3, "满意"),
            "糖果": (2, "兴奋"),
            "骨头": (4, "开心")
        }
        exp, mood = effects.get(food, (1, "满意"))
        self.exp += exp
        self.mood = mood
        self.feed_count += 1
        self.level = 1 + self.exp // 10
        self.save_memory()
        return f"奶龙吃了{food}，经验+{exp}，现在{self.mood}～"

    # Prompt
    def build_system_prompt(self, today, search_result):
        memory = "\n".join(
            [f"{m['role']}: {m['content']}" for m in self.short_term_memory[-6:]]
        )

        search_block = f"\n【联网搜索结果】\n{search_result}\n" if search_result else ""

        return f"""
你是一只名叫【奶龙】的虚拟{self.type}宠物
性格：{self.personality}
当前心情：{self.mood}

今天的真实日期是：{today}
{search_block}

规则：
- 现实 / 时间 / 最新问题 → 必须基于日期和搜索结果
- 闲聊 → 可爱宠物语气
- 不要编造事实

最近对话：
{memory}
"""

    # 记忆
    def update_short_term_memory(self, user, pet):
        self.short_term_memory.append({"role": "user", "content": user})
        self.short_term_memory.append({"role": "pet", "content": pet})
        self.short_term_memory = self.short_term_memory[-10:]
        self.save_memory()

    def get_status(self):
        return f"奶龙({self.type}) | 性格:{self.personality} | 心情:{self.mood} | 等级:{self.level}"

    def save_memory(self):
        with open(self.memory_file, "w", encoding="utf-8") as f:
            json.dump(self.__dict__, f, ensure_ascii=False, indent=2)

    def load_memory(self):
        if os.path.exists(self.memory_file):
            with open(self.memory_file, "r", encoding="utf-8") as f:
                self.__dict__.update(json.load(f))
