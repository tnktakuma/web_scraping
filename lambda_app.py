import base64
import datetime
import hashlib
import hmac
import json
import os
from typing import Callable, Dict, List
from urllib.parse import parse_qs
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import boto3

import shinagawa_api
import tokyo_api


LINE_REPLY_URL = "https://api.line.me/v2/bot/message/reply"
LINE_PUSH_URL = "https://api.line.me/v2/bot/message/push"

COMMANDS: Dict[str, Dict[str, Callable]] = {
    "/badminton": {
        "name": "badminton",
        "label": "バドミントン",
        "main": shinagawa_api.main,
    },
    "/tennis": {
        "name": "tennis",
        "label": "テニス",
        "main": tokyo_api.main,
    },
}


def _json_response(body: Dict, status_code: int = 200) -> Dict:
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json; charset=utf-8"},
        "body": json.dumps(body, ensure_ascii=False),
    }


def format_results_for_line(title: str, results: Dict[str, List[str]]) -> str:
    today = datetime.datetime.now() + datetime.timedelta(hours=9)
    lines = [today.strftime(f"%Y年%m月%d日(%a) {title}の空き情報")]

    if not results:
        lines.append("空きは見つかりませんでした。")
        return "\n".join(lines)

    for location, slots in results.items():
        lines.append(f"\n[{location}]")
        lines.extend(f"- {slot}" for slot in slots)

    return "\n".join(lines)[:4900]


def _line_headers() -> Dict[str, str]:
    access_token = os.getenv("LINE_ACCESS_TOKEN")
    if not access_token:
        raise RuntimeError("LINE_ACCESS_TOKEN is not set")
    return {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }


def _post_line_api(url: str, payload: Dict):
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = Request(url, data=data, headers=_line_headers(), method="POST")
    try:
        with urlopen(request, timeout=10) as response:
            response.read()
    except HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"LINE API error {e.code}: {body}") from e


def reply_line_message(reply_token: str, text: str):
    _post_line_api(
        LINE_REPLY_URL,
        {
            "replyToken": reply_token,
            "messages": [{"type": "text", "text": text[:4900]}],
        },
    )


def push_line_message(to: str, text: str):
    _post_line_api(
        LINE_PUSH_URL,
        {
            "to": to,
            "messages": [{"type": "text", "text": text[:4900]}],
        },
    )


def _line_target_id(source: Dict) -> str:
    for key in ("userId", "groupId", "roomId"):
        value = source.get(key)
        if value:
            return value
    raise ValueError("LINE event source has no target id")


def _function_url_body_bytes(event: Dict) -> bytes:
    body = event.get("body") or "{}"
    if event.get("isBase64Encoded"):
        return base64.b64decode(body)
    return body.encode("utf-8")


def _parse_function_url_body(event: Dict) -> Dict:
    return json.loads(_function_url_body_bytes(event).decode("utf-8"))


def _header_value(event: Dict, name: str) -> str:
    headers = event.get("headers") or {}
    target = name.lower()
    for key, value in headers.items():
        if key.lower() == target:
            return value or ""
    return ""


def _verify_line_signature(event: Dict) -> bool:
    channel_secret = os.getenv("LINE_CHANNEL_SECRET")
    if not channel_secret:
        raise RuntimeError("LINE_CHANNEL_SECRET is not set")

    signature = _header_value(event, "x-line-signature")
    if not signature:
        return False

    digest = hmac.new(
        channel_secret.encode("utf-8"),
        _function_url_body_bytes(event),
        hashlib.sha256,
    ).digest()
    expected_signature = base64.b64encode(digest).decode("utf-8")
    return hmac.compare_digest(signature, expected_signature)


def _invoke_async(command_name: str, to: str):
    function_name = os.getenv("AWS_LAMBDA_FUNCTION_NAME", "shinagawa-api")
    boto3.client("lambda").invoke(
        FunctionName=function_name,
        InvocationType="Event",
        Payload=json.dumps({"lineAsync": command_name, "to": to}).encode("utf-8"),
    )


def handle_line_webhook(event: Dict) -> Dict:
    if not _verify_line_signature(event):
        return _json_response({"error": "invalid signature"}, status_code=403)

    payload = _parse_function_url_body(event)

    for line_event in payload.get("events", []):
        if line_event.get("type") != "message":
            continue

        message = line_event.get("message") or {}
        if message.get("type") != "text":
            continue

        command = (message.get("text") or "").strip()
        config = COMMANDS.get(command)
        if not config:
            continue

        reply_token = line_event.get("replyToken")
        target_id = _line_target_id(line_event.get("source") or {})
        label = config["label"]
        if reply_token:
            reply_line_message(
                reply_token,
                f"{label}の空き情報を検索しています。完了したら結果を送ります。",
            )
        _invoke_async(config["name"], target_id)

    return _json_response({"ok": True})


def handle_line_async(event: Dict) -> Dict:
    command_name = event.get("lineAsync")
    config = next(
        (item for item in COMMANDS.values() if item["name"] == command_name),
        None,
    )
    if not config:
        raise ValueError(f"unknown async event: {command_name}")

    results = config["main"]()
    push_line_message(
        event["to"],
        format_results_for_line(str(config["label"]), results),
    )
    return {"ok": True}


def _is_function_url_event(event: Dict) -> bool:
    return "requestContext" in event


def _command_from_query(event: Dict) -> str:
    params = event.get("queryStringParameters") or {}
    raw_params = parse_qs(event.get("rawQueryString") or "")
    command = (
        params.get("command")
        or params.get("q")
        or (raw_params.get("command") or [None])[0]
        or (raw_params.get("q") or [None])[0]
        or "badminton"
    ).strip()
    if not command.startswith("/"):
        command = f"/{command}"
    return command


def handle_direct_request(event: Dict) -> Dict:
    command = _command_from_query(event)
    config = COMMANDS.get(command)
    if not config:
        return _json_response(
            {"error": "unknown command", "commands": sorted(COMMANDS.keys())},
            status_code=400,
        )

    results = config["main"]()
    return _json_response(results)


def lambda_handler(event, context):
    if event.get("lineAsync"):
        return handle_line_async(event)

    if _is_function_url_event(event):
        method = event.get("requestContext", {}).get("http", {}).get("method")
        if method == "POST":
            return handle_line_webhook(event)
        if method == "GET":
            return handle_direct_request(event)

    results = shinagawa_api.main()
    return _json_response(results)
