"""远行商人QQ机器人 - OneBot v11 WebSocket"""

import json
import threading
import time

import requests
import websockets

from scraper import fetch_shop_items, is_merchant_active
from formatter import format_shop_message
from config import GROUP_ID, API_URL, WS_URL, SHOP_URL
from sprite_data import predict_sprites, format_prediction_message, update_sprite_data, load_sprites


class OneBotAPI:
    """OneBot v11 HTTP API 封装"""

    def __init__(self, api_url: str):
        self.api_url = api_url

    def send_group_message(self, group_id: int, message: str) -> bool:
        """发送群消息"""
        try:
            response = requests.post(
                f"{self.api_url}/send_group_msg",
                json={"group_id": group_id, "message": message},
                timeout=10
            )
            result = response.json()
            if result.get("status") == "ok":
                print(f"[发送] 消息已发送到群 {group_id}")
                return True
            else:
                print(f"[错误] 发送失败: {result}")
                return False
        except Exception as e:
            print(f"[错误] 发送消息异常: {e}")
            return False

    def get_login_info(self) -> dict | None:
        """获取登录信息"""
        try:
            response = requests.get(f"{self.api_url}/get_login_info", timeout=10)
            result = response.json()
            if result.get("status") == "ok":
                return result.get("data")
        except Exception as e:
            print(f"[错误] 获取登录信息失败: {e}")
        return None


# 全局 API 实例
bot = OneBotAPI(API_URL)
self_qq = None  # 机器人QQ号


def get_help_message() -> str:
    """获取帮助消息"""
    return """📖 命令帮助

@机器人 远行商人 - 查询当前远行商人商店
@机器人 <身高> <体重> - 预测精灵蛋孵化结果（如 @机器人 0.6 4）
#更新精灵数据 - 更新精灵数据库"""


def get_shop_message() -> str:
    """获取商店消息"""
    if not is_merchant_active():
        return format_shop_message([])
    items = fetch_shop_items(SHOP_URL)
    return format_shop_message(items)


def push_shop_info():
    """推送商店信息"""
    if not is_merchant_active():
        print("[跳过] 当前无远行商人，不推送")
        return

    text = get_shop_message()
    bot.send_group_message(GROUP_ID, text)


def handle_event(data: dict):
    """处理事件"""
    global self_qq

    post_type = data.get("post_type")

    # 连接成功事件
    if post_type == "meta_event" and data.get("meta_event_type") == "lifecycle":
        if data.get("sub_type") == "connect":
            self_qq = data.get("self_id")
            print(f"[连接] WebSocket 已连接，机器人QQ: {self_qq}")

    # 群消息事件
    if post_type == "message" and data.get("message_type") == "group":
        handle_group_message(data)


def handle_group_message(data: dict):
    """处理群消息"""
    global self_qq

    group_id = data.get("group_id")
    user_id = data.get("user_id")
    message = data.get("message", "")

    # 只处理目标群的消息
    if group_id != GROUP_ID:
        return

    # 解析消息
    is_at_bot = False
    text_content = ""

    if isinstance(message, list):
        for msg in message:
            if msg.get("type") == "at":
                qq = msg.get("data", {}).get("qq")
                if qq == str(self_qq):
                    is_at_bot = True
            elif msg.get("type") == "text":
                text_content += msg.get("data", {}).get("text", "")
    elif isinstance(message, str):
        text_content = message

    text_content = text_content.strip()

    # 帮助指令
    if is_at_bot and ("help" in text_content.lower() or "帮助" in text_content):
        print(f"[消息] 用户 {user_id} 在群 {group_id} 查询帮助")
        text = get_help_message()
        bot.send_group_message(group_id, text)

    # 远行商人指令
    if is_at_bot and "远行商人" in text_content:
        print(f"[消息] 用户 {user_id} 在群 {group_id} 触发远行商人指令")
        text = get_shop_message()
        bot.send_group_message(group_id, text)

    # 精灵蛋预测指令：@机器人 身高 体重
    if is_at_bot:
        # 解析身高体重数字
        import re
        numbers = re.findall(r"[\d.]+", text_content)
        if len(numbers) >= 2:
            try:
                height = float(numbers[0])
                weight = float(numbers[1])
                print(f"[消息] 用户 {user_id} 查询精灵蛋: {height}m {weight}kg")
                sprites = predict_sprites(height, weight)
                text = format_prediction_message(sprites, height, weight)
                bot.send_group_message(group_id, text)
            except ValueError:
                pass  # 不是有效数字，忽略

    # 更新精灵数据指令
    if "#更新精灵数据" in text_content or "#更新精灵" in text_content:
        print(f"[消息] 用户 {user_id} 触发更新精灵数据")
        success = update_sprite_data()
        if success:
            sprites = load_sprites()
            bot.send_group_message(group_id, f"精灵数据已更新，共 {len(sprites)} 个精灵")
        else:
            bot.send_group_message(group_id, "精灵数据更新失败，请稍后重试")


def check_and_push():
    """定时检查并推送"""
    now = time.localtime()
    hour = now.tm_hour
    minute = now.tm_min

    # 检查是否是时段开始后10分钟
    push_times = [(8, 10), (12, 10), (16, 10), (20, 10)]

    for h, m in push_times:
        if hour == h and minute == m:
            push_shop_info()
            return


async def websocket_client():
    """WebSocket 客户端"""
    print(f"[连接] 正在连接 WebSocket: {WS_URL}")

    while True:
        try:
            async with websockets.connect(WS_URL) as ws:
                print("[连接] WebSocket 连接成功")

                async for message in ws:
                    try:
                        data = json.loads(message)
                        handle_event(data)
                    except json.JSONDecodeError:
                        pass

        except Exception as e:
            print(f"[错误] WebSocket 连接失败: {e}")
            print("[重试] 5秒后重连...")
            await asyncio.sleep(5)


import asyncio

def run_websocket():
    """运行 WebSocket 客户端"""
    asyncio.run(websocket_client())


def main():
    print(f"[配置] 目标群: {GROUP_ID}")
    print(f"[配置] API地址: {API_URL}")
    print(f"[配置] WebSocket: {WS_URL}")
    print(f"[配置] 商店URL: {SHOP_URL}")

    # 检查精灵数据
    sprites = load_sprites()
    if sprites:
        print(f"[数据] 已加载 {len(sprites)} 个精灵数据")
    else:
        print("[数据] 精灵数据为空，首次查询时将自动爬取")

    # 检查连接
    login_info = bot.get_login_info()
    if login_info:
        print(f"[连接] 已连接，机器人QQ: {login_info.get('user_id')}, 昵称: {login_info.get('nickname')}")
    else:
        print("[警告] 无法连接到 NapCat API，请确认 NapCat 已启动")

    # 启动 WebSocket 客户端（在后台线程）
    ws_thread = threading.Thread(target=run_websocket, daemon=True)
    ws_thread.start()

    # 主循环：每分钟检查一次
    print("[运行] 开始定时检查...")
    while True:
        time.sleep(60)
        check_and_push()


if __name__ == "__main__":
    main()
