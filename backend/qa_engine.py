"""问答引擎 — 3步对话状态机"""
import json

STEPS = [
    {
        "key": "video_type",
        "question": "你想做什么类型的视频？",
        "options": ["产品营销", "金融科普", "政策解读", "企业文化"],
        "hint": "选择一个类型"
    },
    {
        "key": "topic",
        "question": "具体主题是什么？",
        "options": None,
        "hint": "例如：大额存单、反诈技巧、新农合缴费"
    },
    {
        "key": "style",
        "question": "你的身份和风格偏好是什么？",
        "options": ["柜员+亲切自然", "客户经理+专业可信", "大堂经理+活力热情"],
        "hint": "选择最适合你的风格"
    },
]


class QASession:
    def __init__(self):
        self.answers = {}
        self.step = 0

    def next_question(self):
        if self.step >= len(STEPS):
            return None
        s = STEPS[self.step]
        return {"step": self.step + 1, "total": len(STEPS), "key": s["key"], "question": s["question"], "options": s.get("options"), "hint": s.get("hint")}

    def answer(self, value):
        key = STEPS[self.step]["key"]
        self.answers[key] = value
        self.step += 1
        return self.next_question()

    def is_complete(self):
        return self.step >= len(STEPS)

    def build_prompt(self, templates):
        rules = {
            "合规要求": [
                "不承诺具体收益率", "不使用绝对化用语（最/第一/100%）",
                "风险提示必须标注", "禁止诱导分享话术",
                "金融产品需注明免责声明"
            ],
            "拍摄建议": [
                "人物着装整洁，佩戴工牌", "背景体现银行环境",
                "语速适中，表情自然", "时长控制在60-90秒"
            ]
        }

        matched_templates = []
        video_type = self.answers.get("video_type", "")
        for t in templates:
            if t.get("type") == video_type:
                matched_templates.append(t)

        prompt_parts = [
            f"## 角色",
            f"你是一位遵义农信的新媒体内容专家，擅长为基层员工创作抖音短视频脚本。",
            f"",
            f"## 任务",
            f"根据以下信息，生成一条60-90秒的抖音视频脚本（口播稿+分镜提示）。",
            f"",
            f"## 视频信息",
            f"- 类型：{self.answers.get('video_type', '')}",
            f"- 主题：{self.answers.get('topic', '')}",
            f"- 风格：{self.answers.get('style', '')}",
            f"",
        ]

        if matched_templates:
            prompt_parts.append("## 参考模板")
            for i, mt in enumerate(matched_templates[:2]):
                prompt_parts.append(f"### 模板{i+1}：{mt.get('title', '')}")
                prompt_parts.append(f"- 结构：{mt.get('script_structure', '')}")
                prompt_parts.append(f"- 分镜建议：{', '.join(mt.get('shot_tips', []))}")
                prompt_parts.append(f"- 样例开头：{mt.get('sample', '')[:100]}...")
                prompt_parts.append("")

        prompt_parts.extend([
            "## 合规要求（必须遵守）",
            *[f"- {r}" for r in rules["合规要求"]],
            "",
            "## 拍摄建议",
            *[f"- {r}" for r in rules["拍摄建议"]],
            "",
            "## 输出格式",
            "【脚本标题】一句话吸引人的标题",
            "【口播稿】完整的60-90秒口播文案，语言通俗易懂，适合银行基层员工自然表达",
            "【分镜提示】分3-5个镜头，每个镜头标注画面内容和时长",
            "【合规检查】标注本脚本符合的合规要点",
            "【热门标签】3-5个抖音热门标签",
        ])

        return "\n".join(prompt_parts)


SESSION_STORE = {}


def get_session(session_id):
    return SESSION_STORE.get(session_id)


def create_session():
    import uuid
    sid = uuid.uuid4().hex[:12]
    SESSION_STORE[sid] = QASession()
    return sid, SESSION_STORE[sid]
