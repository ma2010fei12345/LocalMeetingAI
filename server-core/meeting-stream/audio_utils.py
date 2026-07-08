import pyaudio
import wave
import os
from cryptography.fernet import Fernet

# 本地密钥，仅本机加密文件，不联网传输
def get_or_create_aes_key():
    key_path = "./local-data/key.key"
    os.makedirs("./local-data", exist_ok=True)
    if os.path.exists(key_path):
        with open(key_path, "rb") as f:
            return f.read()
    key = Fernet.generate_key()
    with open(key_path, "wb") as f:
        f.write(key)
    return key

# 音频文件加密保存
def encrypt_save_audio(raw_audio_data: bytes, save_path: str):
    key = get_or_create_aes_key()
    fernet = Fernet(key)
    encrypt_data = fernet.encrypt(raw_audio_data)
    with open(save_path, "wb") as f:
        f.write(encrypt_data)

# 基础音频参数配置（本地录音）
AUDIO_FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 1024