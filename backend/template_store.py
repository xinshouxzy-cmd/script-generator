"""模板库存储 — 本地JSON + GitHub持久化"""
import os
import json
import time

DATA_FILE = os.path.join(os.path.dirname(__file__), "data", "templates.json")


class TemplateStore:
    def __init__(self):
        self._ensure_file()

    def _ensure_file(self):
        os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
        if not os.path.exists(DATA_FILE):
            self._save({"templates": []})

    def _load(self):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save(self, data):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def get_all(self):
        return self._load().get("templates", [])

    def get_by_id(self, tid):
        for t in self.get_all():
            if t["id"] == tid:
                return t
        return None

    def add(self, template):
        data = self._load()
        template["id"] = template.get("id") or f"tpl_{int(time.time()*1000)}"
        template["created_at"] = template.get("created_at") or time.strftime("%Y-%m-%d")
        template["source"] = template.get("source", "manual")
        data["templates"].append(template)
        self._save(data)
        return template

    def update(self, tid, updates):
        data = self._load()
        for t in data["templates"]:
            if t["id"] == tid:
                t.update(updates)
                self._save(data)
                return t
        return None

    def delete(self, tid):
        data = self._load()
        before = len(data["templates"])
        data["templates"] = [t for t in data["templates"] if t["id"] != tid]
        if len(data["templates"]) < before:
            self._save(data)
            return True
        return False

    def refresh_from_github(self):
        """从GitHub拉取最新templates.json"""
        try:
            repo = os.environ.get("GITHUB_REPO", "xinshouxzy-cmd/script-generator")
            token = os.environ.get("GITHUB_PAT", "")
            if not token:
                return False
            import urllib.request
            url = f"https://api.github.com/repos/{repo}/contents/backend/data/templates.json"
            req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
            with urllib.request.urlopen(req) as resp:
                content = json.loads(resp.read()).get("content", "")
            import base64
            data = json.loads(base64.b64decode(content))
            self._save(data)
            return True
        except Exception as e:
            print(f"Refresh from GitHub failed: {e}")
            return False

    def push_to_github(self):
        """推送templates.json到GitHub"""
        try:
            repo = os.environ.get("GITHUB_REPO", "xinshouxzy-cmd/script-generator")
            token = os.environ.get("GITHUB_PAT", "")
            if not token:
                return False
            import urllib.request
            import base64

            data = self._load()
            content = json.dumps(data, ensure_ascii=False, indent=2)
            encoded = base64.b64encode(content.encode()).decode()

            url = f"https://api.github.com/repos/{repo}/contents/backend/data/templates.json"
            req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
            sha = ""
            try:
                with urllib.request.urlopen(req) as resp:
                    sha = json.loads(resp.read()).get("sha", "")
            except:
                pass

            body = json.dumps({"message": "更新模板库", "content": encoded, "sha": sha}).encode()
            req2 = urllib.request.Request(url, data=body, headers={
                "Authorization": f"Bearer {token}", "Content-Type": "application/json"
            }, method="PUT")
            with urllib.request.urlopen(req2) as resp:
                pass
            return True
        except Exception as e:
            print(f"Push to GitHub failed: {e}")
            return False


store = TemplateStore()
