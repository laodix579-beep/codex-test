# MP3 录音接入测试报告

测试日期：2026-10-25（北京时间）。以现有应用 2615230 为基线接入所提供录音包。测试工具为 Python Playwright + Chromium，手机使用视口、触屏及 Android/iPhone UA/缺少新 API 的模拟配置。

## 已通过的检查

| 检查 | 实际结果 |
| --- | --- |
| 提供的 MP3 文件完整性 | 610/610 文件与输入包 SHA-256 完全一致；未生成、替换、转码或再次处理音频 |
| 全量浏览器解码 | 610/610 可解码，时长有效并存在非静音样本 |
| 现有词库映射 | 136/136 CSV 映射指向实际提供文件；正式词条顺序和稳定 ID 保留 |
| 指定测试词 | apple、book、orange、Please 在桌面和手机模拟配置均可搜索并播放独立词 MP3 |
| 旧词及例句 | 10 个旧词和 10 个对应例句按 UI 播放；核对实际 URL、录音文本和播放时间前进。具体文本见下文及 JSON 结果 |
| 搜索行为 | 大小写不敏感、部分英文、中文、例句、Enter、可见按钮、清空及无结果提示通过 |
| DJ/GA 分离 | 结果显示 DJ 英式音标，播放按文本键选择提供的 GA MP3，不将 IPA 传给播放器 |
| 无 TTS | 以抛错 getter 禁止访问 speechSynthesis 和 SpeechSynthesisUtterance，完整集成检查通过；缺失 MP3 明确提示，不生成替代声音 |
| GitHub Pages 子路径 | 静态服务器 /codex-test/ 子路径运行；捕获请求无越出项目根路径的资源 URL |
| 离线及 Range 请求 | 桌面/手机模拟配置均能离线重开、搜索及播放；MP3 bytes=0-127 返回 206 和 128 字节 |
| 用户记录保留 | 已有词条、自定义词、课程及导入课程、单词/句子进度、笔记、收藏、课程收藏、计划、设置、日期学习记录及对话状态核对通过 |
| 独立试听词 | apple、book 不写入正式词库；orange、please 复用原词条。搜索不改变词条数和课程顺序 |
| 原配置 | supabase-config.js 与基线字节完全相同，未要求提供 API Key |
| 完整部署 ZIP | 已实际解压检查 610 个 MP3 与来源哈希一致；在 /preview/project/ 子路径用主入口和中文兼容入口搜索、播放成功 |
| 单文件个人备份 | word_catalog 回归验证导出 HTML 包含现有 MP3 原始字节，可在无原仓库资源的独立目录播放，保留学习数据 |

12 个回归脚本均已实际执行并通过：

```
python3 tests/mobile_practice.py
python3 tests/space_shortcuts.py
python3 tests/word_catalog.py
python3 tests/word_spelling.py
python3 tests/word_entry.py
python3 tests/word_cloze.py
python3 tests/speech_reference.py
python3 tests/pep_pronunciation.py
python3 tests/navigation_audio.py
python3 tests/mobile_startup.py
python3 tests/sentence_word_audio.py
python3 tests/recording_integration.py
```

## 具体播放样本

旧词：hello、hi、good morning、good afternoon、good evening、good night、goodbye、bye、see you、see you later。

例句：

- Hello, Anna.
- Hi, Tom!
- Good morning, Mom.
- Good afternoon, Mr. Lee.
- Good evening, Dad.
- Good night, Mom.
- Goodbye, everyone.
- Bye! See you tomorrow.
- See you tomorrow.
- See you later!


## 来源与测试边界

- 609 段旧 MP3 由录音包提供者从原项目提取并统一响度；本次只核验并接入这些已有文件。
- apple.mp3 是包内已存在的本地 eSpeak 临时美式测试录音，音色可能不同；界面与文档均有标注。本次未调用 eSpeak 或其他 TTS。
- 包内旧音素/语调 JSON 属于历史元数据；本次未生成新语音，也不将旧声学测量当作当前文件的新测量结果。
- 未做真实 Android/iPhone 硬件或 Safari 引擎实机测试，未做人工逐条发音/音色认证。浏览器检查验证映射、文件可访问、解码、播放及功能行为。
- 当前基线没有启用远端登录/同步服务，相关配置原样保留；未测试远端登录或同步，不把这一项标记为通过。音频接入不需要 API。
- 输入包自带 HTML 存在 script 闭合问题；本次基于现有可运行版本接入 MP3，并生成一致的两个有效入口。

原音频逐文件哈希见 source-audio-sha256.json，结构化检查结果见 recording-integration-results.json。
