import os


class LocalLLM:
    def __init__(self) -> None:
        self.endpoint = os.getenv("LOCALMEETINGAI_VLLM_ENDPOINT", "http://127.0.0.1:8001/v1/chat/completions")

    async def stream_opinion(self, prompt: str):
        summary = _local_reasoning(prompt)
        for sentence in summary.split("\n"):
            if sentence.strip():
                yield sentence.strip()


def _local_reasoning(prompt: str) -> str:
    return "\n".join(
        [
            "建议核对当前讨论与项目资料的一致性。",
            "若存在决策分歧，请先补齐约束、负责人、截止时间和验收标准。",
            "本地vLLM未配置时使用规则引擎输出；配置LOCALMEETINGAI_VLLM_ENDPOINT后可替换为模型流式推理。",
        ]
    )
