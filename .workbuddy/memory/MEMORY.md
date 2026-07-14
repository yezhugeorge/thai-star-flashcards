# 泰国追星泰语点读卡 - 项目记忆

## 项目概述
- 独立的追星泰语学习应用，与"活人泰语点读卡"（生活版）分开
- GitHub: https://github.com/yezhugeorge/thai-star-flashcards
- 线上: https://yezhugeorge.github.io/thai-star-flashcards/
- 路径: /Users/angus/WorkBuddy/app 泰语追星/

## 数据结构
- CATEGORIES: 6大模块 (bl/gl/star/concert/social/offline)
- SUBCATS: 每模块6个子分类，共36个
- SENTENCES: 722句 { id, cat, sub, thai, cn }
- DIALOGUES: 48个对话 { id, cat, title, scene, turns: [{ s, t, c }] }

## 关键技术决策
- 激活码localStorage键名用 thai_star_ 前缀（与生活版区分）
- 对话音频ID: {dialogueId}-{turnIndex}（如 dlg-bl-01-0）
- 音频路径: audio/{id}.mp3 (女声), audio/male/{id}.mp3 (男声)
- 复用生活版的 codes.js（500个激活码哈希）
- TTS回退: 无MP3时自动用浏览器speechSynthesis (th-TH)

## 待完成
- 生成全部MP3音频文件（句子722×2 + 对话~336×2）
- ElevenLabs API Key: 212ead77df6967aa9766feb2f2541cf39eeac9f9ff02292b5a414a4b450c4255
- 女声Voice ID: qoykJB8jGk5wSDo1GaDJ
- 男声Voice ID: pNInz6obpgDQGcFmaJgB
- TTS模型: eleven_v3 + language_code=th
