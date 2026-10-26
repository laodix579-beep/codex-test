# 老K学英语

本次在原网站的“家庭与日常生活”入口新增 **200 条**：家庭成员 33、房间与家具 44、家居用品 53、日常生活与作息 70。总词库现为 **754 条**，原基础入门 136、时间与自然 220、学校与学习 198 保持。

沿用原有界面和操作：四个二级入口提供整组练习及 22 个可选小组，搜索、DJ 英式音标、GA 美式朗读、例句填空、答案弹窗、上下题、整组重练、续学、个人资料、打卡、备份和本地学习记录保持可用。补齐 plays/washes/does/mops/takes 五种短语动词词形识别，例句和词条原文保留；答题仍要求填写例句实际词形。原 554 条填空结果与更新前一致。

新增 **365 个** Bella GA 单词／完整语句 MP3，相同读音复用已有录音；原 **1387 个 MP3** 字节保持，现有总数 **1752 个**。新增 25 张无损 WebP 图集，为 200 条各提供对应场景，人物沿用首页男孩与女孩，并按家人关系添加成人或其他孩子。资源静态随包提供，运行网页无需模型、语音服务或 API Key。

## 完整包和部署

- 网站：https://laodix579-beep.github.io/codex-test/
- 原下载入口：https://laodix579-beep.github.io/codex-test/downloads/frog-study-offline.zip

完整包超过 GitHub 的单个提交文件限制，原下载入口现在自动下载当前 `gh-pages` 发布分支的 GitHub 完整 ZIP；没有额外网站。解压后打开 `codex-test-gh-pages` 文件夹，把其中含 `index.html` 的全部文件与文件夹一起上传到发布根目录，保留层级。不要把 ZIP 文件直接上传充当网页，也不要多套一层文件夹。具体步骤见 [DEPLOY_WINDOWS.md](DEPLOY_WINDOWS.md)。原“保存完整网页”仍导出含个人记录和媒体的单 HTML。

## 内容维护与核对

- 原始词包 JSON 分别保留于 `data/time-nature/`、`data/school-learning/`、`data/family-daily/`。原基础资料为 `data/basic-vocabulary.json`。
- `tools/build_family_assets.py` 追加 C04 内容包；词库版本保持 `basic-us-v1`，按 `family-daily-v1` 包标记安装一次，旧状态/旧备份保留，用户明确删除后不强制补回。
- `tools/build_family_mappings.py` 维护本包中文词义对应和 22 个练习小组。
- `tools/generate_family_audio.py` 是制作阶段的可选工具，仅制作新包缺少的录音；依赖、模型和临时缓存不随网站分发。`data/family-daily-audio-generation.json` 记录音素、声线、模型和文件哈希；`data/family-daily-audio-map.csv` 提供 200 条单词与例句映射。
- `tools/build_audio_assets.py`、`build_meaning_assets.py`、`build_scene_assets.py`、`build_practice_groups.py` 校验并内嵌全部已发布词包的静态映射。
- `python3 tools/package_pages.py /workspace/output/laok-pages-v37.zip` 可生成本地平铺部署包，公开下载使用原入口自动提供当前 `gh-pages` 完整源码 ZIP，避免递归提交大 ZIP。

在仓库根目录运行 `python3 -m http.server 8000` 后，使用 Python Playwright 和 Chromium 核对：

```sh
python3 tests/family_daily.py
python3 tests/phrase_forms.py
python3 tests/school_learning.py
python3 tests/time_nature.py
python3 tests/meaning_targets.py
python3 tests/practice_groups.py
python3 tests/audio_quality.py
python3 tests/home_export.py
python3 tests/pages_package.py /workspace/output/laok-pages-v37.zip
```

当前实际通过范围见 [reports/test-report.md](reports/test-report.md)；历史教材流程测试仍作归档，未声称其通过当前仅词库版本。
