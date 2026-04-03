from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from pathlib import Path
from urllib import error, request

from fx_multi_factor.common.config import load_settings


@dataclass(slots=True)
class FeishuBotConfig:
    webhook_url: str
    secret: str | None = None


class FeishuWebhookError(RuntimeError):
    """Raised when Feishu webhook delivery fails."""


def load_feishu_bot_config(project_root: Path | None = None) -> FeishuBotConfig:
    settings = load_settings(project_root=project_root)
    webhook_url = getattr(settings, "feishu_webhook_url", None)
    webhook_secret = getattr(settings, "feishu_webhook_secret", None)
    if not webhook_url:
        raise RuntimeError(
            "未配置 FXMF_FEISHU_WEBHOOK_URL。请先在环境变量或 .env 中填写飞书群机器人的 webhook。"
        )
    return FeishuBotConfig(
        webhook_url=webhook_url,
        secret=webhook_secret,
    )


def _build_signature(secret: str) -> dict[str, str]:
    timestamp = str(int(time.time()))
    string_to_sign = f"{timestamp}\n{secret}".encode("utf-8")
    sign = base64.b64encode(hmac.new(string_to_sign, digestmod=hashlib.sha256).digest()).decode("utf-8")
    return {
        "timestamp": timestamp,
        "sign": sign,
    }


def send_feishu_text_message(
    message: str,
    title: str | None = None,
    project_root: Path | None = None,
    timeout_seconds: float = 10.0,
) -> dict[str, object]:
    text = message.strip()
    if not text:
        raise ValueError("发送到飞书的消息不能为空")

    config = load_feishu_bot_config(project_root=project_root)
    rendered_text = f"[{title.strip()}]\n{text}" if title and title.strip() else text
    payload: dict[str, object] = {
        "msg_type": "text",
        "content": {
            "text": rendered_text,
        },
    }
    if config.secret:
        payload.update(_build_signature(config.secret))

    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    http_request = request.Request(
        url=config.webhook_url,
        data=body,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )

    try:
        with request.urlopen(http_request, timeout=timeout_seconds) as response:
            response_text = response.read().decode("utf-8")
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise FeishuWebhookError(f"飞书 webhook 返回 HTTP {exc.code}: {detail}") from exc
    except error.URLError as exc:
        raise FeishuWebhookError(f"无法连接飞书 webhook: {exc.reason}") from exc

    try:
        response_payload = json.loads(response_text)
    except json.JSONDecodeError as exc:
        raise FeishuWebhookError(f"飞书 webhook 返回了非 JSON 响应: {response_text}") from exc

    if response_payload.get("code", 0) != 0:
        raise FeishuWebhookError(f"飞书 webhook 调用失败: {response_payload}")

    return {
        "status": "sent",
        "title": title.strip() if title else None,
        "message": rendered_text,
        "response": response_payload,
    }
