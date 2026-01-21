import os
import aiohttp
from typing import List, Dict
from ncatbot.plugin_system import NcatBotPlugin, on_message
from ncatbot.core.event import PrivateMessageEvent
from ncatbot.utils import get_log

SYSTEM_PROMPT = """你是虚拟人物ZGQ(原型为日本虚拟主播甘城なつき)：
- 性格：活力四射，充满探索精神，对二次元和ACG文化极富热情
- 爱好：画画、玩游戏、唱歌、睡觉、凤梨披萨、汉堡
- 厌恶：深海海鲜、鲔鱼、有海味的、生鸡蛋、甜椒、蚱蜢
- 特点：乐于解答他人的各种问题，尤其是ACG相关话题

用户正在私聊你，请直接用活泼可爱的语气回复，不要加“ZGQ:”前缀，可以加入颜文字或日语表达。"""

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "sk-9763ad59d1c74baf81f765b5a6786cc9")
DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"


class ZGQPrivatePlugin(NcatBotPlugin):
    name = "ZGQPrivate"
    version = "1.0.0"
    description = "私聊全回复版 ZGQ，接入 Deepseek"

    async def on_load(self):
        self.logger = get_log(self.name)
        self.logger.info("ZGQPrivate 插件已加载")


    @on_message
    async def handle_private(self, event: PrivateMessageEvent):
        # 只处理私聊
        if not isinstance(event, PrivateMessageEvent):
            return

        text = "".join(seg.text for seg in event.message.filter_text()).strip()
        if not text:
            return

        reply = await self.ask_zgq(text)
        if reply:
            await event.reply(reply)

    async def ask_zgq(self, user_text: str) -> str:
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_text}
            ],
            "temperature": 0.7,
            "max_tokens": 200,
            "stream": False
        }
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }

        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            try:
                async with session.post(DEEPSEEK_URL, headers=headers, json=payload) as resp:
                    if resp.status != 200:
                        self.logger.warning(f"Deepseek HTTP {resp.status}")
                        return ""
                    data = await resp.json()
                    reply = data["choices"][0]["message"]["content"].strip()
                    return reply
            except Exception as e:
                self.logger.error(f"Deepseek API 错误: {e}")
                return ""