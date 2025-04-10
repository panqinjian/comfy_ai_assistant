import re
import json
from aiohttp import web
import shlex
import subprocess
from flask import Flask, Response  # Flask框架核心组件

try:
    from .utils.cmd_win import run_cmd_with_subprocess
except Exception as e:
    from utils.cmd_win import run_cmd_with_subprocess


def register_ffmpeg_api(app):
    try:
        app.router.add_post("/comfy_ai_assistant/cmd_win_ffmpeg", cmd_win_ffmpeg_route)
        app.router.add_get("/comfy_ai_assistant/ffmpeg_run_win", ffmpeg_run_win_route)
        print("ComfyUI AI Assistant: ffmpeg API 已注册")
    except Exception as e:
        print(f"ComfyUI AI Assistant: 注册ffmpeg API 失败: {e}")

async def ffmpeg_run_win_route(request):
    """处理FFmpeg命令的API路由"""
    try:
        # 获取请求数据
        try:
            data = await request.json()
        except json.JSONDecodeError:
            return web.json_response({"success": False, "error": "无效的JSON格式"}, status=400)

        cmd = data.get('cmd')
        timestamp = data.get('timestamp')
        if not cmd:
            return web.json_response({"success": False, "error": "命令不能为空"}, status=400)

        # 命令验证和过滤
        command_parts = shlex.split(cmd)
        if not command_parts:
            return web.json_response({"success": False, "error": "无效命令"}, status=400)

        # 执行命令并获取分析结果
        result = ffmpeg_run_win(cmd,timestamp=timestamp ,shell=False)
        
        return web.json_response({"success": True, "result": result})

    except Exception as e:
        return web.json_response({"success": False, "error": str(e)}, status=500)


def ffmpeg_run_win(cmd,timestamp ,cwd=None, shell=True, timeout=None, encoding='utf-8'):
    def generate():
        process = subprocess.Popen(
            cmd,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        while True:
            line = process.stderr.readline()
            if not line and process.poll() is not None:
                yield f"data: {json.dumps({'type': 'result', 'success': True})}\n\n"
                break
            
            if "time=" in line:
                time_match = re.search(r"time=(\d+:\d+:\d+\.\d+)", line)
                if time_match:
                    yield f"data: {json.dumps({'type': 'progress', 'time': time_match.group(1)})}\n\n"

    return Response(generate(), mimetype="text/event-stream")

async def cmd_win_ffmpeg_route(request):
    """处理FFmpeg命令的API路由"""
    try:
        # 获取请求数据
        try:
            data = await request.json()
        except json.JSONDecodeError:
            return web.json_response({"success": False, "error": "无效的JSON格式"}, status=400)

        cmd = data.get('cmd')

        if not cmd:
            return web.json_response({"success": False, "error": "命令不能为空"}, status=400)

        # 命令验证和过滤
        command_parts = shlex.split(cmd)
        if not command_parts:
            return web.json_response({"success": False, "error": "无效命令"}, status=400)

        # 执行命令并获取分析结果
        result = cmd_win_ffmpeg(cmd, shell=False)
        
        return web.json_response({"success": True, "result": result})

    except Exception as e:
        return web.json_response({"success": False, "error": str(e)}, status=500)

def cmd_win_ffmpeg(cmd, cwd=None, shell=True, timeout=None, encoding='utf-8'):
    """
    执行FFmpeg命令并分析结果
    
    Args:
        cmd: 要执行的FFmpeg命令
        cwd: 执行命令的工作目录
        shell: 是否使用shell执行
        timeout: 超时时间（秒）
        encoding: 输出编码
        
    Returns:
        dict: 包含执行结果及分析的字典
    """
    #print(f"执行FFmpeg命令: {cmd}")
    
    # 执行命令
    result = run_cmd_with_subprocess(cmd, cwd=cwd, shell=shell, timeout=timeout, encoding=encoding)
    
    # 提取实际错误信息（去除版本和配置信息）
    if not result['success'] and result['error']:
        error_lines = result['error'].split('\n')
        actual_error = []
        for line in error_lines:
            # 跳过版本信息、配置信息和库版本信息
            if (line.startswith('ffmpeg version') or 
                line.startswith('  configuration:') or 
                line.startswith('  built with') or 
                line.startswith('  lib')):
                continue
            if line.strip():
                actual_error.append(line.strip())
        result['error'] = '\n'.join(actual_error)

    
    # 分析FFmpeg执行结果
    if result['success']:
        # 命令执行成功
        analysis = analyze_successful_ffmpeg(str(result))
        for key,item in analysis.items():
            result[key] = item

        if result['type']:
            result['error']=""

        #result['analysis'] = analysis
    else:
        # 命令执行失败
        analysis = analyze_failed_ffmpeg(result['error'], result['output'], result['exit_code'])
        for key,item in analysis.items():
            result[key] = item
        #result['analysis'] = analysis
    
    result['output']=result['output'].replace(f'\\\\', f'\\')
    result['message']=result['message'].replace(f'\\\\', f'\\')
    return result

def analyze_successful_ffmpeg(output):
    """分析成功的FFmpeg输出"""
    analysis = {
        'type': 'success',
        'message': '命令执行成功'
    }
    
    # 提取输出文件信息
    output_match = re.search(r"Output #\d+, .+?, to ['\"](.*?)['\"]", output)
    if output_match:
        output_file = output_match.group(1)
        analysis['output'] =output_file
        analysis['message'] = f"成功生成文件: {output_file}"
    
    # 提取处理时间
    time_match = re.search(r"time=(\d+:\d+:\d+\.\d+)", output)
    if time_match:
        analysis['details'] = {'processed_time': time_match.group(1)}
    
    # 提取统计信息
    size_matches = re.findall(r"video:(\d+)kB audio:(\d+)kB", output)
    if size_matches:
        video_size, audio_size = size_matches[-1]  # 使用最后一个匹配结果
        analysis['details'] = analysis.get('details', {})
        analysis['details']['video_size'] = f"{video_size}kB"
        analysis['details']['audio_size'] = f"{audio_size}kB"
    
    # 提取fps信息
    fps_match = re.search(r"(\d+\.?\d*) fps", output)
    if fps_match:
        analysis['details'] = analysis.get('details', {})
        analysis['details']['fps'] = f"{fps_match.group(1)}"
    
    # 查找总体概述
    summary_match = re.search(r"video:(\d+)kB audio:(\d+)kB subtitle:(\d+)kB other streams:(\d+)kB global headers:(\d+)kB muxing overhead: ([\d\.]+)%", output)
    if summary_match:
        analysis['details'] = analysis.get('details', {})
        analysis['details']['muxing_overhead'] = f"{summary_match.group(6)}%"
    
    
    return analysis

def analyze_failed_ffmpeg(error, output, exit_code):
    """分析失败的FFmpeg命令输出"""
    # 合并错误和输出信息进行分析
    combined_output = error + "\n" + output
    
    # 默认错误分析
    analysis = {
        'type': 'error',
        'message': '命令执行失败',
        'details': f'退出代码: {exit_code}'
    }
    
    # 检查常见错误类型
    if "No such file or directory" in combined_output:
        file_path = extract_file_path(combined_output)
        analysis['message'] = '文件不存在'
        analysis['details'] = f'找不到文件: {file_path}'
        analysis['solution'] = '请检查文件路径是否正确，确保文件存在'
        
    elif "Invalid data found when processing input" in combined_output:
        analysis['message'] = '无效的输入文件'
        analysis['details'] = '文件格式不正确或已损坏'
        analysis['solution'] = '请检查输入文件是否为有效的媒体文件'
        
    elif "Unknown encoder" in combined_output:
        codec = extract_codec_name(combined_output)
        analysis['message'] = '未知的编码器'
        analysis['details'] = f'编码器 {codec} 不可用'
        analysis['solution'] = '请安装相应的编解码器或使用其他可用的编码器'
        
    elif "Permission denied" in combined_output:
        analysis['message'] = '权限被拒绝'
        analysis['details'] = '无法读取输入文件或写入输出文件'
        analysis['solution'] = '请检查文件权限，或以管理员身份运行命令'
        
    elif "Output file is empty" in combined_output:
        analysis['message'] = '输出文件为空'
        analysis['details'] = '处理后未生成有效内容'
        analysis['solution'] = '请检查输入参数和文件格式是否正确'
        
    elif "Invalid argument" in combined_output:
        param = extract_invalid_parameter(combined_output)
        analysis['message'] = '无效的参数'
        analysis['details'] = f'参数错误: {param}'
        analysis['solution'] = '请检查命令参数是否正确'
    
    elif "Unrecognized option" in combined_output:
        option = extract_unrecognized_option(combined_output)
        analysis['message'] = '无法识别的选项'
        analysis['details'] = f'无效选项: {option}'
        analysis['solution'] = '请检查命令选项是否正确拼写，或查阅FFmpeg文档'
    
    return analysis

def extract_file_path(text):
    """从错误信息中提取文件路径"""
    match = re.search(r"No such file or directory\s*['\"](.*?)['\"]", text)
    if match:
        return match.group(1)
    
    match = re.search(r"No such file or directory:\s*(.*?)(\s|$)", text)
    if match:
        return match.group(1)
    
    return "未能识别文件路径"

def extract_codec_name(text):
    """从错误信息中提取编解码器名称"""
    match = re.search(r"Unknown encoder\s*['\"](.*?)['\"]", text)
    if match:
        return match.group(1)
    return "未知编解码器"

def extract_invalid_parameter(text):
    """从错误信息中提取无效参数"""
    match = re.search(r"Invalid argument\s*['\"](.*?)['\"]", text)
    if match:
        return match.group(1)
    return "未能识别的无效参数"

def extract_unrecognized_option(text):
    """从错误信息中提取无法识别的选项"""
    match = re.search(r"Unrecognized option\s*['\"](.*?)['\"]", text)
    if match:
        return match.group(1)
    return "未能识别的选项"


if __name__ == "__main__":
    # 使用原始字符串r前缀或双反斜杠避免Unicode转义错误
    out = f"""
[mov,mp4,m4a,3gp,3g2,mj2 @ 000001b10ad4bbc0] Unknown cover type: 0x1.
Input #0, mov,mp4,m4a,3gp,3g2,mj2, from 'D:\\AI\\Comfyui_Nvidia\\input\\a.mp4':
  Metadata:
    major_brand     : isom
    minor_version   : 512
    compatible_brands: isomiso2avc1mp41
    creation_time   : 2024-07-09T13:03:01.000000Z
    Hw              : 1
    bitrate         : 12000000
    maxrate         : 0
    te_is_reencode  : 1
    encoder         : Lavf58.76.100
  Duration: 00:00:40.82, start: 0.000000, bitrate: 9988 kb/s
  Stream #0:0[0x1](und): Video: h264 (High) (avc1 / 0x31637661), yuv420p(tv, bt709, progressive), 1080x1920 [SAR 1:1 DAR 9:16], 9792 kb/s, 30 fps, 30 tbr, 30 tbn (default)
      Metadata:
        creation_time   : 2024-07-09T13:03:01.000000Z
        handler_name    : VideoHandler
        vendor_id       : [0][0][0][0]
  Stream #0:1[0x2](und): Audio: aac (LC) (mp4a / 0x6134706D), 44100 Hz, stereo, fltp, 194 kb/s (default)
      Metadata:
        creation_time   : 2024-07-09T13:03:01.000000Z
        handler_name    : SoundHandler
        vendor_id       : [0][0][0][0]
Input #1, mov,mp4,m4a,3gp,3g2,mj2, from 'D:\\AI\\Comfyui_Nvidia\\input\\b.mp4':
  Metadata:
    major_brand     : isom
    minor_version   : 512
    compatible_brands: isomiso2avc1mp41
    comment         : vid:v0300fg10000ci36ru3c77u5pp0p78gg
    encoder         : Lavf58.76.100
  Duration: 00:00:40.80, start: 0.000000, bitrate: 2428 kb/s
  Stream #1:0[0x1](und): Audio: aac (LC) (mp4a / 0x6134706D), 44100 Hz, stereo, fltp, 128 kb/s (default)
      Metadata:
        handler_name    : SoundHandler
        vendor_id       : [0][0][0][0]
  Stream #1:1[0x2](und): Video: h264 (High) (avc1 / 0x31637661), yuv420p(tv, bt709, progressive), 720x1280 [SAR 1:1 DAR 9:16], 2291 kb/s, 30 fps, 30 tbr, 15360 tbn (default)
      Metadata:
        handler_name    : VideoHandler
        vendor_id       : [0][0][0][0]
Stream mapping:
  Stream #0:0 (h264) -> overlay
  Stream #1:1 (h264) -> format:default
  overlay:default -> Stream #0:0 (h264_nvenc)
  Stream #0:1 -> #0:1 (aac (native) -> aac (native))
Press [q] to stop, [?] for help
Output #0, mp4, to 'D:\\AI\\Comfyui_Nvidia\\input\\ab.mp4':
  Metadata:
    major_brand     : isom
    minor_version   : 512
    compatible_brands: isomiso2avc1mp41
    te_is_reencode  : 1
    Hw              : 1
    bitrate         : 12000000
    maxrate         : 0
    encoder         : Lavf61.7.100
  Stream #0:0: Video: h264 (Main) (avc1 / 0x31637661), yuv420p(tv, bt709, progressive), 1080x1920 [SAR 1:1 DAR 9:16], q=2-31, 2000 kb/s, 30 fps, 15360 tbn
      Metadata:
        encoder         : Lavc61.19.100 h264_nvenc
      Side data:
        cpb: bitrate max/min/avg: 0/0/2000000 buffer size: 4000000 vbv_delay: N/A
  Stream #0:1(und): Audio: aac (LC) (mp4a / 0x6134706D), 44100 Hz, stereo, fltp, 128 kb/s (default)
      Metadata:
        creation_time   : 2024-07-09T13:03:01.000000Z
        handler_name    : SoundHandler
        vendor_id       : [0][0][0][0]
        encoder         : Lavc61.19.100 aac
[out#0/mp4 @ 000001b10ad53380] video:10437KiB audio:641KiB subtitle:0KiB other streams:0KiB global headers:0KiB muxing overhead: 0.317800%
frame= 1224 fps=378 q=37.0 Lsize=   11113KiB time=00:00:40.80 bitrate=2231.2kbits/s speed=12.6x
[aac @ 000001b10ade2100] Qavg: 768.345
"""
   
    cmd = r'ffmpeg -i D:\\AI\\Comfyui_Nvidia\\input\\a.mp4 -i D:\\AI\\Comfyui_Nvidia\\input\\b.mp4 -filter_complex  [1:v]format=yuva420p,fade=t=out:st=0:d=0:alpha=1[bg];[0:v][bg]overlay=0:0  -y -c:v h264_nvenc -preset fast D:\\AI\\Comfyui_Nvidia\\input\\ab.mp4'
    # 或使用双反斜杠: cmd = f'ffmpeg -i "C:\\Users\\Administrator\\Desktop\\test.mp4" -vf "scale=iw:ih+100" -c:v libx264 -c:a copy "C:\\Users\\Administrator\\Desktop\\test_output.mp4"'
    
    # 使用修改后的cmd_win_ffmpeg函数
    result = cmd_win_ffmpeg(cmd, shell=False)
    print(result)

