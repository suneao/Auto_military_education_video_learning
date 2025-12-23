#!/usr/bin/env python3
"""
视频学习自动化脚本 - 文本用户界面 (TUI)
修复版，包含完整的交互式菜单系统
"""

import asyncio
import json
import os
import sys
import time
from typing import Optional, Dict

# Windows控制台编码设置
if sys.platform == "win32":
    try:
        # 尝试设置控制台编码为UTF-8
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='ignore')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='ignore')
    except:
        pass

# 添加当前目录到Python路径，确保可以导入本地模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from video_auto_learner import VideoAutoLearner, login_with_fixed_screentype

class VideoLearnerTUI:
    """视频学习自动化TUI"""
    
    def __init__(self):
        self.learner = VideoAutoLearner(base_url="http://www.gaoxiaokaoshi.com")
        self.course_list_path = "考试平台_files/LibraryStudyList.html"
        
        # 尝试从配置文件加载账号密码
        credentials = self.learner.load_credentials_from_file("config.json")
        if credentials:
            self.username, self.password = credentials
            print(f"从配置文件加载账号: {self.username}")
        else:
            self.username = ""  # 用户需要在运行时输入
            self.password = ""  # 用户需要在运行时输入
        
    def clear_screen(self):
        """清屏"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def print_header(self, title: str):
        """打印标题"""
        self.clear_screen()
        print("=" * 60)
        print(f"视频学习自动化脚本 - {title}")
        print("=" * 60)
        print()
    
    def print_status(self):
        """显示当前状态"""
        print("\n" + "-" * 40)
        print("📊 当前状态")
        print("-" * 40)
        
        # 检查配置文件
        config_files = []
        if os.path.exists("config.json"):
            config_files.append("✅ config.json")
        else:
            config_files.append("❌ config.json (不存在)")
        
        # 检查课程列表文件
        if os.path.exists(self.course_list_path):
            course_status = f"✅ {self.course_list_path}"
        else:
            course_status = f"❌ {self.course_list_path} (不存在)"
        
        # 检查依赖
        try:
            import aiohttp
            import bs4
            deps_status = "✅ 依赖已安装"
        except ImportError:
            deps_status = "❌ 依赖未安装"
        
        print(f"配置文件: {', '.join(config_files)}")
        print(f"课程列表: {course_status}")
        print(f"依赖状态: {deps_status}")
        
        # 显示账号信息
        if self.username:
            print(f"当前账号: {self.username}")
            print(f"当前密码: {'*' * len(self.password)}")
        else:
            print("当前账号: 未设置 (请在'设置账号密码'中配置)")
        print("-" * 40)
    
    def main_menu(self):
        """主菜单"""
        while True:
            self.print_header("主菜单")
            self.print_status()
            
            print("请选择操作:")
            print("  1) 🛠️  配置Cookie")
            print("  2) 🚀 开始视频学习")
            print("  3) 📊 查看学习进度")
            print("  4) 🔗 测试连接")
            print("  5) ⚙️  设置账号密码")
            print("  6) 📁 检查文件")
            print("  7) ❓ 帮助")
            print("  8) 🚪 退出")
            print()
            
            choice = input("请输入选项 (1-8): ").strip()
            
            if choice == "1":
                self.configure_cookies()
            elif choice == "2":
                self.start_learning()
            elif choice == "3":
                self.view_progress()
            elif choice == "4":
                self.test_connection()
            elif choice == "5":
                self.set_credentials()
            elif choice == "6":
                self.check_files()
            elif choice == "7":
                self.show_help()
            elif choice == "8":
                print("\n👋 再见！")
                sys.exit(0)
            else:
                print("\n❌ 无效选项，请重新输入")
                time.sleep(1)
    
    def configure_cookies(self):
        """配置Cookie菜单"""
        while True:
            self.print_header("配置Cookie")
            print("请选择Cookie来源:")
            print("  1) 🔄 重新登录获取新Cookie")
            print("  2) 📂 从现有配置文件加载")
            print("  3) ⌨️  手动输入Cookie")
            print("  4) 🔙 返回主菜单")
            print()
            
            choice = input("请输入选项 (1-4): ").strip()
            
            if choice == "1":
                self.login_and_get_cookies()
                break
            elif choice == "2":
                self.load_cookies_from_file()
                break
            elif choice == "3":
                self.manual_input_cookies()
                break
            elif choice == "4":
                return
            else:
                print("\n❌ 无效选项")
                time.sleep(1)
    
    def login_and_get_cookies(self):
        """登录获取新Cookie"""
        self.print_header("重新登录")
        
        if self.username and self.password:
            print(f"当前账号: {self.username}")
            print(f"当前密码: {'*' * len(self.password)}")
            print()
            print("是否使用已保存的账号密码？")
            use_saved = input("使用已保存的账号密码？ (y/n): ").strip().lower()
            
            if use_saved == 'y':
                username = self.username
                password = self.password
            else:
                username = input("请输入账号: ").strip()
                password = input("请输入密码: ").strip()
        else:
            print("当前未设置账号密码，请输入：")
            username = input("请输入账号: ").strip()
            password = input("请输入密码: ").strip()
        
        print(f"\n正在使用账号 {username} 登录...")
        
        try:
            cookies = login_with_fixed_screentype(username, password)
            if cookies:
                print(f"\n✅ 登录成功！获取到 {len(cookies)} 个Cookie")
                self.learner.set_cookies(cookies)
                print("✅ Cookie已保存到配置文件")
            else:
                print("\n❌ 登录失败，请检查账号密码或网络连接")
        except Exception as e:
            print(f"\n❌ 登录过程中出错: {e}")
        
        input("\n按回车键继续...")
    
    def load_cookies_from_file(self):
        """从文件加载Cookie"""
        self.print_header("从文件加载Cookie")
        
        if not os.path.exists("config.json"):
            print("❌ 未找到配置文件 config.json")
            input("\n按回车键继续...")
            return
        
        print("可用的配置文件:")
        print("  1) config.json")
        print("  2) 🔙 返回")
        print()
        
        choice = input("请选择文件: ").strip()
        
        if choice == "1" and os.path.exists("config.json"):
            config_file = "config.json"
        elif choice == "2":
            return
        else:
            print("❌ 无效选择")
            input("\n按回车键继续...")
            return
        
        try:
            cookies = self.learner.load_cookies_from_file(config_file)
            if cookies:
                print(f"\n✅ 成功从 {config_file} 加载Cookie")
                self.learner.set_cookies(cookies)
            else:
                print(f"\n❌ 从 {config_file} 加载Cookie失败")
        except Exception as e:
            print(f"\n❌ 加载配置文件出错: {e}")
        
        input("\n按回车键继续...")
    
    def manual_input_cookies(self):
        """手动输入Cookie"""
        self.print_header("手动输入Cookie")
        
        print("请从浏览器开发者工具中复制Cookie信息")
        print("格式: name1=value1; name2=value2; ...")
        print()
        print("必需的Cookie:")
        print("  - ASP.NET_SessionId: 会话ID")
        print("  - .ASPXAUTH: 认证令牌")
        print("  - Clerk: 用户信息")
        print("  - ZYLTheme: 主题设置 (格式: Theme=blue&ScreenType=1280)")
        print()
        
        cookie_str = input("请输入Cookie字符串: ").strip()
        
        if not cookie_str:
            print("❌ Cookie字符串不能为空")
            input("\n按回车键继续...")
            return
        
        # 解析Cookie字符串
        cookies = {}
        parts = cookie_str.split(';')
        for part in parts:
            part = part.strip()
            if '=' in part:
                name, value = part.split('=', 1)
                cookies[name.strip()] = value.strip()
        
        if not cookies:
            print("❌ 未解析到有效的Cookie")
            input("\n按回车键继续...")
            return
        
        print(f"\n✅ 解析到 {len(cookies)} 个Cookie:")
        for name in cookies.keys():
            print(f"  - {name}")
        
        save = input("\n是否保存这些Cookie？ (y/n): ").strip().lower()
        if save == 'y':
            self.learner.set_cookies(cookies)
            print("✅ Cookie已保存")
        
        input("\n按回车键继续...")
    
    def start_learning(self):
        """开始视频学习"""
        self.print_header("开始视频学习")
        
        # 检查课程列表文件
        if not os.path.exists(self.course_list_path):
            print(f"❌ 课程列表文件不存在: {self.course_list_path}")
            print("请先保存课程列表页面")
            input("\n按回车键继续...")
            return
        
        # 检查Cookie
        if not self.learner.session_cookies:
            print("❌ 未配置Cookie，请先配置Cookie")
            input("\n按回车键继续...")
            return
        
        print("✅ 准备开始视频学习")
        print(f"课程列表: {self.course_list_path}")
        print(f"Cookie已配置: {len(self.learner.session_cookies)} 个")
        print()
        print("脚本将:")
        print("  1. 优先从API获取课程列表（如失败则从文件读取）")
        print("  2. 从API获取每个视频的参数")
        print("  3. 并行提交学习进度")
        print("  4. 每分钟提交60秒学习时间")
        print()
        print("📝 详细日志将输出到控制台")
        print()
        print("按 Ctrl+C 可以随时停止脚本")
        print()
        
        confirm = input("是否开始？ (y/n): ").strip().lower()
        if confirm != 'y':
            print("操作已取消")
            input("\n按回车键继续...")
            return
        
        print("\n🚀 开始视频学习...")
        print("模式: 优先使用API，失败则使用本地文件")
        print("日志输出: 控制台")
        print("-" * 40)
        
        try:
            asyncio.run(self.learner.run(self.course_list_path, use_api=True))
            print("\n✅ 视频学习完成！")
        except KeyboardInterrupt:
            print("\n⏹️  脚本已被用户中断")
        except Exception as e:
            print(f"\n❌ 运行过程中出错: {e}")
            print("请查看控制台输出获取详细错误信息")
        
        input("\n按回车键返回主菜单...")
    
    def view_progress(self):
        """查看学习进度"""
        self.print_header("查看学习进度")
        
        print("⚠️  出于安全考虑，日志不保存到文件")
        print("实时进度将在运行过程中显示在控制台")
        print("\n要查看学习进度，请:")
        print("1. 运行视频学习")
        print("2. 在控制台中查看实时输出")
        print("3. 按 Ctrl+C 停止后，进度信息将消失")
        
        input("\n按回车键继续...")
    
    def test_connection(self):
        """测试连接"""
        self.print_header("测试连接")
        
        print("正在测试与考试平台的连接...")
        
        # 在函数开头导入requests
        import requests
        
        # 检查网络连接
        try:
            response = requests.get("http://www.gaoxiaokaoshi.com", timeout=10)
            print(f"✅ 网络连接正常 (状态码: {response.status_code})")
        except Exception as e:
            print(f"❌ 网络连接失败: {e}")
        
        # 检查Cookie有效性
        if self.learner.session_cookies:
            print("\n正在测试Cookie有效性...")
            try:
                session = requests.Session()
                session.cookies.update(self.learner.session_cookies)
                session.headers.update({
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                })
                
                test_url = "http://www.gaoxiaokaoshi.com/Study/LibraryStudy.aspx"
                response = session.get(test_url, params={"Id": "1298", "PlanId": "32"}, timeout=10)
                
                if response.status_code == 200:
                    print("✅ Cookie有效，可以访问课程页面")
                    if "hidNewId" in response.text:
                        print("✅ 可以正常解析课程参数")
                    else:
                        print("⚠️  可以访问页面，但未找到课程参数")
                else:
                    print(f"❌ Cookie无效 (状态码: {response.status_code})")
                    
            except Exception as e:
                print(f"❌ Cookie测试失败: {e}")
        else:
            print("\n⚠️  未配置Cookie，跳过Cookie测试")
        
        # 测试API课程列表获取功能
        if self.learner.session_cookies:
            print("\n正在测试API课程列表获取功能...")
            try:
                # 创建临时会话
                session = requests.Session()
                session.cookies.update(self.learner.session_cookies)
                session.headers.update({
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Referer": "http://www.gaoxiaokaoshi.com/Homes/MainPage.aspx"
                })
                
                # 测试第一页
                api_url = "http://www.gaoxiaokaoshi.com/Study/LibraryStudyList.aspx"
                params = {"ddlClass": "32", "page": "1"}
                
                print(f"请求API: {api_url}?ddlClass=32&page=1")
                response = session.get(api_url, params=params, timeout=10)
                
                if response.status_code == 200:
                    print(f"✅ API请求成功 (状态码: {response.status_code})")
                    
                    content = response.text
                    if "学习中" in content:
                        learning_count = content.count("学习中")
                        print(f"✅ API返回包含 '学习中' 状态 ({learning_count} 次)")
                        
                        # 尝试解析课程
                        import asyncio
                        try:
                            # 创建异步任务来测试解析
                            async def test_parse():
                                return self.learner.parse_course_list_html(content)
                            
                            courses = asyncio.run(test_parse())
                            print(f"✅ API解析到 {len(courses)} 个未完成课程")
                            
                            if len(courses) == 0 and learning_count > 0:
                                print("⚠️  警告: API返回'学习中'状态但未解析到课程，可能需要检查解析逻辑")
                        except Exception as e:
                            print(f"⚠️  API解析测试出错: {e}")
                    else:
                        print("⚠️  API返回不包含 '学习中' 状态")
                        
                        # 检查是否有"已完成"状态
                        if "已完成" in content:
                            completed_count = content.count("已完成")
                            print(f"  API返回包含 '已完成' 状态 ({completed_count} 次)")
                        
                        # 检查是否有表格
                        if "table" in content and "开始学习" in content:
                            print("  API返回包含课程表格")
                else:
                    print(f"❌ API请求失败 (状态码: {response.status_code})")
                    
            except Exception as e:
                print(f"❌ API测试失败: {e}")
        else:
            print("\n⚠️  未配置Cookie，跳过API测试")
        
        # 检查课程列表文件
        print("\n正在检查课程列表文件...")
        if os.path.exists(self.course_list_path):
            file_size = os.path.getsize(self.course_list_path)
            print(f"✅ 课程列表文件存在 ({file_size} 字节)")
            
            # 尝试解析
            try:
                with open(self.course_list_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if "table" in content and "开始学习" in content:
                        print("✅ 文件格式正确，包含课程表格")
                    else:
                        print("⚠️  文件可能不是正确的课程列表页面")
            except Exception as e:
                print(f"❌ 读取课程列表文件失败: {e}")
        else:
            print(f"❌ 课程列表文件不存在: {self.course_list_path}")
        
        print("\n" + "-" * 40)
        print("📋 测试完成")
        input("\n按回车键继续...")
    
    def set_credentials(self):
        """设置账号密码"""
        self.print_header("设置账号密码")
        
        print(f"当前账号: {self.username}")
        print(f"当前密码: {'*' * len(self.password)}")
        print()
        
        new_username = input("请输入新账号 (直接回车保持当前): ").strip()
        new_password = input("请输入新密码 (直接回车保持当前): ").strip()
        
        if new_username:
            self.username = new_username
            print(f"✅ 账号已更新为: {self.username}")
        
        if new_password:
            self.password = new_password
            print(f"✅ 密码已更新")
        
        # 保存账号密码到配置文件
        if new_username or new_password:
            self.learner.save_credentials_to_config(self.username, self.password)
            print("✅ 账号密码已保存到配置文件")
        else:
            print("ℹ️  账号密码未更改")
        
        input("\n按回车键继续...")
    
    def check_files(self):
        """检查文件"""
        self.print_header("检查文件")
        
        print("📁 当前目录文件结构:")
        print("-" * 40)
        
        # 列出当前目录
        for item in os.listdir('.'):
            if os.path.isfile(item):
                size = os.path.getsize(item)
                print(f"📄 {item} ({size} 字节)")
            elif os.path.isdir(item):
                file_count = len([f for f in os.listdir(item) if os.path.isfile(os.path.join(item, f))])
                print(f"📂 {item}/ ({file_count} 个文件)")
        
        print("\n" + "-" * 40)
        print("必需的文件:")
        print("  ✅ video_auto_learner.py - 主脚本")
        print("  ✅ requirements.txt - 依赖列表")
        
        if os.path.exists(self.course_list_path):
            print(f"  ✅ {self.course_list_path} - 课程列表")
        else:
            print(f"  ❌ {self.course_list_path} - 课程列表 (缺失)")
        
        print(f"  ⚠️  config.json - 配置文件 (出于安全考虑，不自动生成)")
        
        input("\n按回车键继续...")
    
    def show_help(self):
        """显示帮助"""
        self.print_header("帮助")
        
        print("📖 使用指南:")
        print("-" * 40)
        print()
        print("1. 🔧 首次使用步骤:")
        print("   a) 运行 'pip install -r requirements.txt' 安装依赖")
        print("   b) 登录考试平台，保存课程列表页面")
        print("   c) 在TUI中选择 '配置Cookie' → '重新登录获取新Cookie'")
        print("   d) 开始视频学习")
        print()
        print("2. 📁 文件说明:")
        print("   - video_auto_learner.py: 主脚本")
        print("   - video_learner_tui.py: 文本用户界面")
        print("   - 考试平台_files/: 课程数据目录 (需手动保存)")
        print("   - ⚠️  出于安全考虑，不自动生成配置和日志文件")
        print()
        print("3. ⚠️  注意事项:")
        print("   - Cookie有有效期，过期后需要重新登录")
        print("   - 确保网络连接稳定")
        print("   - 按 Ctrl+C 可以随时停止脚本")
        print()
        print("4. 🆘 故障排除:")
        print("   - 查看 video_auto_learner.log 获取详细错误信息")
        print("   - 使用 '测试连接' 功能检查网络和Cookie")
        print("   - 确保课程列表HTML文件完整")
        print()
        
        input("按回车键返回主菜单...")
    
    def run(self):
        """运行TUI"""
        try:
            self.main_menu()
        except KeyboardInterrupt:
            print("\n\n👋 再见！")
            sys.exit(0)
        except Exception as e:
            print(f"\n❌ TUI运行出错: {e}")
            import traceback
            traceback.print_exc()
            input("\n按回车键退出...")

def main():
    """主函数"""
    print("正在启动视频学习自动化TUI...")
    time.sleep(1)
    
    tui = VideoLearnerTUI()
    tui.run()

if __name__ == "__main__":
    main()