# 老K学英语

在原网站“出行与社会”入口新增 **218 条**词汇，原页面、按钮、电脑／手机版操作和学习记录格式保持。四个二级入口为：交通、方向与位置 **85**，城市与公共场所 **39**，职业与工作 **45**，购物与金钱 **49**。继续使用原选择弹窗，提供整组练习及 **12 个小类，每类 12–24 词**。

源词条 ID、英文、DJ 英式音标、中文及中英文例句逐项保留。新增 **401 段** Bella GA 单词／完整例句 MP3，32 处复用旧录音，另外 3 处重复词共用本包录音；原 **2616 段**字节不变，总数 **3017 段**。新增 **28 张**无损 WebP 图集，为 218 条各提供独立场景，需要人物时沿用首页男孩／女孩。原 140 个场景文件、首页及分类背景不变。网页仅播放静态 MP3，不需要 API 或运行时语音合成。

全站现有 **1428 条词汇、28 个有内容入口、88 个学习分组，每组 10–24 词**。原基础入门 136、时间与自然 220、学校与学习 198、家庭与日常生活 200、饮食与健康 218、动物与自然 238 均保留。“动作、描述与表达”四个入口继续为空。源包五个语义分类映射到原有四个入口，不能按词条 ID 中的 S01–S05 推断 UI 入口。

手机版继续使用已同步的浅色紫色模板、抽屉导航、两列分类卡、单列主要卡片及原触屏输入／底部练习操作。系统深色偏好下首屏仍浅色；软键盘弹出时保留题目与操作按钮。搜索、DJ、GA、完整例句填空、词义对应、居中答案弹窗、正确提交、上下题、重练、续学、资料、打卡、备份及本地记录沿用原功能。

`café` 的 é 保持在同一英文单词内，修复原分词把重音字母拆成标点的兼容问题；原词条与操作流程保持。

`penny` 的源例句使用不规则复数 `pence`，沿用原词条拼写练习并在用法中说明，保留源例句；没有为此改动全站填空算法。`delivery` 在源中文用“货物明天送到”自然表达，用原“本句用法”提示并保留词义。

## 完整包和部署

- 网站：https://laodix579-beep.github.io/codex-test/
- 原下载入口：https://laodix579-beep.github.io/codex-test/downloads/frog-study-offline.zip

完整包超过 GitHub 的单个提交文件限制，原下载入口现在自动下载当前 `gh-pages` 发布分支的 GitHub 完整 ZIP；没有额外网站。解压后打开 `codex-test-gh-pages` 文件夹，把其中含 `index.html` 的全部文件与文件夹一起上传到发布根目录，保留层级。不要把 ZIP 文件直接上传充当网页，也不要多套一层文件夹。具体步骤见 [DEPLOY_WINDOWS.md](DEPLOY_WINDOWS.md)。原“保存完整网页”仍导出含个人记录和媒体的单 HTML。为避免本包全部媒体的 base64 文本超过浏览器单字符串容量，单文件改用可逆的紧凑字符封装，打开时还原为原有数据格式；录音和图片字节完全保持，下载、源码复制和练习流程沿用原入口。

## 内容维护与核对

- C07 原始 JSON 与审阅稿保留于 `data/travel-social/`，SHA-256 见 `reports/travel-source-sha256.json`。`tools/build_travel_assets.py` 追加 `travel-social-v1`，词库版本保持 `basic-us-v1`，安装一次，尊重用户删除，旧备份可补装新包。
- `tools/build_travel_mappings.py` 维护 218 个中文词义对应与四入口的 12 个小类；窗口与源语义分类关系见 `data/travel-social-windows.json`，分组定义见 `data/travel-social-practice-sections.json`。
- `tools/generate_travel_audio.py` 只制作新包缺少的录音，模型／依赖在仓库外；词与整句路径见 `data/travel-social-audio-map.csv`，音素及哈希见 `data/travel-social-audio-generation.json`。
- `tools/build_travel_scenes.py` 将图像工具生成的 28 张 PNG 无损编码为 WebP 图集，沿用现有分格渲染；218 个词各有独立场景，源图哈希见 `reports/travel-scene-source-sha256.json`。


- C06 原始 JSON 与审阅稿保留于 `data/animal-nature/`，SHA-256 见 `reports/animal-source-sha256.json`。`tools/build_animal_assets.py` 追加 `animal-nature-v1`，词库版本保持 `basic-us-v1`，安装一次，尊重用户删除；旧备份可补装新包。
- `tools/build_animal_mappings.py` 校验中文词义对应与四入口的 15 个小类；源六语义类别与四 UI 入口关系见 `data/animal-nature-windows.json`，练习定义见 `data/animal-nature-practice-sections.json`。词条 ID 保持，不按 ID 中 S01–S06 推断网站入口。
- `tools/generate_animal_audio.py` 只制作新包缺少的录音，模型/依赖在仓库外；词、整句路径见 `data/animal-nature-audio-map.csv`，音素及哈希见 `data/animal-nature-audio-generation.json`。原 C06 接入时既有的 2169 段不变，网页不调用语音合成。
- `tools/build_animal_scenes.py` 将图像工具生成的 30 张 PNG 无损编码为 WebP 图集，浏览器沿用现有分格渲染；238 个词各有独立对应场景，源图哈希见 `reports/animal-scene-source-sha256.json`。

- 原始词包 JSON 分别保留于 `data/time-nature/`、`data/school-learning/`、`data/family-daily/`、`data/food-health/`、`data/animal-nature/`、`data/travel-social/`。原基础资料为 `data/basic-vocabulary.json`。
- `tools/build_food_assets.py` 追加 C05 内容包；词库版本保持 `basic-us-v1`，按 `food-health-v1` 包标记安装一次，旧状态/旧备份保留，用户明确删除后不强制补回。
- `tools/build_food_mappings.py` 维护本包中文词义对应及四入口的 14 个小类；具体分组见 `data/food-health-practice-sections.json`。`data/food-health-windows.json` 保留源语义分类和网站入口的对应关系。
- `tools/generate_food_audio.py` 是制作阶段的可选工具，仅制作新包缺少的录音；依赖、模型和临时缓存不随网站分发。`data/food-health-audio-generation.json` 记录音素、声线、模型和文件哈希；`data/food-health-audio-map.csv` 提供 218 条单词与例句映射。
- `data/practice-group-policy.json` 维护全站相关小类的合并与 10–25 词目标；运行各词包构建器后，必须运行 `tools/build_practice_groups.py`，重新应用合并、校验全量覆盖并更新页面及审计报告。重复构建不会恢复零碎分组。
- `tools/build_audio_assets.py`、`build_meaning_assets.py`、`build_scene_assets.py`、`build_practice_groups.py` 校验并内嵌全部已发布词包的静态映射。
- `python3 tools/package_pages.py /workspace/output/laok-pages-v44.zip` 可生成本地平铺部署包，公开下载使用原入口自动提供当前 `gh-pages` 完整源码 ZIP，避免递归提交大 ZIP。

在仓库根目录运行 `python3 -m http.server 8000` 后，使用 Python Playwright 和 Chromium 核对：

```sh
python3 tests/travel_social.py
python3 tests/audio_quality.py
python3 tests/site_group_audit.py
python3 tests/mobile_light.py
python3 tests/mobile_touch.py
python3 tests/startup_paint.py
python3 tests/practice_groups.py
python3 tests/learning_progress.py
python3 tests/resume_position.py
python3 tests/practice_focus.py
python3 tests/home_export.py
python3 tests/pages_package.py /workspace/output/laok-pages-v44.zip
```

当前实际通过范围见 [reports/test-report.md](reports/test-report.md)；历史教材流程测试仍作归档，未声称其通过当前仅词库版本。
