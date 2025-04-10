import sys
import re
import subprocess
from pathlib import Path

# 添加项目根目录到系统路径，以便导入其他模块
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from ai_services.utils.cmd_win import run_cmd, get_system_info, get_software_version

def get_nvidia_gpu_info():
    """
    使用ComfyUI相关的方法获取GPU信息
    
    Returns:
        tuple: (gpu_info, driver_version, cuda_version, vram_total)
    """
    try:
        # 尝试导入torch，这是ComfyUI使用的库
        import torch
        
        # 检查CUDA是否可用
        if not torch.cuda.is_available():
            print("CUDA不可用，回退到系统方法获取GPU信息")
            return get_gpu_info_fallback()
        
        # 获取CUDA版本
        cuda_version = torch.version.cuda if hasattr(torch.version, 'cuda') else "未知"
        
        # 获取设备数量
        device_count = torch.cuda.device_count()
        if device_count == 0:
            print("未检测到CUDA设备，回退到系统方法获取GPU信息")
            return get_gpu_info_fallback()
        
        # 收集所有GPU信息
        gpu_models = []
        total_vram = 0
        
        for i in range(device_count):
            # 获取GPU名称
            gpu_name = torch.cuda.get_device_name(i)
            gpu_models.append(gpu_name)
            
            # 获取GPU显存
            try:
                # 以GB为单位显示总显存
                props = torch.cuda.get_device_properties(i)
                vram = props.total_memory / (1024**3)  # 转换为GB
                total_vram += vram
            except:
                pass
        
        # 拼接GPU型号信息
        gpu_info = ", ".join(gpu_models)
        
        # 尝试获取驱动版本
        driver_version = "未知"
        try:
            # 尝试使用nvidia-smi获取驱动版本
            result = subprocess.run(['nvidia-smi', '--query-gpu=driver_version', '--format=csv,noheader'], 
                                   capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and result.stdout.strip():
                driver_versions = [v.strip() for v in result.stdout.strip().split('\n') if v.strip()]
                if driver_versions:
                    # 使用第一个设备的驱动版本
                    driver_version = driver_versions[0]
        except:
            pass
        
        return gpu_info, driver_version, cuda_version, total_vram
        
    except ImportError:
        print("无法导入torch，回退到系统方法获取GPU信息")
        return get_gpu_info_fallback() + ("未知", 0)
    except Exception as e:
        print(f"使用ComfyUI方法获取GPU信息失败: {str(e)}")
        return get_gpu_info_fallback() + ("未知", 0)

def get_nvidia_driver_info():
    """
    使用nvidia-smi获取GPU驱动版本和GPU信息
    
    Returns:
        tuple: (gpu_info, driver_version)
    """
    try:
        # 使用subprocess直接执行nvidia-smi命令
        result = subprocess.run(['nvidia-smi'], capture_output=True, text=True, timeout=5)
        
        if result.returncode == 0:
            output = result.stdout
            
            # 从输出中提取驱动版本
            driver_match = re.search(r'Driver Version: (\d+\.\d+\.\d+)', output)
            driver_version = driver_match.group(1) if driver_match else "未知"
            
            # 从输出中提取GPU型号
            gpu_matches = re.findall(r'\| (NVIDIA [A-Za-z0-9\s]+)(?:\s+\d+)?\s+\d+', output)
            if gpu_matches:
                gpu_info = ", ".join(gpu_matches)
            else:
                # 尝试从更简单的模式匹配
                gpu_matches = re.findall(r'(NVIDIA [A-Za-z0-9\s]+)', output)
                gpu_info = ", ".join(gpu_matches) if gpu_matches else "未检测到NVIDIA GPU"
            
            return gpu_info, driver_version
        else:
            # 如果nvidia-smi命令失败，回退到wmic方法
            return get_gpu_info_fallback()
    except Exception as e:
        print(f"获取NVIDIA GPU信息失败: {str(e)}")
        # 出现异常时回退到wmic方法
        return get_gpu_info_fallback()

def get_gpu_info_fallback():
    """
    获取GPU信息的回退方法，使用wmic命令
    
    Returns:
        tuple: (gpu_info, driver_version)
    """
    system_info = get_system_info()
    
    gpu_info = "未检测到GPU"
    driver_version = "未知"
    
    if 'gpus' in system_info and system_info['gpus'] != "未知" and len(system_info['gpus']) > 0:
        gpu_models = []
        
        for gpu in system_info['gpus']:
            if 'Name' in gpu:
                gpu_models.append(gpu['Name'])
            if 'DriverVersion' in gpu and driver_version == "未知":
                driver_version = gpu['DriverVersion']
        
        if gpu_models:
            gpu_info = ", ".join(gpu_models)
    
    return gpu_info, driver_version

def get_ffmpeg_version():
    """
    获取FFmpeg版本信息
    
    Returns:
        tuple: (version_string, version_number, has_cuda)
    """
    try:
        # 使用subprocess直接执行ffmpeg -version命令
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
        
        if result.returncode == 0:
            output = result.stdout
            
            # 提取版本行
            version_line = output.split('\n')[0]
            # 尝试提取版本号
            version_match = re.search(r'ffmpeg version (\S+)', version_line)
            version_number = version_match.group(1) if version_match else "未知"
            
            # 检查是否支持CUDA
            cuda_match = re.search(r'--enable-cuda|--enable-nvenc|--enable-cuvid|--enable-ffnvcodec', output)
            has_cuda = cuda_match is not None
            
            return version_line, version_number, has_cuda
        else:
            return "FFmpeg未安装或未找到", "未知", False
    except Exception as e:
        print(f"获取FFmpeg版本失败: {str(e)}")
        return f"获取FFmpeg版本失败: {str(e)}", "未知", False

def run_process_ffmpeg_command():
    """
    处理获取系统信息和FFmpeg相关信息的命令
    
    Returns:
        str: 格式化的结果
    """
    # 获取系统信息
    system_info = get_system_info()
    
    # 先尝试使用ComfyUI方法获取GPU信息
    try:
        gpu_info, driver_version, cuda_version, vram_total = get_nvidia_gpu_info()
    except Exception as e:
        print(f"ComfyUI方法获取GPU信息失败: {e}")
        # 如果失败，回退到nvidia-smi方法
        gpu_info, driver_version = get_nvidia_driver_info()
        cuda_version = "未知"
        vram_total = 0
    
    # 获取FFmpeg版本
    ffmpeg_version_line, ffmpeg_version, has_cuda = get_ffmpeg_version()
    
    # 构建返回的信息
    result = {
        "系统信息": {
            "Windows版本": system_info.get('windows_version', "未知"),
            "CPU": system_info.get('cpu', "未知"),
            "内存": system_info.get('memory', "未知")
        },
        "GPU信息": {
            "GPU型号": gpu_info,
            "驱动版本": driver_version,
            "CUDA版本": cuda_version
        }
    }
    
    # 如果有显存信息，添加到GPU信息中
    if vram_total > 0:
        result["GPU信息"]["显存"] = f"{vram_total:.2f} GB"
    
    # 添加FFmpeg信息
    result["FFmpeg信息"] = {
        "版本": ffmpeg_version_line,
        "版本号": ffmpeg_version,
        "支持CUDA": "是" if has_cuda else "否"
    }
    
    # 格式化输出
    output_text = "# 系统和媒体信息\n\n"
    
    for section, data in result.items():
        output_text += f"## {section}：\n"
        
        if isinstance(data, dict):
            for key, value in data.items():
                output_text += f"- **{key}**: {value}\n"
        else:
            output_text += f"{data}\n"
        
        output_text += "\n"
    
    return output_text

def process_ffmpeg_command(query, **kwargs):
    """
    处理FFmpeg命令
    
    Args:
        query: 用户查询
        **kwargs: 其他参数
        
    Returns:
        str: 处理结果
    """
    # 这是一个更完整的函数实现，用于处理FFmpeg相关的命令
    if "获取系统信息" in query or "显示信息" in query:
        return run_process_ffmpeg_command()
    
    # 检测ffmpeg是否安装
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
        if result.returncode != 0:
            return "错误: FFmpeg未安装或无法找到。请安装FFmpeg后再试。"
    except Exception:
        return "错误: FFmpeg未安装或无法找到。请安装FFmpeg后再试。"
    
    # 提取ffmpeg命令
    ffmpeg_cmd = None
    if "ffmpeg " in query:
        cmd_start = query.find("ffmpeg ")
        ffmpeg_cmd = query[cmd_start:].strip()
    
    if ffmpeg_cmd:
        # 执行ffmpeg命令
        try:
            # 将命令分割为参数列表
            cmd_parts = ffmpeg_cmd.split()
            result = subprocess.run(cmd_parts, capture_output=True, text=True, timeout=600)  # 10分钟超时
            
            if result.returncode == 0:
                return f"FFmpeg命令执行成功:\n\n```\n{result.stdout}\n```"
            else:
                return f"FFmpeg命令执行失败:\n\n```\n{result.stderr}\n```"
        except subprocess.TimeoutExpired:
            return "FFmpeg命令执行超时(10分钟)。"
        except Exception as e:
            return f"执行FFmpeg命令时出错: {str(e)}"
    else:
        # 如果没有明确的ffmpeg命令，返回系统和FFmpeg信息
        return run_process_ffmpeg_command()

