# 仅保留单词仓库版本测试报告

日期：2026-10-25（北京时间）。基于 9e1766c，页面缓存版本 frog-warehouse-only-v16。

## 当前行为

- 已移除课程广场、教材同步、音标课程导航和 PEP 试听入口；旧链接重定向到单词仓库。
- 默认只展示基础入门：问候与礼貌用语 22、数字与数量 62、颜色 19、形状与大小 33，共 136 词；空主题及空二级分类不展示。
- 搜索只查当前仓库词条、释义及对应例句。独立试听词 apple/book 不自动进入结果；用户原先已保存到仓库的自定义词仍保留。
- 首页学习入口、计划、收藏和练习均使用仓库词条。新用户不再自动添加示例课程；个人网页导出也不自动补入教材。
- 历史课程、句子进度和收藏仍在原本的 localStorage 与完整备份中。没有执行清空、删除学习记录或重置仓库操作。
- 提供的 MP3 字节保持原样，不调用 TTS，不需要 API。未使用的录音和来源文件保留作归档，不作为额外学习词条展示。

## 本次实际通过

1. `tests/warehouse_scope.py`：桌面和手机模拟配置验证导航、目录、旧链接、仓库范围搜索、历史课程不外露、自定义词保留、收藏/笔记/进度/计划不变、完整备份和离线单词练习。默认 136 个内置词 ID 与顺序不变。
2. `tests/word_catalog.py`：分类、词库迁移与恢复副本、用户添加词、个人单文件导出、录音解码及离线播放。
3. `tests/word_entry.py`：有词条分类弹窗、整组练习数量、图片设置、空分类旧链接回退和词条管理。
4. `tests/word_spelling.py`：拼写、错词、重试、触屏和输入音效。
5. `tests/word_cloze.py`：136 个词条例句上下文、短语及词形、词义位置、桌面与手机答题。
6. `tests/navigation_audio.py`：返回、取消、答题完成后的单次朗读、重听和退出停止播放。
7. `tests/mobile_startup.py`：缺少新版浏览器 API 的安卓/iPhone UA 模拟、数据保存及异常可见提示。
8. `tests/sentence_word_audio.py`：实际播放例句一次、目标词两次，重听、切题取消及退出取消。
9. `tests/speech_reference.py`：仓库 DJ 显示、已有单词和例句 MP3、旧音标链接回退、缺录音提示及禁止 TTS。

部署 ZIP 已实际解压，在 /preview/project/ 子路径验证了两个入口、仅仓库目录、旧链接回退和单词 MP3 播放；打包时再次核对了 610 个原始 MP3 哈希。

结构化结果见 `warehouse-scope-results.json` 和 `warehouse-regression-results.json`。

## 范围与未执行项

- 旧教材/独立音标页面以及 v15 独立试听词场景已按要求移除，本次没有把相关旧流程列作通过。具体为 mobile_practice.py、space_shortcuts.py、pep_pronunciation.py 的旧模块场景及 recording_integration.py 的旧试听词搜索场景。
- 没有做真实手机硬件、Safari 引擎实测或人工发音认证；手机为 Chromium 视口、触屏与旧 API/UA 模拟。
- 未测试远端登录/同步服务；原配置文件保留。
- v15 完整录音接入的历史结果保存在 `recordings-v15-test-report.md`；本报告不将旧结果冒充本次重新执行。
