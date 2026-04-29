"""精灵数据模块 - 爬取、缓存、预测精灵蛋"""

import json
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

import requests
from bs4 import BeautifulSoup


@dataclass
class Sprite:
    """精灵数据"""
    name: str           # 精灵名称
    height_min: float   # 身高下限（米）
    height_max: float   # 身高上限（米）
    weight_min: float   # 体重下限（千克）
    weight_max: float   # 体重上限（千克）
    stage: int          # 进化阶段（1=一阶段）
    url: str            # 详情页URL


# 数据文件路径
DATA_DIR = Path(__file__).parent / "data"
SPRITES_FILE = DATA_DIR / "sprites.json"


def load_sprites() -> list[Sprite]:
    """
    从缓存加载精灵数据

    Returns:
        精灵列表，无缓存返回空列表
    """
    if not SPRITES_FILE.exists():
        return []

    try:
        with open(SPRITES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [Sprite(**item) for item in data]
    except (json.JSONDecodeError, KeyError) as e:
        print(f"[错误] 加载精灵数据失败: {e}")
        return []


def save_sprites(sprites: list[Sprite]) -> bool:
    """
    保存精灵数据到缓存

    Args:
        sprites: 精灵列表

    Returns:
        是否保存成功
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    try:
        data = [asdict(s) for s in sprites]
        with open(SPRITES_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"[完成] 已保存 {len(sprites)} 个精灵数据")
        return True
    except Exception as e:
        print(f"[错误] 保存精灵数据失败: {e}")
        return False


def parse_height_weight(text: str) -> tuple[Optional[float], Optional[float]]:
    """
    解析身高体重范围字符串

    Args:
        text: 如 "0.53~0.75M" 或 "3.62~4.6KG"

    Returns:
        (最小值, 最大值) 或 (None, None)
    """
    # 匹配 "数字~数字单位" 格式
    match = re.search(r"([\d.]+)\s*~\s*([\d.]+)", text)
    if match:
        try:
            min_val = float(match.group(1))
            max_val = float(match.group(2))
            return min_val, max_val
        except ValueError:
            pass
    return None, None


def fetch_sprite_list() -> list[str]:
    """
    从精灵蛋图鉴获取可孵化精灵名称列表

    Returns:
        精灵名称列表
    """
    url = "https://wiki.biligame.com/rocom/%E7%B2%BE%E7%81%B5%E8%9B%8B%E5%9B%BE%E9%89%B4"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"[错误] 获取精灵蛋图鉴失败: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")

    # 查找精灵蛋卡片中的精灵名称
    names = []
    # 精灵蛋名称格式: "喵喵的蛋" 或 "喵喵的蛋（xxx）"
    egg_links = soup.select("a[href*='/rocom/']")

    for link in egg_links:
        text = link.get_text(strip=True)
        # 匹配 "xxx的蛋" 格式
        match = re.match(r"(.+?)的蛋", text)
        if match:
            name = match.group(1)
            # 排除重复和特殊标记
            if name and name not in names and not name.startswith("文件"):
                names.append(name)

    print(f"[获取] 发现 {len(names)} 个可孵化精灵")
    return names


def fetch_sprite_detail(name: str) -> Optional[Sprite]:
    """
    获取单个精灵的详细信息

    Args:
        name: 精灵名称

    Returns:
        Sprite 对象或 None
    """
    # URL编码精灵名称
    from urllib.parse import quote
    url = f"https://wiki.biligame.com/rocom/{quote(name)}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"[警告] 获取 {name} 详情失败: {e}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    content = soup.get_text()

    # 查找身高体重数据
    # 格式: "0.53~0.75M" 和 "3.62~4.6KG"
    height_match = re.search(r"([\d.]+)\s*~\s*([\d.]+)\s*M", content)
    weight_match = re.search(r"([\d.]+)\s*~\s*([\d.]+)\s*KG", content)

    if not height_match or not weight_match:
        print(f"[跳过] {name} 缺少身高体重数据")
        return None

    try:
        height_min = float(height_match.group(1))
        height_max = float(height_match.group(2))
        weight_min = float(weight_match.group(1))
        weight_max = float(weight_match.group(2))
    except ValueError:
        print(f"[跳过] {name} 身高体重数据格式错误")
        return None

    return Sprite(
        name=name,
        height_min=height_min,
        height_max=height_max,
        weight_min=weight_min,
        weight_max=weight_max,
        stage=1,  # 可孵化精灵都是一阶段
        url=url
    )


def fetch_all_sprites() -> list[Sprite]:
    """
    爬取所有可孵化精灵数据

    Returns:
        精灵列表
    """
    names = fetch_sprite_list()
    if not names:
        print("[错误] 未获取到精灵列表")
        return []

    sprites = []
    total = len(names)

    for i, name in enumerate(names, 1):
        print(f"[爬取] {i}/{total} {name}...")
        sprite = fetch_sprite_detail(name)
        if sprite:
            sprites.append(sprite)

    print(f"[完成] 成功爬取 {len(sprites)} 个精灵数据")
    return sprites


def predict_sprites(height: float, weight: float) -> list[Sprite]:
    """
    根据身高体重预测可能的精灵

    Args:
        height: 身高（米）
        weight: 体重（千克）

    Returns:
        匹配的精灵列表，按名称排序
    """
    sprites = load_sprites()
    if not sprites:
        # 无数据时自动爬取
        print("[数据] 无缓存，开始爬取精灵数据...")
        sprites = fetch_all_sprites()
        if sprites:
            save_sprites(sprites)
        else:
            return []

    matched = []
    for sprite in sprites:
        # 精确匹配：身高体重都在范围内
        if (sprite.height_min <= height <= sprite.height_max and
            sprite.weight_min <= weight <= sprite.weight_max):
            matched.append(sprite)

    # 按名称排序
    matched.sort(key=lambda s: s.name)
    return matched


def format_prediction_message(sprites: list[Sprite], height: float, weight: float) -> str:
    """
    格式化预测结果为QQ消息

    Args:
        sprites: 匹配的精灵列表
        height: 查询身高
        weight: 查询体重

    Returns:
        格式化的消息字符串
    """
    lines = [f"精灵蛋预测", f"身高: {height}m  体重: {weight}kg", ""]

    if not sprites:
        lines.append("未找到匹配的精灵")
        lines.append("请检查输入是否正确")
        return "\n".join(lines)

    lines.append(f"可能孵化出 {len(sprites)} 个精灵:")
    lines.append("")

    for sprite in sprites:
        lines.append(
            f"• {sprite.name} "
            f"(身高: {sprite.height_min}~{sprite.height_max}m, "
            f"体重: {sprite.weight_min}~{sprite.weight_max}kg)"
        )

    return "\n".join(lines)


def update_sprite_data() -> bool:
    """
    更新精灵数据缓存

    Returns:
        是否更新成功
    """
    print("[更新] 开始爬取精灵数据...")
    sprites = fetch_all_sprites()
    if sprites:
        return save_sprites(sprites)
    return False


if __name__ == "__main__":
    # 测试：爬取并保存数据
    update_sprite_data()
