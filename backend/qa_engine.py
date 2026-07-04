"""问答引擎 — 开放式引导，帮员工梳理创作思路"""
import json

STEPS = [
    {
        "key": "identity",
        "question": "先介绍一下你自己吧——你是做什么岗位的？怎么称呼？",
        "hint": "例如：我是大堂经理小王 / 我是柜员小李 / 我是客户经理老张"
    },
    {
        "key": "topic",
        "question": "你想拍什么主题的视频？有什么想跟大家聊的？",
        "hint": "例如：最近很多客户问大额存单怎么选 / 想提醒村里老人注意电信诈骗 / 今年惠农贷款政策有变化想告诉大家"
    },
    {
        "key": "scene",
        "question": "你打算在哪里拍？描述一下拍摄场景？",
        "hint": "例如：在我们网点大堂，背景能看到柜台和排队的人 / 在村里田间地头，想拍得接地气一点 / 就在工位上，简单拍一段"
    },
    {
        "key": "style",
        "question": "你希望这个视频给观众什么感觉？有什么特别想强调的？",
        "hint": "例如：希望大家觉得我专业可靠 / 想拍得亲切温暖一点 / 主要是想强调一下存钱安全的重要性"
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
        return {
            "step": self.step + 1,
            "total": len(STEPS),
            "key": s["key"],
            "question": s["question"],
            "hint": s.get("hint")
        }

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
                "不承诺具体收益率",
                "不使用绝对化用语（最/第一/100%/保证）",
                "金融产品必须附带风险提示",
                "不诱导分享、转发、点赞",
                "不攻击同行"
            ],
            "拍摄建议": [
                "着装整洁，佩戴工牌",
                "背景体现银行或工作环境",
                "语速适中，表情自然",
                "时长控制在60-90秒"
            ]
        }

        topic = self.answers.get("topic", "")
        matched_templates = []
        for t in templates:
            ttitle = t.get("title", "")
            tscene = t.get("scene", "")
            ttags = " ".join(t.get("hot_tags", []))
            if any(kw in topic for kw in ttags.split()):
                matched_templates.append(t)
        if not matched_templates:
            matched_templates = templates[:2]

        prompt_parts = [
            "## 角色",
            "你是遵义农信的 AI 创作助手，专门帮基层员工创作抖音短视频脚本。",
            "",
            "## 任务",
            "根据以下员工的真实想法，生成一条抖音视频脚本（口播稿+分镜提示）。",
            "脚本要自然、接地气，符合这位员工的身份和风格，不要机械套用模板。",
            "",
            "## 员工信息",
            f"- 身份：{self.answers.get('identity', '')}",
            f"- 主题：{self.answers.get('topic', '')}",
            f"- 拍摄场景：{self.answers.get('scene', '')}",
            f"- 风格要求：{self.answers.get('style', '')}",
            "",
        ]

        if matched_templates:
            prompt_parts.append("## 参考模板（仅供参考结构，不要照抄内容）")
            for i, mt in enumerate(matched_templates[:2]):
                prompt_parts.append(f"### 模板{i+1}：{mt.get('title', '')}")
                prompt_parts.append(f"- 结构参考：{mt.get('script_structure', '')}")
                prompt_parts.append(f"- 分镜参考：{', '.join(mt.get('shot_tips', []))}")
                prompt_parts.append("")

        prompt_parts.extend([
            "## 合规要求（务必遵守）",
            *[f"- {r}" for r in rules["合规要求"]],
            "",
            "## 拍摄建议",
            *[f"- {r}" for r in rules["拍摄建议"]],
            "",
            "## 输出格式（严格按此顺序）",
            "【脚本标题】一句吸引人的标题（10字内）",
            "【口播稿】完整口播文案，语言自然接地气，符合员工身份",
            "【分镜提示】3-5个镜头，每个标注画面内容和时长",
            "【合规检查】列出本脚本符合的合规要点",
            "【热门标签】3-5个#标签",
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
