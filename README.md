# 全球指数实时行情大屏

[![构建镜像](https://github.com/Suzzt/market-screen/actions/workflows/docker.yml/badge.svg)](https://github.com/Suzzt/market-screen/actions/workflows/docker.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

单文件（`index.html`）的纯前端行情大屏，无需构建、无外部依赖、无 npm 包。
实时展示 A 股 / 港股 / 美股共 14 个主要指数，带**流动弹幕**和**5 套可切换皮肤**。

## 运行

**只看行情**：双击 `index.html` 即可（Chrome / Edge / Safari）。
若浏览器拦截了 `file://` 的跨域请求，改用本地服务：

```bash
python3 -m http.server 8777
```

**要多人一起发弹幕**：用配套的弹幕服务，它同时托管页面：

```bash
python3 danmaku_server.py
```

启动后终端会打印局域网地址，同事打开 `http://<你的IP>:8788/` 就能同屏发弹幕。
**注意**：联机前要把 `index.html` 里的 `DM_API` 从 `null` 改成 `""`（见下）。

**Docker 部署**：见下面的 [Docker](#docker) 一节，一条命令搞定，联机弹幕默认就开着。

## 功能

| 区域 | 说明 |
| --- | --- |
| 顶部 | 北京时间时钟、A股/港股/美股开闭市状态灯、刷新频率（3/5/10/30s）、轮播、弹幕、暂停、全屏、主题 |
| KPI 卡 | 上证 / 深证 / 创业板 / 科创50 四大核心指数，含迷你分时走势 |
| 左栏 | 全部 14 个指数，按市场分组，价格变动闪烁高亮，点击切换主图 |
| 中间 | **分时图**（价格线 + 昨收基准 + 成交量柱 + 十字光标）/ **日K**（60 日蜡烛 + MA5/MA10）；下方六项关键指标 |
| 右栏 | 涨跌幅横向排行、综合情绪指数、涨跌家数统计 |

- 休市时段若无分时数据（例如美股白天），主图**自动回退到日 K**。
- 刷新频率、选中指数、图表模式、轮播、主题、弹幕设置全部记忆在 `localStorage`。

## 弹幕

点顶部 `💬 弹幕` 或按 `D` 开关。开启后图表区出现输入栏，Enter 发送。三个来源：

1. **自己输入** —— 颜色可选，默认跟随当前主题。
2. **行情自动播报** —— 输入栏里的「播报开/关」控制。触发规则：
   - 指数翻红 / 翻绿（每指数最短间隔 60s）
   - 涨跌幅跨过 0.5% 档位（最短间隔 45s）
   - 刷新日内新高 / 新低（最短间隔 3 分钟）
   - 每 90 秒一条全场概览（涨跌家数 + 最强最弱）
3. **多人联机** —— 见下。

弹幕内容一律转义后再插入 DOM，不会被 HTML/脚本注入。

### 多人联机

改 `index.html` 里这一行：

```js
const DM_API = null;   // null = 关闭联机；"" = 同源；"http://192.168.1.20:8788" = 指向另一台机器
```

> 用 Docker 部署时不用手改，容器会按 `DM_API` 环境变量自动注入，默认就是同源联机。

| 值 | 效果 |
| --- | --- |
| `null`（默认） | 只有本机，外加**同一浏览器的其它标签页**（走 BroadcastChannel，零配置） |
| `""` | 同源。用 `danmaku_server.py` 托管页面时用这个 |
| `"http://IP:8788"` | 页面放在别处，弹幕服务单独部署 |

`danmaku_server.py` 只用 Python 标准库，内存存最近 500 条，单 IP 限速 10 秒 5 条，
接口：

```
GET  /danmaku?since=<cursor>   →  {cursor, list:[{id,text,color,ts}], online}
POST /danmaku  {"text":"...","color":"#fff"}
```

`since=-1` 表示「我刚上线，只要之后的新弹幕」，不会灌历史记录。

## Docker

镜像基于 `python:3.12-alpine`，只用 Python 标准库，无第三方依赖，约 83MB。
容器同时托管页面和弹幕接口，**联机弹幕默认开启**，不用改代码。

```bash
docker run -d --name market-screen -p 8788:8788 --restart unless-stopped \
  ghcr.io/suzzt/market-screen:latest
```

镜像由 GitHub Actions 自动构建推送，支持 `linux/amd64` 和 `linux/arm64`
（Apple Silicon、树莓派都能直接跑）。可用 tag：

| tag | 说明 |
| --- | --- |
| `latest` | main 分支最新 |
| `1.2.3` / `1.2` | 打 `v*` 标签时生成 |
| `sha-abc1234` | 按 commit 固定版本，生产环境建议用这个 |

也可以本地构建：

```bash
git clone https://github.com/Suzzt/market-screen.git
cd market-screen
docker build -t market-screen .
docker run -d --name market-screen -p 8788:8788 --restart unless-stopped market-screen
```

然后打开 `http://<宿主机IP>:8788/`。

或者用 compose：

```bash
docker compose up -d
```

### 环境变量

| 变量 | 默认 | 说明 |
| --- | --- | --- |
| `DM_API` | `""` | 弹幕联机模式。`""` 同源联机（推荐）；`null` / `off` 关闭联机；`http://host:port` 指向另一台机器的弹幕服务。容器启动时由 entrypoint 注入进页面，不用手改文件 |
| `PORT` | `8788` | 容器内监听端口，改了记得同步改 `-p` 映射 |

例：只要大屏、不要联机弹幕（弹幕仍可本机自己发）：

```bash
docker run -d -p 8788:8788 -e DM_API=null market-screen
```

例：换端口：

```bash
docker run -d -p 9000:9000 -e PORT=9000 market-screen
```

容器带 `HEALTHCHECK`，`docker ps` 能直接看到 `healthy`。

## 主题

点 `🎨 主题` 或按 `T` 循环切换，5 套：**深空蓝**（默认）、**曜石黑金**、**晨曦白**、**赛博霓虹**、**矩阵绿**。
主题通过 CSS 变量实现，Canvas 图表的网格、坐标、K 线、均线、十字光标颜色都会跟着换。

加一套自己的皮肤：在 `<style>` 里复制一段 `[data-theme="xxx"]{...}`，再往 JS 顶部的 `THEMES` 数组里加一项即可。

## 快捷键

| 键 | 作用 |
| --- | --- |
| `空格` | 暂停 / 继续刷新 |
| `↑` `↓` | 上下切换指数 |
| `K` | 分时 / 日K 切换 |
| `C` | 开关轮播 |
| `D` | 开关弹幕 |
| `/` | 开弹幕并聚焦输入框 |
| `T` | 切换主题 |
| `R` | 立即刷新 |
| `F` | 全屏 |

（焦点在输入框里时快捷键不生效，可以正常打字。）

## 数据源

腾讯财经公开行情接口（响应头带 `Access-Control-Allow-Origin: *`，可直接前端调用）：

| 用途 | 接口 |
| --- | --- |
| 实时快照（批量） | `https://qt.gtimg.cn/q=sh000001,hkHSI,...`（GBK，前端用 `TextDecoder('gbk')` 解码；失败时自动回退 script 标签注入） |
| 分时数据 | `https://web.ifzq.gtimg.cn/appstock/app/minute/query?code=sh000001` |
| 日 K 数据 | `https://web.ifzq.gtimg.cn/appstock/app/{fqkline\|hkfqkline\|usfqkline}/get?param=CODE,day,,,60,qfq` |

行情为延时数据（A 股通常延时若干秒，港美股延时更久），**仅供参考，不构成投资建议**。
接口为第三方非承诺服务，可能随时变更或限流。

## 自定义指数

编辑 `index.html` 顶部的 `INDICES` 数组：

```js
const INDICES = [
  { code:"sh000001", name:"上证指数", mk:"cn", kpi:1 },  // kpi:1 = 显示在顶部大卡
  { code:"bj899050", name:"北证50",   mk:"cn" },
  { code:"sh600519", name:"贵州茅台", mk:"cn" },        // 个股同样支持
  ...
];
```

`mk` 取值 `cn` / `hk` / `us`，决定交易时段、分时时间轴和成交额单位。

## 文件

```
market-screen/
├── index.html             大屏本体（单文件，含全部 CSS/JS）
├── danmaku_server.py      可选：弹幕服务 + 静态托管，零依赖
├── Dockerfile             容器镜像
├── docker-entrypoint.sh   启动时把 DM_API 注入页面
├── docker-compose.yml
├── .dockerignore
├── README.md
└── LICENSE                MIT
```

## 安全提示

`danmaku_server.py`（含 Docker 容器）监听 `0.0.0.0` 且**没有任何鉴权**，
能访问到端口的人都可以看页面、发弹幕。内网自用没问题，**不要直接暴露到公网**。

真要放到公网，至少做一层：

- 反向代理加 Basic Auth / OAuth（Nginx、Caddy、Cloudflare Access 都行）
- 或者只绑本机再走 SSH 隧道：`docker run -p 127.0.0.1:8788:8788 ...`

另外行情数据来自腾讯的公开接口，页面刷得越勤、开的人越多，被限流的概率越高，
公开部署建议把刷新频率调到 10s 以上。

## License

[MIT](LICENSE)
