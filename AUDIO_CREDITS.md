# 美式英语音频

词条、英文例句、已有课程与音标例词均使用美式配音。
书面音标采用英式 DJ 体系，作为教材式学习参考；它与美式录音分别维护，部分元音和 r 音会有所区别。

- 模型：Kokoro-82M v1.0，Apache-2.0。
- 声音：`af_bella`（American English），原始生成速度 1.0。
- 发音前端：Misaki-fork 0.9.6 美式英语词典；使用模型约定的音素格式。未收录的人名使用 Misaki 自带、经过格式转换的美式 eSpeak 回退，不把原始 eSpeak 音素直接送入模型。
- 推理：kokoro-onnx 0.6.0，CPU，全精度模型 `kokoro-v1.0.onnx`。
- 转码：FFmpeg / libmp3lame，24 kHz 单声道 MP3，96 kbit/s。
- 单词按独立词条生成，不额外添加句末标点；例句保留原始标点。音频裁除静音后增加短暂停顿，并做峰值归一化；单词卡试听按标准速度播放，练习语速由用户设置。
- 模型与声音文件的固定发布版本：
  https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.1
- 模型来源：https://github.com/hexgrad/kokoro
- 推理实现：https://github.com/thewh1teagle/kokoro-onnx
- 英语发音前端：https://github.com/hexgrad/misaki

许可证见 `licenses/`。本应用分发的是生成的音频，不分发模型。
生成式语音仍可能存在个别词语的读音偏差，可在网页逐词试听。

`tools/generate_us_audio.py` 是可选的音频制作工具；运行网页无需安装模型或连接语音服务。
它从网页中的真实课程、词条和例句提取原文，保留大小写与标点，为每段录音保存对应原文。缓存标识包含原文、音素、模型、声音和编码参数，避免修改配音后误用旧录音。
生成工具使用的临时缓存应放在仓库以外，不要提交模型、虚拟环境或中间音频。

用户以后手动添加、且没有内置录音的新内容，使用浏览器提供的 `en-US` 语音。
没有美式语音时会提示安装美国英语语音包，不会回退到英式声音。
