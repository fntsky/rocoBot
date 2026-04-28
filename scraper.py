"""远行商人商店爬取模块"""

import re
from dataclasses import dataclass
from datetime import datetime

import requests
from bs4 import BeautifulSoup


@dataclass
class ShopItem:
    """商店物品"""
    name: str
    item_type: str
    limit: int
    price: str
    description: str


def fetch_shop_items(url: str) -> list[ShopItem]:
    """
    爬取远行商人商店当前时段的商品

    Args:
        url: 商店页面URL

    Returns:
        当前显示的商品列表
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"[错误] 请求失败: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    shop_list = soup.select('.shop-list li')

    items = []
    for li in shop_list:
        # 只提取当前显示的商品（排除 display:none）
        style = li.get('style', '')
        if 'display:none' in style:
            continue

        # 提取 onclick 中的商品信息
        onclick = li.get('onclick', '')
        match = re.search(
            r"showShopinfo\('([^']+)','([^']+)','([^']+)','([^']+)'\)",
            onclick
        )

        if not match:
            continue

        img, name, item_type, description = match.groups()

        # 提取限购和价格
        limit_match = re.search(r'限购(\d+)', str(li))
        price_match = re.search(r'价格：(\S+)', str(li))

        limit = int(limit_match.group(1)) if limit_match else 0
        price = price_match.group(1) if price_match else '未知'

        items.append(ShopItem(
            name=name,
            item_type=item_type,
            limit=limit,
            price=price,
            description=description
        ))

    return items


def get_current_time_slot() -> str:
    """获取当前时段"""
    now = datetime.now()
    hour = now.hour

    if 0 <= hour < 8:
        return "无商人 (0:00-8:00)"
    elif 8 <= hour < 12:
        return "8:00-12:00"
    elif 12 <= hour < 16:
        return "12:00-16:00"
    elif 16 <= hour < 20:
        return "16:00-20:00"
    else:
        return "20:00-24:00"


def is_merchant_active() -> bool:
    """检查当前是否有远行商人（0:00-8:00 无商人）"""
    hour = datetime.now().hour
    return 8 <= hour < 24


if __name__ == "__main__":
    # 测试爬取
    url = "https://www.onebiji.com/hykb_tools/comm/lkwgmerchant/preview.php?id=1"
    items = fetch_shop_items(url)

    print(f"当前时段: {get_current_time_slot()}")
    print(f"商品数量: {len(items)}")

    for item in items:
        print(f"\n{item.name}")
        print(f"  类型: {item.item_type}")
        print(f"  限购: {item.limit}")
        print(f"  价格: {item.price}")
