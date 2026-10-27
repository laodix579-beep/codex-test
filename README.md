# 老K学英语

手机版已同步为电脑端的浅色紫色模板，使用相同的首页、八大类／二级分类、小类选择、学习进度与个人资料入口。手机采用抽屉导航、两列首页分类卡、单列主要卡片和适合触屏的字号／按钮；练习继续使用原手机输入、答案与底部操作，播放器保持可见。软键盘弹出时收起大图、压缩顶部，并防止点击操作按钮时因焦点变化造成移位漏点。首屏和安装启动背景均为浅色，系统深色模式下也保持此设计。

原 1210 词、DJ、2616 段 MP3、140 张场景图片、分类背景和个人记录格式均保持。词汇、题目、掌握记录、笔记、资料和备份不会因模板更新而清空。完整验证见 `reports/mobile-light-v43-test-report.md`。

在原网站“动物与自然”入口新增 **238 条**，保持原页面、操作、设置和记录格式。四个二级入口为：宠物与农场动物 **72**、野生与海洋动物 **75**、植物与花卉 **42**、自然环境 **49**。各入口均保留整组练习与小类弹窗，共 **15 个小类，每类 11–20 词**；按相近内容组织，不拆成零碎小组。

本包词条、ID、DJ 英式音标及中英文例句保留源值。新增 **447 段** Bella GA 单词／完整例句 MP3，其余相同读音复用现有录音；原 **2169 段**字节不变，总数 **2616 段**。新增 **30 张**无损 WebP 图集，为 238 条各提供独立场景；需要人物时沿用首页男孩与女孩，其余突出对应动植物及环境。原 110 个图片文件与分类背景保持。

全站现有 **1210 条词汇、24 个有内容入口、76 个学习分组，每组 10–24 词**。原基础入门 136、时间与自然 220、学校与学习 198、家庭与日常生活 200、饮食与健康 218 保留。其余未提供词汇的入口继续为空。搜索、DJ、GA、完整例句填空、词义对应、居中答案弹窗、正确提交、上下题、重练、续学、资料、打卡、备份及本地记录沿用原功能。

源包六个语义分类映射到既有四个入口，保持 UI ID 和源词条 ID。`kid` 在本包指小山羊，`lead` 指牵引绳；中文例句中 `poppy` 仅概括为红花，使用原“本句用法”提示并保留词义，避免错误地把所有红花等同于 poppy。

## 完整包和部署

- 网站：https://laodix579-beep.github.io/codex-test/
- 原下载入口：https://laodix579-beep.github.io/codex-test/downloads/frog-study-offline.zip

完整包超过 GitHub 的单个提交文件限制，原下载入口现在自动下载当前 `gh-pages` 发布分支的 GitHub 完整 ZIP；没有额外网站。解压后打开 `codex-test-gh-pages` 文件夹，把其中含 `index.html` 的全部文件与文件夹一起上传到发布根目录，保留层级。不要把 ZIP 文件直接上传充当网页，也不要多套一层文件夹。具体步骤见 [DEPLOY_WINDOWS.md](DEPLOY_WINDOWS.md)。原“保存完整网页”仍导出含个人记录和媒体的单 HTML。

## 内容维护与核对

- 新包原始 JSON 与审阅稿保留于 `data/animal-nature/`，SHA-256 见 `reports/animal-source-sha256.json`。`tools/build_animal_assets.py` 追加 `animal-nature-v1`，词库版本保持 `basic-us-v1`，安装一次，尊重用户删除；旧备份可补装新包。
- `tools/build_animal_mappings.py` 校验中文词义对应与四入口的 15 个小类；源六语义类别与四 UI 入口关系见 `data/animal-nature-windows.json`，练习定义见 `data/animal-nature-practice-sections.json`。词条 ID 保持，不按 ID 中 S01–S06 推断网站入口。
- `tools/generate_animal_audio.py` 只制作新包缺少的录音，模型/依赖在仓库外；词、整句路径见 `data/animal-nature-audio-map.csv`，音素及哈希见 `data/animal-nature-audio-generation.json`。原 2169 段不变，网页不调用语音合成。
- `tools/build_animal_scenes.py` 将图像工具生成的 30 张 PNG 无损编码为 WebP 图集，浏览器沿用现有分格渲染；238 个词各有独立对应场景，源图哈希见 `reports/animal-scene-source-sha256.json`。

- 原始词包 JSON 分别保留于 `data/time-nature/`、`data/school-learning/`、`data/family-daily/`、`data/food-health/`、`data/animal-nature/`。原基础资料为 `data/basic-vocabulary.json`。
- `tools/build_food_assets.py` 追加 C05 内容包；词库版本保持 `basic-us-v1`，按 `food-health-v1` 包标记安装一次，旧状态/旧备份保留，用户明确删除后不强制补回。
- `tools/build_food_mappings.py` 维护本包中文词义对应及四入口的 14 个小类；具体分组见 `data/food-health-practice-sections.json`。`data/food-health-windows.json` 保留源语义分类和网站入口的对应关系。
- `tools/generate_food_audio.py` 是制作阶段的可选工具，仅制作新包缺少的录音；依赖、模型和临时缓存不随网站分发。`data/food-health-audio-generation.json` 记录音素、声线、模型和文件哈希；`data/food-health-audio-map.csv` 提供 218 条单词与例句映射。
- `data/practice-group-policy.json` 维护全站相关小类的合并与 10–25 词目标；运行各词包构建器后，必须运行 `tools/build_practice_groups.py`，重新应用合并、校验全量覆盖并更新页面及审计报告。重复构建不会恢复零碎分组。
- `tools/build_audio_assets.py`、`build_meaning_assets.py`、`build_scene_assets.py`、`build_practice_groups.py` 校验并内嵌全部已发布词包的静态映射。
- `python3 tools/package_pages.py /workspace/output/laok-pages-v43.zip` 可生成本地平铺部署包，公开下载使用原入口自动提供当前 `gh-pages` 完整源码 ZIP，避免递归提交大 ZIP。

在仓库根目录运行 `python3 -m http.server 8000` 后，使用 Python Playwright 和 Chromium 核对：

```sh
python3 tests/mobile_light.py
python3 tests/mobile_touch.py
python3 tests/startup_paint.py
python3 tests/practice_groups.py
python3 tests/learning_progress.py
python3 tests/resume_position.py
python3 tests/practice_focus.py
python3 tests/home_export.py
python3 tests/pages_package.py /workspace/output/laok-pages-v43.zip
```

当前实际通过范围见 [reports/test-report.md](reports/test-report.md)；历史教材流程测试仍作归档，未声称其通过当前仅词库版本。
