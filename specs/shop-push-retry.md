# Spec: 远行商人定时推送重试机制

## Objective
定时推送远行商人商店信息时，如果爬取失败（返回空列表），自动每分钟重试，直到获取成功或达到重试上限。避免因临时网络波动导致群内收不到商店推送。

## 背景
当前 `check_and_push()` 在固定时间点（8:10、12:10、16:10、20:10）调用 `push_shop_info()`。`push_shop_info()` 内部调用 `fetch_shop_items()`，若爬取失败返回空列表，消息照常发送（显示"暂无商品"），不会重试。

## 功能需求

### 重试触发条件
- 仅在**定时推送**场景触发重试
- 当 `fetch_shop_items()` 返回空列表时视为获取失败，触发重试
- 用户主动查询远行商人时不触发重试（用户可自行再次查询）

### 重试行为
- 每分钟重试一次爬取
- 重试成功后自动推送商店信息到群
- 最多重试 10 次（共 10 分钟窗口）
- 超过重试上限后放弃，不推送任何消息
- 每次重试记录日志

### 重试期间去重
- 同一时段只触发一组重试，避免多个重试并行
- 如果已在重试中，不启动新的重试序列

## 技术方案

### 修改文件
- `main.py` — 新增异步重试逻辑

### 实现方式
使用后台线程异步重试，不阻塞主循环：

```python
import threading

MAX_RETRY = 10
_retrying = False  # 防止并行重试的全局标志


def _retry_push():
    """后台重试推送商店信息，每分钟重试一次，最多10次"""
    global _retrying
    try:
        for attempt in range(1, MAX_RETRY + 1):
            print(f"[重试] 远行商人数据获取失败，{attempt}/{MAX_RETRY} 次重试，60秒后重试...")
            time.sleep(60)
            items = fetch_shop_items(SHOP_URL)
            if items:
                text = format_shop_message(items)
                bot.send_group_message(GROUP_ID, text)
                print(f"[成功] 第 {attempt} 次重试成功")
                return
        print(f"[失败] 远行商人数据获取失败，已重试 {MAX_RETRY} 次，放弃推送")
    finally:
        _retrying = False


def push_shop_with_retry():
    """推送商店信息，失败时启动后台重试线程"""
    global _retrying

    items = fetch_shop_items(SHOP_URL)
    if items:
        text = format_shop_message(items)
        bot.send_group_message(GROUP_ID, text)
        return

    # 爬取失败，启动后台重试
    if _retrying:
        print("[跳过] 已有重试任务进行中")
        return

    _retrying = True
    retry_thread = threading.Thread(target=_retry_push, daemon=True)
    retry_thread.start()
    print(f"[重试] 远行商人数据获取失败，已启动后台重试（最多{MAX_RETRY}次）")
```

### 关键设计决策
1. **后台线程异步重试**：使用 `threading.Thread(daemon=True)` 在后台运行重试循环，不阻塞主线程的定时检查
2. **MAX_RETRY = 10**：10分钟重试窗口足够覆盖临时网络故障，且不会跨越下一个时段
3. **全局标志去重**：`_retrying` 标志防止同一时段启动多组重试，`finally` 确保标志总能重置
4. **daemon线程**：主进程退出时重试线程自动终止

## Commands
```bash
运行: python main.py
```

## Success Criteria
- 定时推送时爬取失败，每分钟自动重试
- 重试成功后自动推送商店信息
- 最多重试10次后放弃
- 同一时段不会并行多组重试
- 重试过程有日志输出
- 用户主动查询远行商人功能不受影响

## Boundaries
- Always: 保持现有用户查询功能不变
- Always: 重试逻辑仅影响定时推送路径
- Never: 不修改 scraper.py 或 formatter.py
