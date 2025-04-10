import subprocess
import threading

def run_cmd(cmd, cwd=None, shell=True, timeout=None, encoding='utf-8'):
    """
    执行CMD命令，并实时输出执行进度
    
    Args:
        cmd: 要执行的命令
        cwd: 执行命令的工作目录
        shell: 是否使用shell执行
        timeout: 超时时间（秒）
        encoding: 输出编码
        
    Returns:
        dict: 包含执行结果的字典，格式为 {'success': bool, 'output': str, 'error': str, 'exit_code': int}
    """
    #print(f"执行命令: {cmd}")
    if cwd:
        print(f"在目录: {cwd}")
    
    try:
        # 创建进程
        process = subprocess.Popen(
            cmd,
            cwd=cwd,
            shell=shell,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            encoding=encoding,
            errors='replace'
        )
        
        # 输出收集
        stdout_data = []
        stderr_data = []
        
        # 创建读取输出的线程
        def read_output(stream, data_list):
            for line in iter(stream.readline, ''):
                print(line.rstrip())  # 显示进度
                data_list.append(line)
                
        # 启动读取线程
        stdout_thread = threading.Thread(target=read_output, args=(process.stdout, stdout_data))
        stderr_thread = threading.Thread(target=read_output, args=(process.stderr, stderr_data))
        stdout_thread.daemon = True
        stderr_thread.daemon = True
        stdout_thread.start()
        stderr_thread.start()
        
        # 等待命令完成
        exit_code = process.wait(timeout=timeout)
        
        # 等待线程完成
        stdout_thread.join(1)
        stderr_thread.join(1)
        
        # 处理可能没被线程读完的输出
        stdout_remaining = process.stdout.read()
        stderr_remaining = process.stderr.read()
        
        if stdout_remaining:
            print(stdout_remaining.rstrip())
            stdout_data.append(stdout_remaining)
        
        if stderr_remaining:
            print(stderr_remaining.rstrip())
            stderr_data.append(stderr_remaining)
        
        stdout_text = ''.join(stdout_data)
        stderr_text = ''.join(stderr_data)
        
        result = {
            'success': exit_code == 0,
            'output': stdout_text,
            'error': stderr_text,
            'exit_code': exit_code
        }
        
        return result
        
    except subprocess.TimeoutExpired:
        print(f"命令执行超时: {cmd}")
        return {
            'success': False,
            'output': '',
            'error': '命令执行超时',
            'exit_code': -1
        }
    except Exception as e:
        print(f"执行命令时出错: {str(e)}")
        return {
            'success': False,
            'output': '',
            'error': str(e),
            'exit_code': -1
        }

def run_cmd_with_subprocess(cmd, cwd=None, shell=True, timeout=None, encoding='utf-8', capture_output=True):
    """
    使用subprocess.run执行命令，适用于简单命令
    
    Args:
        cmd: 要执行的命令
        cwd: 执行命令的工作目录
        shell: 是否使用shell执行
        timeout: 超时时间（秒）
        encoding: 输出编码
        capture_output: 是否捕获输出
        
    Returns:
        dict: 包含执行结果的字典
    """
    #print(f"执行命令 (subprocess): {cmd}")
    if cwd:
        print(f"在目录: {cwd}")
    
    try:
        #print(f"使用subprocess.run执行命令: {cmd}")
        result = subprocess.run(
            cmd,
            cwd=cwd,
            shell=shell,
            capture_output=capture_output,
            text=True,
            encoding=encoding,
            errors='replace',
            timeout=timeout,
            check=False
        )
        
        # 输出命令的执行结果
        #if result.stdout:
            #print(result.stdout.rstrip())
            
        #if result.stderr:
            #print(result.stderr.rstrip())
        
        # 构建结果字典
        return {
            'success': result.returncode == 0,
            'output': result.stdout if result.stdout else '',
            'error': result.stderr if result.stderr else '',
            'exit_code': result.returncode
        }
        
    except subprocess.TimeoutExpired:
        print(f"命令执行超时: {cmd}")
        return {
            'success': False,
            'output': '',
            'error': f'命令执行超时(超过{timeout}秒)',
            'exit_code': -1
        }
    except Exception as e:
        print(f"执行命令时出错: {str(e)}")
        return {
            'success': False,
            'output': '',
            'error': str(e),
            'exit_code': -1
        }

def run_git_cmd(git_cmd, repo_path=None, timeout=None):
    """
    执行Git命令
    
    Args:
        git_cmd: Git命令（不包含'git'前缀）
        repo_path: Git仓库路径
        timeout: 超时时间（秒）
        
    Returns:
        dict: 包含执行结果的字典
    """
    cmd = f"git {git_cmd}"
    return run_cmd(cmd, cwd=repo_path, timeout=timeout)

def git_clone(repo_url, target_dir=None, branch=None, depth=None, timeout=None):
    """
    克隆Git仓库
    
    Args:
        repo_url: 仓库URL
        target_dir: 目标目录
        branch: 指定分支
        depth: 克隆深度
        timeout: 超时时间（秒）
        
    Returns:
        dict: 包含执行结果的字典
    """
    cmd = f"git clone {repo_url}"
    
    if branch:
        cmd += f" -b {branch}"
    
    if depth:
        cmd += f" --depth {depth}"
    
    if target_dir:
        cmd += f" {target_dir}"
    
    return run_cmd(cmd, timeout=timeout)

def git_pull(repo_path=None, timeout=None):
    """
    拉取Git仓库最新代码
    
    Args:
        repo_path: 仓库路径
        timeout: 超时时间（秒）
        
    Returns:
        dict: 包含执行结果的字典
    """
    return run_git_cmd("pull", repo_path=repo_path, timeout=timeout)

def git_status(repo_path=None):
    """
    获取Git仓库状态
    
    Args:
        repo_path: 仓库路径
        
    Returns:
        dict: 包含执行结果的字典
    """
    return run_git_cmd("status", repo_path=repo_path)

def get_system_info():
    """
    获取系统信息
    
    Returns:
        dict: 系统信息字典
    """
    info = {}
    
    # 获取Windows版本
    try:
        result = run_cmd("ver")
        if result['success']:
            info['windows_version'] = result['output'].strip()
    except:
        info['windows_version'] = "未知"
    
    # 获取CPU信息
    try:
        result = run_cmd("wmic cpu get name /value")
        if result['success']:
            cpu_info = result['output'].strip()
            if "Name=" in cpu_info:
                info['cpu'] = cpu_info.split("Name=")[1].strip()
            else:
                info['cpu'] = cpu_info
    except:
        info['cpu'] = "未知"
    
    # 获取内存信息
    try:
        result = run_cmd("wmic ComputerSystem get TotalPhysicalMemory /value")
        if result['success']:
            mem_bytes = result['output'].strip().split("=")[1].strip()
            info['memory'] = f"{int(int(mem_bytes) / (1024**3))} GB"
    except:
        info['memory'] = "未知"
    
    # 获取GPU信息
    try:
        result = run_cmd("wmic path win32_VideoController get name, DriverVersion /value")
        if result['success']:
            output = result['output']
            gpu_parts = output.strip().split("\n\n")
            gpus = []
            
            for part in gpu_parts:
                if not part.strip():
                    continue
                    
                gpu_info = {}
                lines = part.strip().split("\n")
                
                for line in lines:
                    if "=" in line:
                        key, value = line.split("=", 1)
                        gpu_info[key.strip()] = value.strip()
                
                if gpu_info:
                    gpus.append(gpu_info)
            
            info['gpus'] = gpus
    except:
        info['gpus'] = "未知"
    
    return info

def get_software_version(cmd, version_arg="--version"):
    """
    获取软件版本信息
    
    Args:
        cmd: 软件命令
        version_arg: 版本参数
        
    Returns:
        str: 版本信息
    """
    try:
        result = run_cmd(f"{cmd} {version_arg}")
        if result['success']:
            return result['output'].strip()
        else:
            return f"执行错误: {result['error']}"
    except:
        return "未知"

