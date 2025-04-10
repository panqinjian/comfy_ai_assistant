"""
FFmpeg命令处理测试示例
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到系统路径
current_dir = Path(__file__).parent
project_root = current_dir.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from ai_services.handlers.fun_media_handlers import fun_process_ffmpeg_command

# 测试AI响应
test_response = """以下是使用FFmpeg转换视频格式的命令，可以将MP4文件转换为更小的尺寸：

<content type='ffmpeg' cmd='ffmpeg -i input.mp4 -vf "scale=1280:-1" -c:v libx264 -crf 23 -preset medium -c:a aac -b:a 128k output.mp4' title='视频尺寸调整和转码'></content>

这个命令会将输入的MP4文件调整为宽度1280像素(保持长宽比)，并使用H.264编码以及中等的压缩预设。音频会被转换为AAC格式，码率为128kbps。"""

# 测试系统信息响应
system_info_response = """请获取系统和FFmpeg信息

<content type='ffmpeg' explanation='需要获取系统信息和FFmpeg版本' title='系统和FFmpeg信息'></content>
"""

def main():
    # 处理FFmpeg命令响应
    result = fun_process_ffmpeg_command(test_response)
    with open("ffmpeg_command_test.html", "w", encoding="utf-8") as f:
        f.write(result)
    print(f"命令转换结果已保存到 ffmpeg_command_test.html")
    
    # 处理系统信息响应
    system_result = fun_process_ffmpeg_command(system_info_response)
    with open("ffmpeg_system_info_test.html", "w", encoding="utf-8") as f:
        f.write(system_result)
    print(f"系统信息结果已保存到 ffmpeg_system_info_test.html")

if __name__ == "__main__":
    main() 