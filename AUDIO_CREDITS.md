# 美式英语音频

内置语音已从旧的英式录音替换为重新生成的通用美式英语录音。
新词条、英文例句、已有课程与音标例词均使用同一套美式配音。

- 模型：Kokoro-82M v1.0，Apache-2.0。
- 声音：`af_heart`（American English），语言参数 `en-us`，生成速度 0.92。
- 推理：kokoro-onnx 0.4.9，CPU，模型 `kokoro-v1.0.int8.onnx`。
- 转码：FFmpeg / libmp3lame，单声道 MP3，48 kbit/s。
- 模型与声音文件的固定发布版本：
  https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.0
- 模型来源：https://github.com/hexgrad/kokoro
- 推理实现：https://github.com/thewh1teagle/kokoro-onnx

许可证见 `licenses/`。本应用分发的是生成的音频，不分发模型。
生成式语音仍可能存在个别词语的读音偏差，可在网页逐词试听。

`tools/generate_us_audio.py` 是可选的音频制作工具；运行网页无需安装模型或连接语音服务。
它保留现有音频目录中的所有提示语，并补全当前词库的词条和例句。
生成工具使用的临时缓存应放在仓库以外，不要提交模型、虚拟环境或中间音频。

用户以后手动添加、且没有内置录音的新内容，使用浏览器提供的 `en-US` 语音。
没有美式语音时会提示安装美国英语语音包，不会回退到英式声音。
