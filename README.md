# 老K学英语

本次在原网站的“饮食与健康”入口新增 **218 条**：水果与蔬菜 64、食物主食与饮料 69、身体部位 41、健康与身体感受 44。总词库现为 **972 条**，原基础入门 136、时间与自然 220、学校与学习 198、家庭与日常生活 200 保持。

沿用现有四个二级入口和选择弹窗，补齐 **37 个具体练习小类**：水果与蔬菜 11 类、食物主食与饮料 11 类、身体部位 6 类、健康与身体感受 9 类。每个入口保留整组练习，下面按实际词条显示各小类数量，每类 2–11 词。健康组包括健康状态 4、疼痛与不适 6、感冒与发热 8、日常身体感受 7、受伤与伤口 4、药品与护理 4、医护人员与场所 5、休息与康复 3、身体不适与求助 3。搜索、DJ 英式音标、GA 美式朗读、例句填空、答案弹窗、上下题、整组重练、续学、资料、打卡、备份和本地记录保持。

新增 **417 个** Bella GA 单词／完整语句 MP3，相同读音复用已有文件；原 **1752 个 MP3** 字节保持，总数 **2169 个**。新增 28 张无损 WebP 图集，为 218 条各提供对应场景，沿用首页男孩与女孩，并按例句补充家人和医生。网页使用随包静态资源，无需语音服务或 API Key。

源 ZIP 的四窗口与六个语义类别分别保留于原始 JSON；既有网站入口仍为四个，词条 ID 不变。源标签 `cold (feeling)` 的括号用于区分词义，练习和朗读使用 `cold`，DJ、词义和例句保留。补充 green bean／bean sprout 在例句中的规则复数识别，答题要求实际词形；原 754 条填空结果保持。thumb 的源例句使用 thumbs-up 复合词，沿用原单词拼写回退，不强制填写不同词。

## 完整包和部署

- 网站：https://laodix579-beep.github.io/codex-test/
- 原下载入口：https://laodix579-beep.github.io/codex-test/downloads/frog-study-offline.zip

完整包超过 GitHub 的单个提交文件限制，原下载入口现在自动下载当前 `gh-pages` 发布分支的 GitHub 完整 ZIP；没有额外网站。解压后打开 `codex-test-gh-pages` 文件夹，把其中含 `index.html` 的全部文件与文件夹一起上传到发布根目录，保留层级。不要把 ZIP 文件直接上传充当网页，也不要多套一层文件夹。具体步骤见 [DEPLOY_WINDOWS.md](DEPLOY_WINDOWS.md)。原“保存完整网页”仍导出含个人记录和媒体的单 HTML。

## 内容维护与核对

- 原始词包 JSON 分别保留于 `data/time-nature/`、`data/school-learning/`、`data/family-daily/`、`data/food-health/`。原基础资料为 `data/basic-vocabulary.json`。
- `tools/build_food_assets.py` 追加 C05 内容包；词库版本保持 `basic-us-v1`，按 `food-health-v1` 包标记安装一次，旧状态/旧备份保留，用户明确删除后不强制补回。
- `tools/build_food_mappings.py` 维护本包中文词义对应及四入口的 37 个小类；具体分组见 `data/food-health-practice-sections.json`。`data/food-health-windows.json` 保留源语义分类和网站入口的对应关系。
- `tools/generate_food_audio.py` 是制作阶段的可选工具，仅制作新包缺少的录音；依赖、模型和临时缓存不随网站分发。`data/food-health-audio-generation.json` 记录音素、声线、模型和文件哈希；`data/food-health-audio-map.csv` 提供 218 条单词与例句映射。
- `tools/build_audio_assets.py`、`build_meaning_assets.py`、`build_scene_assets.py`、`build_practice_groups.py` 校验并内嵌全部已发布词包的静态映射。
- `python3 tools/package_pages.py /workspace/output/laok-pages-v39.zip` 可生成本地平铺部署包，公开下载使用原入口自动提供当前 `gh-pages` 完整源码 ZIP，避免递归提交大 ZIP。

在仓库根目录运行 `python3 -m http.server 8000` 后，使用 Python Playwright 和 Chromium 核对：

```sh
python3 tests/food_sections.py
python3 tests/food_health.py
python3 tests/food_forms.py
python3 tests/family_daily.py
python3 tests/phrase_forms.py
python3 tests/school_learning.py
python3 tests/time_nature.py
python3 tests/meaning_targets.py
python3 tests/practice_groups.py
python3 tests/audio_quality.py
python3 tests/home_export.py
python3 tests/pages_package.py /workspace/output/laok-pages-v39.zip
```

当前实际通过范围见 [reports/test-report.md](reports/test-report.md)；历史教材流程测试仍作归档，未声称其通过当前仅词库版本。
