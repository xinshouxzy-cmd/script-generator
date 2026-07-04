"""扣子编程客户端 — 调用遵农智创Bot（SSE流式）"""
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


def generate_script(prompt_text, user_id="staff_001"):
    if not _get_token():
        return {"success": False, "error": "API Token未配置"}

    data = {
        "content": {
            "query": {
                "prompt": [{"type": "text", "content": {"text": prompt_text}}]
            }
        },
        "type": "query",
        "session_id": uuid.uuid4().hex[:16],
        "project_id": PROJECT_ID
    }

    try:
        token = _get_token()
        body = json.dumps(data).encode("utf-8")
        req = urllib.request.Request(API_ENDPOINT, data=body, headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "text/event-stream"
        }, method="POST")

        answer_parts = []
        with urllib.request.urlopen(req, timeout=120) as resp:
            for line_bytes in resp:
                line = line_bytes.decode("utf-8").strip()
                if not line or line.startswith(":"):
                    continue
                if line.startswith("data: "):
                    try:
                        event = json.loads(line[6:])
                        content = event.get("content", {})
                        ans = content.get("answer")
                        if ans and isinstance(ans, str):
                            answer_parts.append(ans)
                        if content.get("message_end"):
                            break
                    except json.JSONDecodeError:
                        continue
                elif line.startswith("event: "):
                    pass

        answer = "".join(answer_parts).strip()
        if answer:
            return {"success": True, "script": answer}
        return {"success": False, "error": "Bot未返回有效内容", "raw": f"Received {len(answer_parts)} SSE events"}
    except Exception as e:
        return {"success": False, "error": f"API异常: {str(e)}"}
