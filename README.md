# 洛克王国远行商人QQ机器人

自动推送《洛克王国：世界》远行商人商店信息到QQ群。

## 功能

- 启动时自动推送当前商店信息
- 每个时段开始后10分钟自动推送新商店信息
- 支持 `#远行商人` 指令查询当前商店
- 支持 `@机器人 身高 体重` 指令预测精灵蛋可能孵化的精灵
- 支持 `#更新精灵数据` 指令手动更新精灵数据

## 安装

### 1. 安装依赖

```bash
uv sync
```

### 2. 安装 NapCat

参考 [NapCat 文档](https://napneko.github.io/) 安装并配置 NapCat。

确保开启以下服务（端口 3000）：
- HTTP 服务
- WebSocket 正向连接

### 3. 配置

```bash
# 复制配置示例
cp config.example.json config.json

# 编辑配置，填入目标群号
vim config.json
```

配置说明：
- `group_id`: 目标QQ群号
- `api_port`: NapCat HTTP API 端口（默认 3000）
- `shop_url`: 商店页面URL（一般不需要修改）

### 4. 启动

先启动 NapCat 并登录 QQ，然后启动机器人：

```bash
uv run main.py
```

## 使用

在群内 @机器人 发送：
- `远行商人` - 查询当前商店信息
- `身高 体重` - 预测精灵蛋可能孵化的精灵（如 `0.6 4`）
- `#更新精灵数据` - 手动更新精灵数据缓存

## 商店刷新时段

- 08:00-12:00
- 12:00-16:00
- 16:00-20:00
- 20:00-24:00

每日 0:00-8:00 无远行商人。

## 数据来源

精灵数据来源于 [洛克王国BWIKI](https://wiki.biligame.com/rocom/)，遵循 [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/deed.zh-hans) 协议。
