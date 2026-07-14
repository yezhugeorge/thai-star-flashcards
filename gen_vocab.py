#!/usr/bin/env python3
"""
饭泰 FANTHA - 词汇数据生成
从722句提取核心词汇，生成带释义/词性/例句的单词卡数据
"""
import re, json, subprocess, sys
from collections import defaultdict
from pythainlp.tokenize import word_tokenize

# ====== 加载词典 ======
# 从 gen_enriched.py 中提取 THAI_DICT
with open('gen_enriched.py', 'r') as f:
    content = f.read()
dict_start = content.index('THAI_DICT = {')
dict_end = content.index('\n}\n', dict_start) + 2
dict_code = content[dict_start:dict_end]
THAI_DICT = {}
exec(dict_code, THAI_DICT)
THAI_DICT = THAI_DICT['THAI_DICT']

# 加载补充词典
with open('extra_dict.py', 'r') as f:
    extra_content = f.read()
extra_ns = {}
exec(extra_content, extra_ns)
THAI_DICT.update(extra_ns.get('EXTRA_DICT', {}))

print(f"Dictionary loaded: {len(THAI_DICT)} words")

# ====== 停用词/虚词 ======
STOPWORDS = {
    ' ', '.', ',', '!', '?', 'ๆ', '~', '-', '–', '"', "'", '…', ':', ';',
    'และ', 'หรือ', 'แต่', 'ที่', 'ของ', 'ใน', 'บน', 'กับ', 'จาก',
    'ให้', 'เป็น', 'มี', 'ไม่', 'ก็', 'แล้ว', 'ยัง', 'กำลัง', 'จะ',
    'คือ', 'มาก', 'น้อย', 'ทุก', 'บาง', 'อีก', 'เลย', 'เท่านั้น', 'เกินไป',
    'ค่ะ', 'ครับ', 'คะ', 'นะ', 'น้า', 'เถอะ', 'ละ', 'สิ', 'เสีย',
    'จ้ะ', 'จ๊ะ', 'ฮะ', 'ว่ะ', 'แหละ', 'จริงๆ', 'มากๆ',
    'ผม', 'ฉัน', 'เรา', 'พวกเขา', 'เขา', 'คุณ', 'มัน', 'นั่น', 'โน้น',
    'อะไร', 'ใคร', 'เมื่อไหร่', 'ยังไง', 'เท่าไหร่', 'ไม่กี่', 'หลาย',
    'เพราะ', 'เนื่องจาก', 'ถ้า', 'หาก', 'เพื่อ', 'ต่อ', 'เมื่อ', 'ระหว่าง',
    'ก่อน', 'หลัง', 'ตอน', 'ช่วง', 'ข้าง', 'ตรง',
    'เอง', 'เอา', 'นี่',
    'หนึ่ง', 'สอง', 'สาม', 'สี่', 'ห้า', 'หก', 'เจ็ด', 'แปด', 'เก้า', 'สิบ',
    'ไหม', 'มั้ย', 'ไหน', 'กี่', 'อย่าง', 'เหมือน', 'เกือบ', 'คล้าย',
    'ขึ้น', 'ลง', 'เข้า', 'ออก', 'ไป', 'มา', 'อยู่',
    'กัน', 'ด้วย', 'เท่านั้น', 'เอง', 'นั้น',
    'แค่', 'เพียง', 'ช่วย', 'หน่อย', 'เถอะ', 'ดีกว่า',
    'ทำไม', 'อย่างไร',
}

# 词性标注（常见词的词性）
WORD_POS = {
    # 名词
    'คู่': 'n.', 'ฟีด': 'n.', 'ฉาก': 'n.', 'คอนเสิร์ต': 'n.', 'ตั๋ว': 'n.',
    'ที่นั่ง': 'n.', 'เพลง': 'n.', 'แฟนคลับ': 'n.', 'ไลฟ์': 'n.',
    'โพสต์': 'n.', 'คอมเมนต์': 'n.', 'เทรนด์': 'n.', 'วิดีโอ': 'n.',
    'ราคา': 'n.', 'สี': 'n.', 'ทางออก': 'n.', 'พวงมาลัย': 'n.',
    'หนัง': 'n.', 'เรื่อง': 'n.', 'ความรัก': 'n.', 'คนรัก': 'n.',
    'คนอื่น': 'n.', 'รูป': 'n.', 'ของขวัญ': 'n.', 'ป้าย': 'n.',
    'เซ็น': 'n.', 'ลายเซ็น': 'n.', 'เวที': 'n.', 'แสง': 'n.',
    'ไฟ': 'n.', 'ไฟฉาย': 'n.', 'เสียง': 'n.', 'ที่นี่': 'n.',
    'วัน': 'n.', 'เวลา': 'n.', 'เสื้อ': 'n.', 'สี': 'n.',
    'เพลง': 'n.', 'เนื้อเพลง': 'n.', 'ท่อน': 'n.', 'อัลบั้ม': 'n.',
    'มิวสิค': 'n.', 'วิดีโอ': 'n.', 'คลิป': 'n.', 'ภาพ': 'n.',
    'บัตร': 'n.', 'เบอร์': 'n.', 'ที่อยู่': 'n.', 'ชื่อ': 'n.',
    'เลข': 'n.', 'คิว': 'n.', 'แถว': 'n.', 'ห้อง': 'n.',
    'โรงแรม': 'n.', 'รถ': 'n.', 'ตำรวจ': 'n.', 'โรงพยาบาล': 'n.',
    'ร้าน': 'n.', 'อาหาร': 'n.', 'น้ำ': 'n.', 'เงิน': 'n.',
    'ราคา': 'n.', 'บัตร': 'n.', 'พาสปอร์ต': 'n.', 'วีซ่า': 'n.',
    'สนามบิน': 'n.', 'สถานี': 'n.', 'ถนน': 'n.', 'ทาง': 'n.',
    'ฝั่ง': 'n.', 'ด้าน': 'n.', 'จุด': 'n.', 'ป้าย': 'n.',
    'กำแพง': 'n.', 'ประตู': 'n.', 'หน้า': 'n.', 'หลัง': 'n.',
    'ข้าง': 'n.', 'กลาง': 'n.', 'ใต้': 'n.', 'บน': 'n.',
    'พี่': 'n.', 'น้อง': 'n.', 'เพื่อน': 'n.', 'แฟน': 'n.',
    'ดารา': 'n.', 'นักแสดง': 'n.', 'นักร้อง': 'n.', 'ไอดอล': 'n.',
    'ซุปตาร์': 'n.', 'ผู้จัดการ': 'n.', 'ทีม': 'n.', 'กลุ่ม': 'n.',
    'แบรนด์': 'n.', 'สินค้า': 'n.', 'โฆษณา': 'n.', 'แคมเปญ': 'n.',
    
    # 动词
    'ดู': 'v.', 'อยาก': 'v.', 'ร้องไห้': 'v.', 'จบ': 'v.',
    'ซื้อ': 'v.', 'ขอ': 'v.', 'ส่ง': 'v.', 'เซ็น': 'v.',
    'โหวต': 'v.', 'แชร์': 'v.', 'กด': 'v.', 'สั่ง': 'v.',
    'เขียน': 'v.', 'รอ': 'v.', 'ถึง': 'v.', 'รัก': 'v.',
    'สู้': 'v.', 'เก่ง': 'v.', 'ดูแล': 'v.', 'พบ': 'v.',
    'เจอ': 'v.', 'ได้ยิน': 'v.', 'ฟัง': 'v.', 'พูด': 'v.',
    'บอก': 'v.', 'เห็น': 'v.', 'รู้': 'v.', 'คิด': 'v.',
    'จำ': 'v.', 'ลืม': 'v.', 'เข้าใจ': 'v.', 'ชอบ': 'v.',
    'เลือก': 'v.', 'เปลี่ยน': 'v.', 'แลก': 'v.', 'คืน': 'v.',
    'เปิด': 'v.', 'ปิด': 'v.', 'ถ่าย': 'v.', 'บันทึก': 'v.',
    'อัปโหลด': 'v.', 'ดาวน์โหลด': 'v.', 'ติดตาม': 'v.', 'ปฏิเสธ': 'v.',
    'ยอม': 'v.', 'ตกลง': 'v.', 'ไปถึง': 'v.', 'เดินทาง': 'v.',
    'แตะ': 'v.', 'จับ': 'v.', 'หิ้ว': 'v.', 'ถือ': 'v.',
    
    # 形容词
    'น่ารัก': 'adj.', 'หวาน': 'adj.', 'สวย': 'adj.', 'หล่อ': 'adj.',
    'เท่': 'adj.', 'ไหว': 'adj.', 'ดีมาก': 'adj.', 'เก่ง': 'adj.',
    'สูง': 'adj.', 'ต่ำ': 'adj.', 'ใหม่': 'adj.', 'เก่า': 'adj.',
    'ร้อน': 'adj.', 'หนาว': 'adj.', 'อร่อย': 'adj.', 'อิ่ม': 'adj.',
    'หิว': 'adj.', 'เหนื่อย': 'adj.', 'ง่วง': 'adj.', 'ตื่นเต้น': 'adj.',
    'ดีใจ': 'adj.', 'เสียใจ': 'adj.', 'โกรธ': 'adj.', 'กลัว': 'adj.',
    'ตลก': 'adj.', 'เศร้า': 'adj.', 'มีความสุข': 'adj.',
    'คุ้มค่า': 'adj.', 'เร็ว': 'adj.', 'ช้า': 'adj.',
    'สด': 'adj.', 'ใหญ่': 'adj.', 'เล็ก': 'adj.',
    'ยาว': 'adj.', 'สั้น': 'adj.', 'หนา': 'adj.', 'บาง': 'adj.',
    'แพง': 'adj.', 'ถูก': 'adj.', 'ยาก': 'adj.', 'ง่าย': 'adj.',
    'เย็น': 'adj.', 'อุ่น': 'adj.', 'เด่น': 'adj.', 'พิเศษ': 'adj.',
    
    # 副词
    'ตลอด': 'adv.', 'จริง': 'adv.', 'จัง': 'adv.', 'เหมือน': 'adv.',
    'เกิน': 'adv.', 'พอดี': 'adv.', 'เสมอ': 'adv.', 'อีกครั้ง': 'adv.',
    'สุด': 'adv.', 'ที่สุด': 'adv.',
    
    # 短语
    'ขอบคุณ': 'phrase', 'สวัสดี': 'phrase', 'ไม่เป็นไร': 'phrase',
    'ขอโทษ': 'phrase', 'เสียใจ': 'phrase', 'ดีใจ': 'phrase',
}

# 读取原始句子
orig = subprocess.check_output(['git', 'show', '271f58b:js/data.js'], cwd='.').decode('utf-8')
sentences = []
for m in re.finditer(r"\{ id: '([^']+)', cat: '([^']+)', sub: '([^']+)', thai: '([^']+)', cn: '([^']+)' \}", orig):
    sentences.append({
        'id': m.group(1), 'cat': m.group(2), 'sub': m.group(3),
        'thai': m.group(4), 'cn': m.group(5)
    })

print(f"Sentences: {len(sentences)}")

# 按分类提取词汇
vocab_by_cat = defaultdict(lambda: defaultdict(list))
for s in sentences:
    words = word_tokenize(s['thai'], engine='newmm')
    for w in words:
        w = w.strip()
        if not w or len(w) < 2 or w in STOPWORDS:
            continue
        if re.match(r'^[\d\s\.\,\!\?\-]+$', w):
            continue
        vocab_by_cat[s['cat']][w].append(s['id'])

# 生成词汇数据
VOCAB = []
vocab_id_counter = 0

for cat in ['bl', 'gl', 'star', 'concert', 'social', 'offline']:
    cat_words = vocab_by_cat[cat]
    # 按出现频率排序，取前50个词
    sorted_words = sorted(cat_words.items(), key=lambda x: -len(x[1]))[:50]
    
    for w, sids in sorted_words:
        vocab_id_counter += 1
        vid = f"vocab-{cat}-{vocab_id_counter:03d}"
        
        # 从词典获取拼音和释义
        dict_entry = THAI_DICT.get(w, None)
        if dict_entry and len(dict_entry) >= 3:
            roman = dict_entry[0]
            zhuyin = dict_entry[1]
            meaning = dict_entry[2]
        else:
            roman = ''
            zhuyin = ''
            meaning = '（泰语词）'
        
        # 词性
        pos = WORD_POS.get(w, '')
        
        # 例句（取第一条包含该词的句子）
        example_thai = ''
        example_cn = ''
        for sid in sids:
            s = next((x for x in sentences if x['id'] == sid), None)
            if s:
                example_thai = s['thai']
                example_cn = s['cn']
                break
        
        VOCAB.append({
            'id': vid,
            'cat': cat,
            'word': w,
            'roman': roman,
            'zhuyin': zhuyin,
            'meaning': meaning,
            'pos': pos,
            'example_thai': example_thai,
            'example_cn': example_cn,
            'freq': len(sids),
        })

# 统计
print(f"\nTotal vocab entries: {len(VOCAB)}")
for cat in ['bl', 'gl', 'star', 'concert', 'social', 'offline']:
    cat_vocab = [v for v in VOCAB if v['cat'] == cat]
    has_meaning = sum(1 for v in cat_vocab if v['meaning'] != '（泰语词）')
    print(f"  {cat}: {len(cat_vocab)} words ({has_meaning} with meaning)")

# 写入词汇数据到 data_vocab.js（单独文件，然后在主data.js中引入）
output = "/* 饭泰 FANTHA - 词汇数据 */\n"
output += "window.APP_DATA = window.APP_DATA || {};\n"
output += "window.APP_DATA.VOCAB = [\n"
for v in VOCAB:
    def esc(s):
        return str(s).replace("'", "\\'").replace("\n", " ")
    output += f"  {{ id: '{esc(v['id'])}', cat: '{esc(v['cat'])}', word: '{esc(v['word'])}', roman: '{esc(v['roman'])}', zhuyin: '{esc(v['zhuyin'])}', meaning: '{esc(v['meaning'])}', pos: '{esc(v['pos'])}', ex_thai: '{esc(v['example_thai'])}', ex_cn: '{esc(v['example_cn'])}', freq: {v['freq']} }},\n"
output += "];\n"

with open('js/data_vocab.js', 'w') as f:
    f.write(output)

print(f"\n✅ 词汇数据写入 js/data_vocab.js ({len(VOCAB)} words)")

# 显示样本
print("\n=== 样本 ===")
for cat in ['bl', 'star', 'social']:
    cat_vocab = [v for v in VOCAB if v['cat'] == cat][:5]
    print(f"\n--- {cat} ---")
    for v in cat_vocab:
        print(f"  {v['word']} ({v['pos']}) → {v['meaning']}  | ex: {v['example_thai']}")
