#!/usr/bin/env python3
"""
饭泰 FANTHA - 全量 TTS 音频生成
- 女声: DFze7nnumOAQKorhWJ7w (原文本)
- 男声: eUO4QTSsG1JL1xWAmC6l (ค่ะ→ครับ 转换)
- 模型: eleven_v3, language_code=th
"""

import re, os, sys, time, json, concurrent.futures, requests
from pathlib import Path

API_KEY = "212ead77df6967aa9766feb2f2541cf39eeac9f9ff02292b5a414a4b450c4255"
FEMALE_VOICE = "DFze7nnumOAQKorhWJ7w"
MALE_VOICE = "eUO4QTSsG1JL1xWAmC6l"
MODEL = "eleven_v3"
URL_TMPL = "https://api.elevenlabs.io/v1/text-to-speech/{voice}"

BASE_DIR = Path(__file__).parent
AUDIO_DIR = BASE_DIR / "audio"
MALE_DIR = BASE_DIR / "audio" / "male"

# ===== 泰语女→男句尾词转换 =====
def to_male_text(text):
    """将女性礼貌用语转为男性"""
    t = text
    # นะคะ → นะครับ
    t = t.replace('นะคะ', 'นะครับ')
    # ค่ะ → ครับ (句尾陈述)
    t = t.replace('ค่ะ', 'ครับ')
    # คะ → ครับ (句尾疑问, 但不影响其他含คะ的词)
    # 只替换句尾的 คะ（后面是空格、标点或结尾）
    t = re.sub(r'คะ(?=[\s,。.!？?]|$)', 'ครับ', t)
    return t

# ===== 解析 data.js =====
def parse_data_js():
    with open(BASE_DIR / "js" / "data.js", "r", encoding="utf-8") as f:
        content = f.read()

    items = []  # (id, thai_text)

    # --- 句子 ---
    # 精确匹配每个 sentence 对象: { id: 'xxx', ... thai: 'xxx', ... }
    sent_pattern = r"\{\s*id:\s*'([^']+)',\s*cat:\s*'[^']*',\s*sub:\s*'[^']*',\s*thai:\s*'((?:[^'\\]|\\.)*)'"
    for m in re.finditer(sent_pattern, content):
        sent_id = m.group(1)
        thai = m.group(2).replace("\\'", "'").replace('\\"', '"')
        items.append((sent_id, thai))

    # --- 对话 ---
    # 匹配每个 dialogue 对象: { id: 'dlg-xxx', ..., turns: [{ s:'...', t:'xxx', ... }, ...] }
    dlg_pattern = r"id:\s*'(dlg-[^']+)'[\s\S]*?turns:\s*\[([\s\S]*?)\]\s*\}"
    for m in re.finditer(dlg_pattern, content):
        dlg_id = m.group(1)
        turns_block = m.group(2)
        # 匹配每个 turn: { s:'...', t:'xxx', ... }
        turn_pattern = r"\{\s*s:'[^']*',\s*t:'((?:[^'\\]|\\.)*)'"
        for i, tm in enumerate(re.finditer(turn_pattern, turns_block)):
            thai = tm.group(1).replace("\\'", "'").replace('\\"', '"')
            items.append((f"{dlg_id}-{i}", thai))

    return items

# ===== 解析 data_vocab.js =====
def parse_vocab_js():
    with open(BASE_DIR / "js" / "data_vocab.js", "r", encoding="utf-8") as f:
        content = f.read()

    items = []
    # { id: 'vocab-xxx', ..., word: 'xxx', ... }
    vocab_pattern = r"id:\s*'(vocab-[^']+)'[\s\S]*?word:\s*'((?:[^'\\]|\\.)*)'"
    for m in re.finditer(vocab_pattern, content):
        vid = m.group(1)
        word = m.group(2).replace("\\'", "'").replace('\\"', '"')
        items.append((vid, word))

    return items

# ===== TTS 请求 =====
def tts(text, voice, output_path, retries=3):
    """调用 ElevenLabs TTS API"""
    for attempt in range(retries):
        try:
            resp = requests.post(
                URL_TMPL.format(voice=voice),
                headers={
                    "xi-api-key": API_KEY,
                    "Content-Type": "application/json",
                },
                json={
                    "text": text,
                    "model_id": MODEL,
                    "voice_settings": {
                        "stability": 0.5,
                        "similarity_boost": 0.75,
                        "style": 0.0,
                        "use_speaker_boost": True
                    },
                    "language_code": "th"
                },
                timeout=30
            )
            if resp.status_code == 200:
                with open(output_path, "wb") as f:
                    f.write(resp.content)
                return True
            elif resp.status_code == 422:
                print(f"  [422] {output_path.name}: {resp.text[:100]}")
                return False
            elif resp.status_code == 429:
                wait = min(10 * (attempt + 1), 30)
                print(f"  [429] Rate limited, waiting {wait}s...")
                time.sleep(wait)
                continue
            else:
                print(f"  [{resp.status_code}] {output_path.name}: {resp.text[:100]}")
                if attempt < retries - 1:
                    time.sleep(3)
        except Exception as e:
            print(f"  [ERR] {output_path.name}: {e}")
            if attempt < retries - 1:
                time.sleep(3)
    return False

# ===== 主流程 =====
def main():
    print("=" * 60)
    print("饭泰 FANTHA - 全量 TTS 音频生成")
    print("=" * 60)

    # 解析数据
    sentence_items = parse_data_js()
    vocab_items = parse_vocab_js()
    all_items = sentence_items + vocab_items

    print(f"句子+对话: {len(sentence_items)}")
    print(f"单词: {len(vocab_items)}")
    print(f"总计: {len(all_items)} 条 → {len(all_items) * 2} 个 MP3")

    # 确保目录存在
    AUDIO_DIR.mkdir(exist_ok=True)
    MALE_DIR.mkdir(exist_ok=True)

    # 收集需要生成的任务
    tasks = []  # (id, text, voice, output_path)

    for item_id, thai_text in all_items:
        # 女声（原文本）
        female_path = AUDIO_DIR / f"{item_id}.mp3"
        if not female_path.exists() or female_path.stat().st_size < 500:
            tasks.append((item_id, thai_text, FEMALE_VOICE, female_path, "F"))

        # 男声（转换文本）
        male_text = to_male_text(thai_text)
        male_path = MALE_DIR / f"{item_id}.mp3"
        if not male_path.exists() or male_path.stat().st_size < 500:
            tasks.append((item_id, male_text, MALE_VOICE, male_path, "M"))

    print(f"\n需要生成: {len(tasks)} 个文件")
    print(f"已存在: {len(all_items) * 2 - len(tasks)} 个文件")

    if not tasks:
        print("所有音频文件已存在，无需生成！")
        return

    # 并发生成（3并发，避免限流）
    success = 0
    failed = 0
    start_time = time.time()

    def process_task(task):
        item_id, text, voice, path, gender = task
        ok = tts(text, voice, path)
        return (item_id, gender, ok)

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(process_task, t): t for t in tasks}

        for i, future in enumerate(concurrent.futures.as_completed(futures), 1):
            item_id, gender, ok = future.result()
            if ok:
                success += 1
            else:
                failed += 1

            elapsed = time.time() - start_time
            rate = i / elapsed if elapsed > 0 else 0
            eta = (len(tasks) - i) / rate if rate > 0 else 0

            if i % 20 == 0 or i == len(tasks):
                print(f"  进度: {i}/{len(tasks)} | 成功: {success} | 失败: {failed} | "
                      f"速度: {rate:.1f}/s | 预计剩余: {eta:.0f}s")

    elapsed = time.time() - start_time
    print(f"\n{'=' * 60}")
    print(f"完成！耗时: {elapsed:.0f}s ({elapsed/60:.1f}分钟)")
    print(f"成功: {success} | 失败: {failed} | 总计: {len(tasks)}")

    if failed > 0:
        print(f"\n失败的文件可以重新运行此脚本自动补齐")

if __name__ == "__main__":
    main()
