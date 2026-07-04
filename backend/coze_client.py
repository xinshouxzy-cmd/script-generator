"""扣子编程客户端 — 调用遵农智创Bot"""
import os
import json
import uuid
import urllib.request

API_ENDPOINT = "https://npw7xpxtzy.coze.site/stream_run"
PROJECT_ID = "7658386835852247046"


def _get_token():
    if "COZE_PROJECT_TOKEN" in os.environ:
        return os.environ["COZE_PROJECT_TOKEN"]
    return ""


def _request(path_or_url, data=None):
    token = _get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(path_or_url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read().decode("utf-8")
            status = resp.getcode()
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        status = e.code
    except Exception as e:
        return None, 0, str(e)
    try:
        return json.loads(raw), status, raw
    except json.JSONDecodeError:
        return None, status, raw[:500]


def generate_script(prompt_text, user_id="staff_001"):
    if not _get_token():
        return {"success": False, "error": "API Token未配置，请在Render环境变量中设置COZE_PROJECT_TOKEN"}

    data = {
        "content": {
            "query": {
                "prompt": [
                    {"type": "text", "content": {"text": prompt_text}}
                ]
            }
        },
        "type": "query",
        "session_id": uuid.uuid4().hex[:16],
        "project_id": PROJECT_ID
    }

    try:
        resp, status, raw = _request(API_ENDPOINT, data=data)
        if status == 0:
            return {"success": False, "error": f"网络异常: {raw}", "raw": raw}
        if status != 200:
            return {"success": False, "error": f"HTTP {status}", "raw": raw[:500]}
        if resp is None:
            return {"success": False, "error": f"响应非JSON", "raw": raw[:500]}

        answer = resp.get("answer", "") or resp.get("content", "") or resp.get("data", {}).get("answer", "")
        if isinstance(answer, dict):
            answer = answer.get("text", str(answer))
        if not answer:
            return {"success": False, "error": "Bot未返回内容", "raw": json.dumps(resp, ensure_ascii=False)[:500]}

        return {"success": True, "script": str(answer)}
    except Exception as e:
        return {"success": False, "error": f"API异常: {str(e)}"}
