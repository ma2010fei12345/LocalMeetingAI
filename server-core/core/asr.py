import os
from dataclasses import dataclass


@dataclass
class TranscriptResult:
    text: str
    confidence: float


class WhisperTranscriber:
    def __init__(self) -> None:
        self._model = None
        self._buffer = bytearray()
        model_name = os.getenv("LOCALMEETINGAI_WHISPER_MODEL", "")
        if model_name:
            try:
                import whisper

                self._model = whisper.load_model(model_name)
            except Exception:
                self._model = None

    def transcribe_chunk(self, audio_bytes: bytes) -> TranscriptResult | None:
        self._buffer.extend(audio_bytes)
        if len(self._buffer) < 16000:
            return None
        payload = bytes(self._buffer)
        self._buffer.clear()
        if self._model:
            return TranscriptResult("已接入Whisper模型，请配置PCM/WAV解码后启用实时转写。", 0.75)
        seconds = max(1, len(payload) // 32000)
        return TranscriptResult(f"收到约 {seconds} 秒音频，离线ASR适配器待加载模型。", 0.2)
