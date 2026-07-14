#!/usr/bin/env python3
"""
活人泰语点读卡 - 激活码生成脚本
生成500个激活码，SHA-256哈希后输出到js/codes.js
明文列表输出到codes_list.txt供出售使用
"""

import hashlib
import random
import os

# 安全字符集：排除 0, O, I, 1, L 等易混淆字符
ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
CODE_COUNT = 500
SEGMENTS = 3
SEG_LEN = 4
PREFIX = "THAI"

def generate_code():
    """生成一个激活码，格式: THAI-XXXX-XXXX-XXXX"""
    segments = []
    for _ in range(SEGMENTS):
        seg = ''.join(random.choice(ALPHABET) for _ in range(SEG_LEN))
        segments.append(seg)
    return f"{PREFIX}-" + "-".join(segments)

def sha256_hash(code):
    """对激活码做SHA-256哈希，返回十六进制字符串"""
    return hashlib.sha256(code.encode('utf-8')).hexdigest()

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # 生成不重复的激活码
    codes = set()
    while len(codes) < CODE_COUNT:
        codes.add(generate_code())
    codes = sorted(codes)

    # 计算哈希
    hashes = [sha256_hash(code) for code in codes]

    # 输出 js/codes.js（哈希数组，会提交到GitHub）
    js_dir = os.path.join(script_dir, "js")
    os.makedirs(js_dir, exist_ok=True)
    js_path = os.path.join(js_dir, "codes.js")

    js_content = """/**
 * 活人泰语点读卡 - 激活码哈希表
 * 此文件只包含SHA-256哈希值，无法反推出原始激活码
 * 自动生成，请勿手动修改
 */
window.ACTIVATION_HASHES = [
"""
    for h in hashes:
        js_content += f'  "{h}",\n'
    js_content += "];\n"

    with open(js_path, 'w', encoding='utf-8') as f:
        f.write(js_content)
    print(f"[OK] 已生成 {len(hashes)} 个哈希 -> {js_path}")

    # 输出 codes_list.txt（明文激活码列表，供出售，不提交到GitHub）
    txt_path = os.path.join(script_dir, "codes_list.txt")
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write("=" * 50 + "\n")
        f.write("活人泰语点读卡 - 激活码列表\n")
        f.write(f"共 {len(codes)} 个激活码\n")
        f.write("每个激活码可在任意设备上使用\n")
        f.write("=" * 50 + "\n\n")
        for i, code in enumerate(codes, 1):
            f.write(f"{i:3d}. {code}\n")
    print(f"[OK] 已生成 {len(codes)} 个激活码 -> {txt_path}")
    print(f"\n注意：codes_list.txt 包含明文激活码，请勿提交到GitHub！")
    print(f"该文件已在 .gitignore 中排除。")

    # 显示前5个作为预览
    print(f"\n前5个激活码预览：")
    for i, code in enumerate(codes[:5], 1):
        print(f"  {i}. {code}  (hash: {hashes[i-1][:16]}...)")

if __name__ == "__main__":
    main()
