#!/usr/bin/env python3
"""
饭泰 FANTHA - TTS测试脚本
用泰语原文（不是罗马音/谐音）调用ElevenLabs API生成测试音频
"""
import requests
import json
import os
import sys

API_KEY = "212ead77df6967aa9766feb2f2541cf39eeac9f9ff02292b5a414a4b450c4255"
FEMALE_VOICE = "DFze7nnumOAQKorhWJ7w"   # 女声
MALE_VOICE = "eUO4QTSsG1JL1xWAmC6l"     # 男声
MODEL = "eleven_v3"

# 测试样本 - thai字段才是发给TTS的文本
SAMPLES = [
    {"id": "bl-cp-001",       "thai": "พวกเขาน่ารักมาก",          "cn": "他们好可爱"},
    {"id": "gl-cp-001",       "thai": "พี่สาวเท่มาก",              "cn": "姐姐好飒"},
    {"id": "star-praise-001", "thai": "หล่อมาก",                   "cn": "好帅"},
    {"id": "concert-ticket-001", "thai": "ซื้อตั๋วออนไลน์ที่ไหน",  "cn": "网上在哪买票"},
    {"id": "social-twitter-001", "thai": "รีโพสต์ด้วยนะ",          "cn": "请转发"},
    {"id": "offline-pilgrim-001", "thai": "ที่นี่ถ่ายหนังเรื่องอะไร", "cn": "这里拍了什么剧"},
    {"id": "dlg-bl-01-0",     "thai": "สวัสดีค่ะ ดีใจมากที่ได้เจอ", "cn": "你好，很高兴见到你"},
]

# 音频保存目录
os.makedirs("audio", exist_ok=True)
os.makedirs("audio/male", exist_ok=True)

def generate_tts(text, voice_id, output_path, voice_name="女声"):
    """用ElevenLabs API生成泰语TTS"""
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "xi-api-key": API_KEY,
        "Content-Type": "application/json",
    }
    data = {
        "text": text,                    # ← 泰语原文
        "model_id": MODEL,
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75,
            "style": 0.0,
            "use_speaker_boost": True
        }
    }
    
    print(f"  [{voice_name}] 正在生成: {text}")
    print(f"    → 保存到: {output_path}")
    
    try:
        resp = requests.post(url, headers=headers, json=data, timeout=30)
        if resp.status_code == 200:
            with open(output_path, "wb") as f:
                f.write(resp.content)
            file_size = len(resp.content)
            print(f"    ✅ 成功 ({file_size} bytes)")
            return True
        else:
            print(f"    ❌ 失败: HTTP {resp.status_code}")
            print(f"    响应: {resp.text[:200]}")
            return False
    except Exception as e:
        print(f"    ❌ 错误: {e}")
        return False

print("=" * 60)
print("饭泰 FANTHA - TTS测试")
print(f"女声 Voice ID: {FEMALE_VOICE}")
print(f"男声 Voice ID: {MALE_VOICE}")
print(f"模型: {MODEL}")
print(f"语言: th (泰语)")
print("=" * 60)

success = 0
total = 0

# 生成女声 (全部7条)
print("\n🎤 女声测试 (7条):")
for s in SAMPLES:
    total += 1
    path = f"audio/{s['id']}.mp3"
    if generate_tts(s["thai"], FEMALE_VOICE, path, "女声"):
        success += 1

# 生成男声 (前5条句子，不含对话轮次因为是女声台词)
print("\n🎤 男声测试 (5条):")
for s in SAMPLES[:5]:
    total += 1
    path = f"audio/male/{s['id']}.mp3"
    if generate_tts(s["thai"], MALE_VOICE, path, "男声"):
        success += 1

print(f"\n{'=' * 60}")
print(f"完成: {success}/{total} 成功")
print(f"音频文件保存在: audio/ 和 audio/male/")
print(f"{'=' * 60}")

# 列出生成的文件
print("\n生成的文件:")
for root, dirs, files in os.walk("audio"):
    for f in sorted(files):
        if f.endswith(".mp3"):
            fpath = os.path.join(root, f)
            size = os.path.getsize(fpath)
            print(f"  {fpath} ({size} bytes)")
