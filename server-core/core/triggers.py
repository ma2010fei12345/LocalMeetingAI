DISAGREEMENT_WORDS = ("不同意", "不认可", "冲突", "分歧", "但是", "可是", "反对")
MISSING_INFO_WORDS = ("不确定", "待确认", "缺少", "没有数据", "不知道", "谁负责", "什么时候")
RISK_WORDS = ("风险", "延期", "超预算", "合规", "安全", "依赖", "阻塞")


def detect_triggers(text: str) -> list[str]:
    triggers: list[str] = []
    if any(word in text for word in DISAGREEMENT_WORDS):
        triggers.append("disagreement")
    if any(word in text for word in MISSING_INFO_WORDS):
        triggers.append("missing_info")
    if any(word in text for word in RISK_WORDS):
        triggers.append("risk")
    return triggers


def build_prompt(project_name: str, transcript: str, contexts: list[dict], trigger_type: str) -> str:
    context_text = "\n".join(f"- {item['filename']}: {item['text'][:500]}" for item in contexts) or "- 无命中文档"
    return f"""你是本地会议AI助手。
项目：{project_name}
触发类型：{trigger_type}
会议片段：{transcript}
项目资料：
{context_text}

请输出简短、可执行、带风险意识的实时观点。"""
