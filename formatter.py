"""消息格式化模块"""

from scraper import ShopItem, get_current_time_slot, is_merchant_active


def format_shop_message(items: list[ShopItem]) -> str:
    """
    格式化商店商品为消息文本

    Args:
        items: 商品列表

    Returns:
        格式化后的消息文本
    """
    time_slot = get_current_time_slot()

    # 非时段提示
    if not is_merchant_active():
        return f"【远行商人】\n当前时段: {time_slot}\n\n远行商人正在休息，请 8:00 后再来查看~"

    if not items:
        return f"【远行商人】\n当前时段: {time_slot}\n\n暂无商品或获取失败"

    lines = [
        f"【远行商人】",
        f"当前时段: {time_slot}",
        "",
        "商品列表:"
    ]

    for i, item in enumerate(items, 1):
        lines.append(f"\n{i}. {item.name}")
        lines.append(f"   类型: {item.item_type}")
        lines.append(f"   限购: {item.limit}")
        lines.append(f"   价格: {item.price}")

    return "\n".join(lines)


if __name__ == "__main__":
    # 测试格式化
    from scraper import fetch_shop_items

    url = "https://www.onebiji.com/hykb_tools/comm/lkwgmerchant/preview.php?id=1"
    items = fetch_shop_items(url)
    message = format_shop_message(items)
    print(message)
