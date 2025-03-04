import ctypes
import sys
import logging
import os
import subprocess

def is_admin():
    """检查当前是否具有管理员权限"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin(program, *args):
    """以管理员权限重新运行指定程序"""
    try:
        if not is_admin():
            # 准备参数
            arguments = list(args)
            script = program
            quoted_args = ' '.join(['"%s"' % arg for arg in arguments])
            
            # 构建命令
            cmd = f'"{sys.executable}" "{script}" {quoted_args}'
            
            # 使用 ShellExecute 以管理员权限启动
            ctypes.windll.shell32.ShellExecuteW(
                None,  # hwnd
                "runas",  # operation
                sys.executable,  # file
                cmd,  # parameters
                None,  # directory
                1     # show command
            )
            return True
    except Exception as e:
        logging.error(f"请求管理员权限失败: {e}")
        return False
