import hashlib


class SpeakerDiarizer:
    def identify(self, audio_bytes: bytes) -> str:
        if not audio_bytes:
            return "Speaker 1"
        bucket = hashlib.sha1(audio_bytes[:2048]).digest()[0] % 2
        return f"Speaker {bucket + 1}"
