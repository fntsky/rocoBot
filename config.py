"""配置模块"""

import json
from pathlib import Path

# 加载配置
CONFIG_FILE = Path(__file__).parent / "config.json"
CONFIG_EXAMPLE = {
    "group_id": 123456789,
    "api_port": 3000,
    "shop_url": "https://www.onebiji.com/hykb_tools/comm/lkwgmerchant/preview.php?id=1"
}

if not CONFIG_FILE.exists():
    print(f"[错误] 配置文件不存在: {CONFIG_FILE}")
    print(f"[提示] 请复制 config.example.json 为 config.json 并修改配置")
    exit(1)

with open(CONFIG_FILE, "r", encoding="utf-8") as f:
    config = json.load(f)

GROUP_ID = config["group_id"]
API_PORT = config.get("api_port", 3000)
API_URL = f"http://127.0.0.1:{API_PORT}"
WS_URL = f"ws://127.0.0.1:{API_PORT}"
SHOP_URL = config.get("shop_url", CONFIG_EXAMPLE["shop_url"])
