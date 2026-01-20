#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time
import subprocess
import requests
import psutil
import ctypes
from typing import Optional

# 检测平台并导入相应的键盘输入模块
try:
    if os.name == 'nt':  # Windows
        import msvcrt
    else:  # Linux/Mac
        import termios
        import tty
except ImportError:
    pass

class MihomoManager:
    def __init__(self):
        self.exe_name = "mihomo.exe"
        self.config_dir = "."  # 当前目录
        self.api_url = "http://127.0.0.1:9090"
        self.secret = "123456"
        
    def is_running(self) -> bool:
        """检查 Mihomo 是否正在运行"""
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] and self.exe_name.lower() in proc.info['name'].lower():
                return True
        return False
    
    def start_mihomo(self):
        """启动 Mihomo - 使用独立进程"""
        if self.is_running():
            print("❌ Mihomo 已经在运行中")
            return False
        
        try:
            # 使用独立进程启动 Mihomo，确保它不会随 Python 脚本退出而终止
            if os.name == 'nt':  # Windows
                # 在 Windows 上使用 CREATE_NEW_PROCESS_GROUP 和 DETACHED_PROCESS
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = 0  # 隐藏窗口
                
                subprocess.Popen(
                    [self.exe_name, "-d", self.config_dir],
                    cwd=self.config_dir,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    stdin=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS,
                    startupinfo=startupinfo
                )
            else:  # Unix/Linux
                # 在 Unix/Linux 上使用 preexec_fn=os.setpgrp
                subprocess.Popen(
                    [self.exe_name, "-d", self.config_dir],
                    cwd=self.config_dir,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    stdin=subprocess.DEVNULL,
                    preexec_fn=os.setpgrp
                )
                
            print("✅ Mihomo 启动命令已执行")
            
            # 等待几秒检查是否成功启动
            time.sleep(3)
            if self.is_running():
                print("✅ Mihomo 启动成功")
                return True
            else:
                print("⚠️  Mihomo 可能启动失败，请检查日志")
                return False
                
        except Exception as e:
            print(f"❌ 启动失败: {e}")
            return False
    
    def stop_mihomo(self):
        """停止 Mihomo"""
        if not self.is_running():
            print("❌ Mihomo 未在运行")
            return False
        
        try:
            for proc in psutil.process_iter(['name', 'pid']):
                if proc.info['name'] and self.exe_name.lower() in proc.info['name'].lower():
                    proc.terminate()
                    proc.wait(timeout=10)  # 等待进程结束
                    print(f"✅ 已停止 Mihomo (PID: {proc.info['pid']})")
                    return True
        except psutil.TimeoutExpired:
            print("⚠️  正常终止超时，尝试强制终止...")
            for proc in psutil.process_iter(['name', 'pid']):
                if proc.info['name'] and self.exe_name.lower() in proc.info['name'].lower():
                    proc.kill()
                    print(f"✅ 已强制停止 Mihomo (PID: {proc.info['pid']})")
                    return True
        except Exception as e:
            print(f"❌ 停止失败: {e}")
            return False
        
        return True
    
    def restart_mihomo(self):
        """重启 Mihomo"""
        print("🔄 正在重启 Mihomo...")
        if self.is_running():
            if self.stop_mihomo():
                time.sleep(2)  # 等待进程完全退出
        else:
            print("ℹ️  Mihomo 未运行，直接启动")
        
        return self.start_mihomo()
    
    def reload_config(self):
        """重新加载配置"""
        if not self.is_running():
            print("❌ Mihomo 未运行，无法重新加载配置")
            return False
        
        try:
            headers = {'Authorization': f'Bearer {self.secret}'}
            response = requests.put(f"{self.api_url}/configs?reload=true", headers=headers, timeout=10)
            
            if response.status_code == 204:
                print("✅ 配置重新加载成功")
                return True
            else:
                print(f"❌ 重新加载失败，状态码: {response.status_code}")
                return False
                
        except requests.exceptions.ConnectionError:
            print("❌ 无法连接到 Mihomo API，请检查服务是否正常运行")
            return False
        except requests.exceptions.Timeout:
            print("❌ 连接超时")
            return False
        except Exception as e:
            print(f"❌ 重新加载失败: {e}")
            return False
    
    def show_status(self):
        """显示状态信息"""
        if self.is_running():
            print("🟢 Mihomo 正在运行")
            
            # 尝试获取更多状态信息
            try:
                headers = {'Authorization': f'Bearer {self.secret}'}
                response = requests.get(f"{self.api_url}/version", headers=headers, timeout=5)
                if response.status_code == 200:
                    version_info = response.json()
                    print(f"   版本: {version_info.get('version', '未知')}")
            except:
                print("   版本: 无法获取版本信息")
                
        else:
            print("🔴 Mihomo 未运行")
    
    def check_exe_exists(self) -> bool:
        """检查可执行文件是否存在"""
        if os.path.exists(self.exe_name):
            return True
        
        # 在当前目录搜索
        for file in os.listdir("."):
            if "mihomo" in file.lower() and file.endswith(".exe"):
                self.exe_name = file
                print(f"ℹ️  使用找到的可执行文件: {self.exe_name}")
                return True
        
        print(f"❌ 找不到 Mihomo 可执行文件")
        print(f"   请在当前目录放置 {self.exe_name} 或其他包含 'mihomo' 的 .exe 文件")
        return False
    
    def is_admin(self):
        """检查是否以管理员权限运行"""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
    
    def enable_autostart(self):
        """启用开机自启（计划任务方式）"""
        if not self.is_admin():
            print("❌ 请以管理员身份运行此脚本来设置开机自启！")
            return False
        
        mihomo_path = os.path.abspath(self.exe_name)
        mihomo_dir = os.path.abspath(self.config_dir)
        
        if not os.path.exists(mihomo_path):
            print(f"❌ 找不到 Mihomo: {mihomo_path}")
            return False
        
        try:
            # PowerShell 命令创建计划任务
            ps_command = f'''
$Action = New-ScheduledTaskAction -Execute "{mihomo_path}" -Argument "-d {mihomo_dir}" -WorkingDirectory "{mihomo_dir}"
$Trigger = New-ScheduledTaskTrigger -AtStartup -RandomDelay "00:00:30"
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RestartCount 3 -RestartInterval "00:01:00"
$Principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
Register-ScheduledTask -TaskName "MihomoProxy" -Action $Action -Trigger $Trigger -Settings $Settings -Principal $Principal -Description "Mihomo Proxy Service AutoStart"
'''
            
            # 执行 PowerShell 命令
            result = subprocess.run([
                "powershell", "-ExecutionPolicy", "Bypass", "-Command", ps_command
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print("✅ 计划任务创建成功！")
                print("Mihomo 将在系统启动时自动运行")
                return True
            else:
                print(f"❌ 创建失败: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("❌ 执行超时")
            return False
        except Exception as e:
            print(f"❌ 执行失败: {e}")
            return False
    
    def disable_autostart(self):
        """禁用开机自启"""
        if not self.is_admin():
            print("❌ 请以管理员身份运行此脚本来移除开机自启！")
            return False
        
        try:
            result = subprocess.run([
                "powershell", "-ExecutionPolicy", "Bypass", "-Command",
                "Unregister-ScheduledTask -TaskName 'MihomoProxy' -Confirm:$false"
            ], capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0:
                print("✅ 开机自启已禁用")
                return True
            else:
                # 如果任务不存在，也算成功
                if "找不到" in result.stderr or "not found" in result.stderr.lower():
                    print("ℹ️  未找到 Mihomo 开机自启任务")
                    return True
                else:
                    print(f"❌ 禁用失败: {result.stderr}")
                    return False
                    
        except subprocess.TimeoutExpired:
            print("❌ 执行超时")
            return False
        except Exception as e:
            print(f"❌ 执行失败: {e}")
            return False
    
    def check_autostart_status(self):
        """检查开机自启状态"""
        try:
            result = subprocess.run([
                "powershell", "-ExecutionPolicy", "Bypass", "-Command",
                "Get-ScheduledTask -TaskName 'MihomoProxy' -ErrorAction SilentlyContinue"
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0 and "MihomoProxy" in result.stdout:
                print("🟢 Mihomo 开机自启已启用")
                return True
            else:
                print("🔴 Mihomo 开机自启未设置")
                return False
                
        except Exception as e:
            print(f"❌ 检查失败: {e}")
            return False

def clear_screen():
    """清屏"""
    os.system('cls' if os.name == 'nt' else 'clear')

def show_menu():
    """显示菜单"""
    print("=" * 50)
    print("           Mihomo 管理工具")
    print("=" * 50)
    print("1. 启动 Mihomo")
    print("2. 停止 Mihomo")
    print("3. 重启 Mihomo")
    print("4. 检查状态")
    print("5. 重新加载配置")
    print("6. 设置开机自启")
    print("7. 移除开机自启")
    print("8. 检查自启状态")
    print("-" * 50)
    print("按 ESC 键或直接按回车键退出程序")
    print("-" * 50)

def exit_program():
    """退出程序"""
    print("👋 再见！")
    time.sleep(1)  # 等待1秒让用户看到消息
    sys.exit(0)

def get_user_input(prompt="请选择操作 (1-8): "):
    """获取用户输入，支持 ESC 键检测"""
    try:
        if os.name == 'nt':  # Windows
            print(prompt, end='', flush=True)
            # 检测单个按键输入
            while True:
                if msvcrt.kbhit():
                    key = msvcrt.getch()
                    if key == b'\x1b':  # ESC 键
                        print("ESC")
                        return 'esc'
                    elif key == b'\r':  # 回车键
                        print()
                        return ''
                    elif key in [b'1', b'2', b'3', b'4', b'5', b'6', b'7', b'8']:
                        print(key.decode())
                        return key.decode()
                    elif key == b'\x08':  # 退格键
                        # 忽略退格键，因为我们只接受单字符输入
                        pass
                    else:
                        # 其他按键，忽略
                        pass
        else:  # Linux/Mac
            # 保存终端设置
            old_settings = termios.tcgetattr(sys.stdin)
            try:
                tty.setraw(sys.stdin.fileno())
                ch = sys.stdin.read(1)
                if ch == '\x1b':  # ESC 键
                    return 'esc'
                elif ch == '\r' or ch == '\n':  # 回车键
                    return ''
                elif ch in ['1', '2', '3', '4', '5', '6', '7', '8']:
                    print(ch)
                    return ch
                else:
                    return ch
            finally:
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
    except (ImportError, Exception):
        # 如果平台特定的键盘输入不可用，回退到标准输入
        try:
            user_input = input(prompt).strip()
            if user_input.lower() == 'esc' or user_input == '':
                return 'esc'
            return user_input
        except (KeyboardInterrupt, EOFError):
            return 'esc'

def main():
    manager = MihomoManager()
    
    # 检查可执行文件是否存在
    if not manager.check_exe_exists():
        input("按回车键退出...")
        return
    
    while True:
        clear_screen()
        show_menu()
        manager.show_status()
        
        try:
            choice = get_user_input()
            
            if choice == 'esc' or choice == '':
                print("\n✅ 管理工具已关闭，Mihomo 服务继续运行")
                time.sleep(1)
                exit_program()
            elif choice == "1":
                if manager.start_mihomo():
                    print("\n✅ Mihomo 已启动")
                else:
                    print("\n❌ Mihomo 启动失败")
                input("\n按回车键返回主菜单...")
                    
            elif choice == "2":
                if manager.stop_mihomo():
                    print("\n✅ Mihomo 已停止")
                else:
                    print("\n❌ Mihomo 停止失败")
                input("\n按回车键返回主菜单...")
                    
            elif choice == "3":
                if manager.restart_mihomo():
                    print("\n✅ Mihomo 已重启")
                else:
                    print("\n❌ Mihomo 重启失败")
                input("\n按回车键返回主菜单...")
                    
            elif choice == "4":
                manager.show_status()
                input("\n按回车键返回主菜单...")
                
            elif choice == "5":
                if manager.reload_config():
                    print("\n✅ 配置已重新加载")
                else:
                    print("\n❌ 配置重新加载失败")
                input("\n按回车键返回主菜单...")
            
            elif choice == "6":
                if manager.enable_autostart():
                    print("\n✅ 开机自启设置成功")
                else:
                    print("\n❌ 开机自启设置失败")
                input("\n按回车键返回主菜单...")
            
            elif choice == "7":
                if manager.disable_autostart():
                    print("\n✅ 开机自启已移除")
                else:
                    print("\n❌ 开机自启移除失败")
                input("\n按回车键返回主菜单...")
            
            elif choice == "8":
                manager.check_autostart_status()
                input("\n按回车键返回主菜单...")
                
            else:
                print("❌ 无效选择，请重新输入")
                input("\n按回车键继续...")
                
        except KeyboardInterrupt:
            print("\n👋 用户中断，再见！")
            time.sleep(1)
            sys.exit(0)
        except Exception as e:
            print(f"❌ 发生错误: {e}")
            input("\n按回车键继续...")

if __name__ == "__main__":
    # 如果提供了命令行参数，直接执行相应操作
    if len(sys.argv) > 1:
        manager = MihomoManager()
        manager.check_exe_exists()
        
        arg = sys.argv[1].lower()
        if arg in ["start", "1"]:
            if manager.start_mihomo():
                print("✅ Mihomo 已启动")
            else:
                print("❌ Mihomo 启动失败")
                
        elif arg in ["stop", "2"]:
            if manager.stop_mihomo():
                print("✅ Mihomo 已停止")
            else:
                print("❌ Mihomo 停止失败")
                
        elif arg in ["restart", "3"]:
            if manager.restart_mihomo():
                print("✅ Mihomo 已重启")
            else:
                print("❌ Mihomo 重启失败")
                
        elif arg in ["status", "4"]:
            manager.show_status()
            
        elif arg in ["reload", "5"]:
            if manager.reload_config():
                print("✅ 配置已重新加载")
            else:
                print("❌ 配置重新加载失败")
        
        elif arg in ["autostart-enable", "6"]:
            if manager.enable_autostart():
                print("✅ 开机自启设置成功")
            else:
                print("❌ 开机自启设置失败")
        
        elif arg in ["autostart-disable", "7"]:
            if manager.disable_autostart():
                print("✅ 开机自启已移除")
            else:
                print("❌ 开机自启移除失败")
        
        elif arg in ["autostart-status", "8"]:
            manager.check_autostart_status()
                
        else:
            print("用法: python mihomo_manager.py [start|stop|restart|status|reload|autostart-enable|autostart-disable|autostart-status]")
    else:
        main()