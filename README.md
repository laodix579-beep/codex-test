# 老K学英语

本次在原网站的“学校与学习”入口新增 **198 条**词汇：学习用品 43、教室与校园 45、学科名称 31、课堂常用词 79。总词库现为 **554 条**，基础入门 136 与时间与自然 220 保持原样。

沿用原有界面和操作：四个二级入口提供整组练习及 19 个可选小组，搜索、DJ 英式音标、GA 美式朗读、例句填空、答案弹窗、上下题、整组重练、续学、个人资料、打卡、备份和本地学习记录保持可用。保留完整词义及中文对应提示；非逐字翻译使用本句用法。DJ 标注与 GA 音频分别维护。

新增 **359 个** Bella GA 单词／完整语句 MP3，复用已有相同读音；原 **1028 个 MP3** 字节保持。新增 25 张无损 WebP 图集，为 198 条词汇各提供对应场景，人物沿用首页男孩与女孩。资源全部静态随包提供，浏览器无需模型、语音服务或 API Key。

## 完整包和部署

- 网站：https://laodix579-beep.github.io/codex-test/
- 原下载入口：https://laodix579-beep.github.io/codex-test/downloads/frog-study-offline.zip

完整包超过 GitHub 的单个提交文件限制，原下载入口现在自动下载当前 `gh-pages` 发布分支的 GitHub 完整 ZIP；没有额外网站。解压后打开 `codex-test-gh-pages` 文件夹，把其中含 `index.html` 的全部文件与文件夹一起上传到发布根目录，保留层级。不要把 ZIP 文件直接上传充当网页，也不要多套一层文件夹。具体步骤见 [DEPLOY_WINDOWS.md](DEPLOY_WINDOWS.md)。原“保存完整网页”仍导出含个人记录和媒体的单 HTML。

## 内容维护与核对

- 原始 C03 JSON 保留于 `data/school-learning/`，来源 ZIP 未附带录音。
- `tools/build_school_assets.py` 只追加内容包，词库版本保持 `basic-us-v1`。已有状态和旧备份按包标记安装一次，用户删除词条后不强制补回。
- `tools/build_school_mappings.py` 维护中文词义对应和练习分组。
- `tools/generate_school_audio.py` 是制作阶段的可选工具，只制作新包缺少的录音；模型、依赖和临时缓存不随网站分发。`data/school-learning-audio-generation.json` 记录音素、声线、模型和文件哈希。
- `tools/build_audio_assets.py`、`build_meaning_assets.py`、`build_scene_assets.py`、`build_practice_groups.py` 校验并内嵌静态映射。
- `python3 tools/package_pages.py /workspace/output/laok-pages-v36.zip` 可生成便于本地验证的平铺部署 ZIP，不向仓库提交递归的大 ZIP。

在仓库根目录运行 `python3 -m http.server 8000` 后，使用 Python Playwright 和 Chromium 核对：

```sh
python3 tests/school_learning.py
python3 tests/time_nature.py
python3 tests/meaning_targets.py
python3 tests/practice_groups.py
python3 tests/audio_quality.py
python3 tests/home_export.py
python3 tests/pages_package.py /workspace/output/laok-pages-v36.zip
```

当前实际通过范围见 [reports/test-report.md](reports/test-report.md)；历史教材流程测试仍作归档，未声称其通过当前仅词库版本。
