# 答案末尾符号显示修正测试报告

日期：2026-10-25（北京时间）。基于 283915a，缓存版本 frog-answer-punctuation-v17。

## 修改

仅对“显示答案”卡片中的英文展示文本去掉末尾标点、空白和符号。内部缩写、撇号和逗号保留；不修改词条/例句原文、DJ 音标、判分逻辑、录音键或 MP3 文件。

## 本次实际通过

- `tests/answer_punctuation.py`：桌面及手机模拟配置，验证 See you later! → See you later、How are you today? → How are you today、I'm fine, thank you. → I'm fine, thank you、The apple is red. → The apple is red。
- 连续标点、中文括号、符号结尾也被清除；单词内部撇号和句中逗号保留。
- 验证仅填英文答案即可判定正确，完成后的原例句保持原文。
- 验证每个对应 MP3 仍按原完整例句播放，DJ 音标及已存例句不变；测试中禁止访问浏览器语音合成。
- `tests/word_cloze.py`、`tests/word_spelling.py` 已执行并通过。
- 结构化结果见 `answer-punctuation-results.json`。

## 测试边界

手机为 Chromium 触屏、视口及旧版 Android UA/API 缺失模拟，未做真实手机硬件或 Safari 实机测试。

上一版本的仓库范围完整报告保存在 `warehouse-v16-test-report.md`；本次不将历史报告中的其他脚本算作重新执行。打包时再次逐文件校验提供的 610 个 MP3 与来源 SHA-256 完全一致。
