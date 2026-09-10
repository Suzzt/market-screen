#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
弹幕服务 + 静态托管（零依赖，只用标准库）

    python3 danmaku_server.py            # 默认 8788 端口
    python3 danmaku_server.py 9000       # 指定端口

启动后：
    - 大屏页面      http://<本机IP>:8788/
    - 弹幕接口      GET  /danmaku?since=<cursor>   拉取新弹幕
                    POST /danmaku  {"text":"...","color":"#fff"}   发送

同事在同一局域网打开 http://<你的IP>:8788/ 即可一起发弹幕。
记得把 index.html 里的 DM_API 从 null 改成 ""（同源）。
"""
import json, os, sys, time, threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

ROOT      = os.path.dirname(os.path.abspath(__file__))
MAX_KEEP  = 500          # 内存里最多保留多少条
MAX_LEN   = 60           # 单条弹幕最大字数
RATE_N    = 5            # 每个 IP 每 RATE_SEC 秒最多发几条
RATE_SEC  = 10
ONLINE_TTL = 60          # 多久没请求就算离线

_lock    = threading.Lock()
_items   = []            # [{id, text, color, ts}]
_seq     = 0
_seen    = {}            # ip -> last_seen
_posts   = {}            # ip -> [ts, ...]


def _online() -> int:
    now = time.time()
    return sum(1 for t in _seen.values() if now - t < ONLINE_TTL)


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=ROOT, **kw)

    # ---------- 工具 ----------
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _json(self, obj, code=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self._cors()
        self.end_headers()
        self.wfile.write(body)

    def _touch(self):
        _seen[self.client_address[0]] = time.time()

    # ---------- 路由 ----------
    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self):
        if self.path.split("?")[0] != "/danmaku":
            return super().do_GET()          # 其余交给静态文件
        self._touch()
        try:
            q = self.path.split("?", 1)[1] if "?" in self.path else ""
            since = int(dict(p.split("=", 1) for p in q.split("&") if "=" in p).get("since", -1))
        except Exception:
            since = -1
        with _lock:
            cursor = _seq
            # since < 0 表示「我刚上线，只要之后的新弹幕」
            new = [] if since < 0 else [i for i in _items if i["id"] > since]
        self._json({"cursor": cursor, "list": new, "online": _online()})

    def do_POST(self):
        global _seq
        if self.path.split("?")[0] != "/danmaku":
            return self._json({"error": "not found"}, 404)
        self._touch()
        ip  = self.client_address[0]
        now = time.time()
        with _lock:
            hits = [t for t in _posts.get(ip, []) if now - t < RATE_SEC]
            if len(hits) >= RATE_N:
                return self._json({"error": "太快了，慢一点"}, 429)
            hits.append(now)
            _posts[ip] = hits
        try:
            n    = int(self.headers.get("Content-Length") or 0)
            data = json.loads(self.rfile.read(min(n, 4096)) or b"{}")
        except Exception:
            return self._json({"error": "bad json"}, 400)

        text = str(data.get("text", "")).strip()[:MAX_LEN]
        if not text:
            return self._json({"error": "empty"}, 400)
        color = str(data.get("color", "#ffffff"))
        if not (color.startswith("#") and 4 <= len(color) <= 9):
            color = "#ffffff"

        with _lock:
            _seq += 1
            item = {"id": _seq, "text": text, "color": color, "ts": int(now)}
            _items.append(item)
            del _items[:-MAX_KEEP]
        self._json({"ok": True, "id": item["id"]})

    def log_message(self, fmt, *args):
        if "/danmaku" not in (args[0] if args else ""):
            super().log_message(fmt, *args)


def _lan_ip() -> str:
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8788
    srv  = ThreadingHTTPServer(("0.0.0.0", port), Handler)

    if os.environ.get("MS_IN_DOCKER"):
        # 容器里打印容器内网 IP 没意义，宿主机地址取决于 -p 映射
        print(f"监听 0.0.0.0:{port}（宿主机地址取决于 docker run -p 的映射）")
        print("DM_API 已由 entrypoint 按环境变量注入，无需手改 index.html。")
    else:
        ip = _lan_ip()
        print(f"大屏   http://{ip}:{port}/")
        print(f"弹幕   http://{ip}:{port}/danmaku")
        print("提示：把 index.html 里的 DM_API 改成 \"\" 才会连上这个服务。")
    print("Ctrl+C 退出。")

    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nbye")


if __name__ == "__main__":
    main()
