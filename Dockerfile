# 行情大屏 + 弹幕服务，只用 Python 标准库，无任何第三方依赖
FROM python:3.12-alpine

LABEL org.opencontainers.image.title="market-screen" \
      org.opencontainers.image.description="纯前端行情大屏：A股/港股/美股指数实时行情，带流动弹幕和多套皮肤" \
      org.opencontainers.image.source="https://github.com/Suzzt/market-screen" \
      org.opencontainers.image.licenses="MIT"

# DM_API 控制弹幕联机模式，容器启动时注入到页面：
#   ""     同源联机（容器默认，多人弹幕可用）
#   null   关闭联机，只有本机 + 同浏览器其它标签页
#   http://host:port  指向另一台机器上的弹幕服务
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    MS_IN_DOCKER=1 \
    DM_API="" \
    PORT=8788

# /app 存放只读源码，/srv 是运行时目录（注入后的页面写在这里）
COPY index.html danmaku_server.py /app/
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh

RUN chmod +x /usr/local/bin/docker-entrypoint.sh \
 && adduser -D -H -u 10001 app \
 && mkdir -p /srv \
 && chown app /srv

WORKDIR /srv
USER app

# PORT 改了记得同步改端口映射，EXPOSE 只是声明
EXPOSE 8788

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget -qO- "http://127.0.0.1:${PORT}/danmaku?since=-1" >/dev/null || exit 1

ENTRYPOINT ["docker-entrypoint.sh"]
