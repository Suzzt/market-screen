#!/bin/sh
# 把 DM_API 环境变量注入到 index.html，然后启动弹幕服务。
# 这样使用者不用改代码，docker run -e DM_API=... 就能切换联机模式。
set -eu

PORT="${PORT:-8788}"
: "${DM_API=}"          # 未设置时按空串处理，也就是同源联机

cp /app/danmaku_server.py /srv/danmaku_server.py

python3 - <<'PY'
import json, os, re, sys

val = os.environ.get("DM_API", "")
lit = "null" if val.strip().lower() in ("null", "none", "off") else json.dumps(val)

src = open("/app/index.html", encoding="utf-8").read()
out, n = re.subn(r"^const DM_API\s*=[^;]*;$",
                 "const DM_API   = %s;" % lit,
                 src, count=1, flags=re.M)
if n != 1:
    sys.exit("[entrypoint] 在 index.html 里没找到 DM_API 声明，镜像和源码不匹配")

with open("/srv/index.html", "w", encoding="utf-8") as f:
    f.write(out)
print("[entrypoint] DM_API = %s" % lit)
PY

exec python3 /srv/danmaku_server.py "$PORT"
