"""扣子API客户端 — 调用脚本生成Bot"""
import os
import json
import urllib.request
import urllib.parse

COZE_BASE = "https://api.coze.cn"
BOT_ID = os.environ.get("COZE_SCRIPT_BOT_ID", "")


def _get_token():
    if "COZE_PAT" in os.environ:
        return os.environ["COZE_PAT"]
    return ""


def _request(method, path, data=None):
    token = _get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    url = COZE_BASE + path
    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def generate_script(prompt_text, bot_id=None, user_id="staff_001"):
    bot = bot_id or BOT_ID
    if not bot:
        return {"success": False, "error": "Bot ID未配置，请在扣子平台创建脚本生成Bot后设置环境变量COZE_SCRIPT_BOT_ID"}

    data = {
        "bot_id": bot,
        "user_id": user_id,
        "additional_messages": [
            {"role": "user", "content": prompt_text, "content_type": "text"}
        ],
        "stream": False,
        "auto_save_history": True
    }

    try:
        resp = _request("POST", "/v3/chat", data=data)
        if resp.get("code") != 0:
            return {"success": False, "error": resp.get("msg", "API调用失败")}

        messages = resp.get("data", {}).get("messages", [])
        assistant_msg = ""
        for msg in messages:
            if msg.get("role") == "assistant":
                assistant_msg = msg.get("content", "")
                break

        if not assistant_msg:
            return {"success": False, "error": "Bot未返回有效内容"}

        return {"success": True, "script": assistant_msg}
    except Exception as e:
        return {"success": False, "error": f"API异常: {str(e)}"}
