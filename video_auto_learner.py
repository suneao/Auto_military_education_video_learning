#!/usr/bin/env python3
"""
视频学习自动化脚本
自动为考试平台视频课程提交学习进度
支持并行处理和Cookie自动修复
"""

import asyncio
import aiohttp
import re
import time
import json
import logging
import sys
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from bs4 import BeautifulSoup
import random
import requests

# 配置日志（同时输出到文件和控制台）
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('video_auto_learner.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class VideoCourse:
    """视频课程信息"""
    def __init__(self, course_id: int, course_name: str, total_minutes: int, 
                 completed_minutes: int, status: str):
        self.course_id = course_id
        self.course_name = course_name
        self.total_minutes = total_minutes
        self.completed_minutes = completed_minutes
        self.status = status
        self.required_seconds = max(0, (total_minutes - completed_minutes) * 60)
    
    def __str__(self):
        return f"{self.course_name} (ID: {self.course_id}, 进度: {self.completed_minutes}/{self.total_minutes}分钟, 还需: {self.required_seconds}秒)"

class VideoAutoLearner:
    """视频学习自动化主类"""
    
    def __init__(self, base_url: str = "http://www.gaoxiaokaoshi.com"):
        self.base_url = base_url
        self.session_cookies = None
        self.cookie_header = None
        self.session_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
        
    def set_cookies(self, cookies_dict: Dict[str, str]):
        """设置会话Cookie"""
        self.session_cookies = cookies_dict
        logger.info(f"已设置Cookie: {list(cookies_dict.keys())}")
        
        # 构建Cookie头用于手动设置
        cookie_parts = []
        for name, value in cookies_dict.items():
            cookie_parts.append(f"{name}={value}")
        self.cookie_header = "; ".join(cookie_parts)
        logger.debug(f"构建的Cookie头: {self.cookie_header[:100]}...")
        
        # 更新会话头部，确保包含Cookie头
        if self.cookie_header:
            self.session_headers["Cookie"] = self.cookie_header
            logger.debug("已更新session_headers中的Cookie头")
        
        # 保存到配置文件
        self.save_cookies_to_config(cookies_dict)
    
    def save_cookies_to_config(self, cookies_dict: Dict[str, str]):
        """保存Cookie和配置到配置文件（合并现有配置）"""
        try:
            # 先读取现有配置
            if os.path.exists('config.json'):
                with open('config.json', 'r', encoding='utf-8') as f:
                    config = json.load(f)
            else:
                config = {}
        except:
            config = {}
        
        # 更新配置，保留其他字段
        config.update({
            "cookies": cookies_dict,
            "base_url": self.base_url,
            "update_interval_seconds": 60,  # 改为每分钟提交一次
            "max_concurrent_videos": 30,
            "retry_attempts": 3
        })
        
        try:
            with open('config.json', 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            logger.info("Cookie已保存到 config.json")
        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")
    
    def save_credentials_to_config(self, username: str, password: str):
        """保存账号密码到配置文件（合并现有配置）"""
        try:
            # 先读取现有配置
            if os.path.exists('config.json'):
                with open('config.json', 'r', encoding='utf-8') as f:
                    config = json.load(f)
            else:
                config = {}
        except:
            config = {}
        
        # 更新账号密码，保留其他字段
        config["username"] = username
        config["password"] = password
        
        try:
            with open('config.json', 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            logger.info("账号密码已保存到 config.json")
        except Exception as e:
            logger.error(f"保存账号密码失败: {e}")
    
    def load_credentials_from_file(self, config_file: str = "config.json") -> Optional[Tuple[str, str]]:
        """从配置文件加载账号密码"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                username = config.get("username", "")
                password = config.get("password", "")
                
                if username and password:
                    logger.info(f"从配置文件加载账号: {username}")
                    return username, password
                else:
                    logger.warning("配置文件中未找到有效的账号密码")
                    return None
        except FileNotFoundError:
            logger.warning(f"配置文件 {config_file} 不存在")
            return None
        except Exception as e:
            logger.error(f"加载账号密码失败: {e}")
            return None
    
    def load_cookies_from_file(self, config_file: str = "config.json") -> Optional[Dict[str, str]]:
        """从现有配置文件加载完整的Cookie"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                cookies = config.get("cookies", {})
                logger.info(f"从配置文件 {config_file} 加载Cookie: {list(cookies.keys())}")
                
                # 修复ZYLTheme中的ScreenType
                if "ZYLTheme" in cookies and "ScreenType=" in cookies["ZYLTheme"]:
                    # 检查当前ScreenType值
                    zyl_theme = cookies["ZYLTheme"]
                    if "ScreenType=" in zyl_theme:
                        # 尝试设置有效的ScreenType
                        if "ScreenType=1280" not in zyl_theme and "ScreenType=" in zyl_theme:
                            # 将ScreenType=替换为ScreenType=1280
                            cookies["ZYLTheme"] = zyl_theme.replace("ScreenType=", "ScreenType=1280")
                            logger.info(f"修复ZYLTheme: {cookies['ZYLTheme']}")
                
                return cookies
        except FileNotFoundError:
            logger.warning(f"配置文件 {config_file} 不存在")
            return None
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            return None
    
    def parse_course_list_html(self, html_content: str) -> List[VideoCourse]:
        """解析课程列表HTML"""
        soup = BeautifulSoup(html_content, 'html.parser')
        courses = []
        
        # 找到课程表格
        table = soup.find('table', {'class': 'table', 'width': '850'})
        if not table:
            logger.error("未找到课程表格")
            return []
        
        # 解析表格行（跳过标题行）
        rows = table.find_all('tr')[1:]  # 跳过标题行
        
        for row in rows:
            try:
                # 提取课程名称和ID
                name_cell = row.find('td', {'class': 'pleft30'})
                if not name_cell:
                    continue
                    
                course_name = str(name_cell.get_text(strip=True))
                
                # 从"开始学习"按钮中提取课程ID
                start_button = row.find('a', {'class': 'btn_4'})
                if not start_button:
                    continue
                    
                onclick_text = str(start_button.get('onclick', ''))
                match = re.search(r"showframe\('.*?',(\d+)\)", onclick_text)
                if not match:
                    continue
                    
                course_id = int(match.group(1))
                
                # 提取学时信息
                cells = row.find_all('td')
                if len(cells) < 7:
                    continue
                
                # 总学时 (格式: "60分钟")
                total_cell = str(cells[2].get_text(strip=True))
                total_match = re.search(r'(\d+)', total_cell)
                total_minutes = int(total_match.group(1)) if total_match else 0
                
                # 已完成学时 (格式: "31分钟")
                completed_cell = str(cells[3].get_text(strip=True))
                completed_match = re.search(r'(\d+)', completed_cell)
                completed_minutes = int(completed_match.group(1)) if completed_match else 0
                
                # 状态
                status_cell = cells[4]
                status_span = status_cell.find('span')
                if status_span:
                    status_text = str(status_span.get_text(strip=True))
                    if "学习中" in status_text:
                        status = "学习中"
                    elif "未学习" in status_text:
                        status = "未学习"
                    elif "已完成" in status_text:
                        status = "已完成"
                    else:
                        status = "未知"
                else:
                    status = "未知"
                
                # 处理状态为"学习中"或"未学习"的课程
                if status in ["学习中", "未学习"]:
                    course = VideoCourse(
                        course_id=course_id,
                        course_name=course_name,
                        total_minutes=total_minutes,
                        completed_minutes=completed_minutes,
                        status=status
                    )
                    courses.append(course)
                    logger.info(f"发现课程[{status}]: {course}")
                
            except Exception as e:
                logger.warning(f"解析课程行时出错: {e}")
                continue
        
        logger.info(f"共发现 {len(courses)} 个可学习课程 (状态: 学习中或未学习)")
        return courses
    
    async def fetch_course_list_from_api(self, session: aiohttp.ClientSession) -> List[VideoCourse]:
        """从API获取课程列表（支持分页）"""
        url = f"{self.base_url}/Study/LibraryStudyList.aspx"
        
        # 添加必要的头部
        headers = self.session_headers.copy()
        headers["Referer"] = f"{self.base_url}/Homes/MainPage.aspx"
        headers["Content-Type"] = "application/x-www-form-urlencoded"
        
        all_courses = []
        page = 1
        total_pages = 1
        viewstate = ""
        viewstategenerator = ""
        eventvalidation = ""
        
        try:
            logger.info("正在从API获取课程列表...")
            
            # 首先获取第一页以提取隐藏字段
            logger.info("获取第一页课程列表...")
            async with session.get(url, params={"ddlClass": "32"}, headers=headers) as response:
                if response.status != 200:
                    logger.error(f"获取第一页课程列表失败，状态码: {response.status}")
                    return []
                
                html_content = await response.text()
                logger.info(f"第一页响应大小: {len(html_content)} 字符")
                
                # 提取隐藏字段
                viewstate, viewstategenerator, eventvalidation = self._extract_hidden_fields(html_content)
                
                # 解析第一页的课程（包含学习中状态）
                page_courses = self.parse_course_list_html(html_content)
                logger.info(f"第一页找到 {len(page_courses)} 个课程")
                
                # 添加到总列表
                for course in page_courses:
                    if not any(c.course_id == course.course_id for c in all_courses):
                        all_courses.append(course)
                
                # 解析总页数
                total_pages = self._parse_total_pages(html_content)
                logger.info(f"总页数: {total_pages}")
                
                # 检查页面内容
                self._check_page_content(html_content)
            
            # 如果有更多页面，获取后续页面
            for page in range(2, total_pages + 1):
                if not viewstate:
                    logger.warning(f"缺少隐藏字段，无法获取第 {page} 页")
                    break
                
                # 构建表单数据 - 使用正确的分页参数 PageSplit1$ddlPage
                form_data = {
                    '__VIEWSTATE': viewstate,
                    '__VIEWSTATEGENERATOR': viewstategenerator,
                    '__EVENTVALIDATION': eventvalidation,
                    'ddlClass': '32',
                    'PageSplit1$ddlPage': str(page)
                }
                
                logger.info(f"获取第 {page} 页课程列表...")
                async with session.post(url, data=form_data, headers=headers) as response:
                    if response.status != 200:
                        logger.error(f"获取第 {page} 页课程列表失败，状态码: {response.status}")
                        break
                    
                    html_content = await response.text()
                    logger.info(f"第 {page} 页响应大小: {len(html_content)} 字符")
                    
                    # 解析课程的课程
                    page_courses = self.parse_course_list_html(html_content)
                    logger.info(f"第 {page} 页找到 {len(page_courses)} 个课程")
                    
                    # 检查页面内容
                    self._check_page_content(html_content)
                    
                    # 添加到总列表（去重）
                    for course in page_courses:
                        if not any(c.course_id == course.course_id for c in all_courses):
                            all_courses.append(course)
                    
                    # 短暂延迟
                    await asyncio.sleep(0.5)
            
            logger.info(f"从所有页面共获取到 {len(all_courses)} 个课程")
            return all_courses
                
        except Exception as e:
            logger.error(f"从API获取课程列表时出错: {e}")
            return all_courses
    
    def _extract_hidden_fields(self, html_content: str) -> Tuple[str, str, str]:
        """从HTML内容提取隐藏字段"""
        import re
        viewstate = ""
        viewstategenerator = ""
        eventvalidation = ""
        
        try:
            # 提取VIEWSTATE
            viewstate_match = re.search(r'id=\"__VIEWSTATE\" value=\"([^\"]+)\"', html_content)
            if viewstate_match:
                viewstate = viewstate_match.group(1)
            
            # 提取VIEWSTATEGENERATOR
            viewstategenerator_match = re.search(r'id=\"__VIEWSTATEGENERATOR\" value=\"([^\"]+)\"', html_content)
            if viewstategenerator_match:
                viewstategenerator = viewstategenerator_match.group(1)
            
            # 提取EVENTVALIDATION
            eventvalidation_match = re.search(r'id=\"__EVENTVALIDATION\" value=\"([^\"]+)\"', html_content)
            if eventvalidation_match:
                eventvalidation = eventvalidation_match.group(1)
            
            logger.debug(f"提取隐藏字段: VIEWSTATE长度={len(viewstate)}, VIEWSTATEGENERATOR={viewstategenerator}, EVENTVALIDATION长度={len(eventvalidation)}")
        except Exception as e:
            logger.error(f"提取隐藏字段时出错: {e}")
        
        return viewstate, viewstategenerator, eventvalidation
    
    def _check_page_content(self, html_content: str):
        """检查页面内容，记录不同状态的课程数量"""
        try:
            learning_count = html_content.count("学习中")
            not_learning_count = html_content.count("未学习")
            completed_count = html_content.count("已完成")
            start_learning_count = html_content.count("开始学习")
            
            if learning_count > 0:
                logger.info(f"页面包含 '学习中' 状态 {learning_count} 次")
            if not_learning_count > 0:
                logger.info(f"页面包含 '未学习' 状态 {not_learning_count} 次")
            if completed_count > 0:
                logger.info(f"页面包含 '已完成' 状态 {completed_count} 次")
            if start_learning_count > 0:
                logger.info(f"页面包含 '开始学习' 按钮 {start_learning_count} 次")
                
            # 检查是否有表格
            if "table" in html_content:
                logger.debug("页面包含表格")
        except Exception as e:
            logger.debug(f"检查页面内容时出错: {e}")
    
    def _parse_total_pages(self, html_content: str) -> int:
        """从HTML内容解析总页数"""
        try:
            # 查找分页信息，格式如 "1/6" 或 "第1页/共6页"
            import re
            
            # 尝试匹配 "数字/数字" 格式
            page_pattern = r'(\d+)\s*/\s*(\d+)'
            matches = re.findall(page_pattern, html_content)
            
            for match in matches:
                current, total = match
                total_int = int(total)
                if total_int > 0:
                    return total_int
            
            # 如果没有找到，尝试查找页码选择框
            if 'PageSplit1_ddlPage' in html_content:
                # 计算option数量
                option_count = html_content.count('<option value=')
                if option_count > 0:
                    return option_count
            
            # 默认返回1页
            return 1
            
        except Exception as e:
            logger.error(f"解析总页数时出错: {e}")
            return 1
    
    async def fetch_video_params(self, session: aiohttp.ClientSession, course_id: int) -> Optional[Dict[str, str]]:
        """获取视频参数 - 修复版本"""
        url = f"{self.base_url}/Study/LibraryStudy.aspx"
        params = {
            "Id": str(course_id),
            "PlanId": "32"
        }
        
        # 添加必要的头部
        headers = self.session_headers.copy()
        headers["Referer"] = f"{self.base_url}/Study/LibraryStudyList.aspx"
        
        try:
            logger.info(f"正在获取课程 {course_id} 的参数...")
            async with session.get(url, params=params, headers=headers) as response:
                logger.info(f"获取参数响应状态码: {response.status}")
                
                if response.status != 200:
                    # 尝试读取错误信息
                    try:
                        error_text = await response.text()
                        logger.error(f"错误响应内容前500字符: {error_text[:500]}")
                        
                        # 检查是否是ScreenType错误
                        if "ScreenType" in error_text or "1280" in error_text:
                            logger.warning("检测到ScreenType相关错误，可能需要修复Cookie中的ZYLTheme")
                    except:
                        logger.error("无法读取错误响应内容")
                    return None
                
                html = await response.text()
                
                # 使用正则表达式提取隐藏字段
                patterns = {
                    "hid_new_id": r'id="hidNewId"\s+value="([^"]+)"',
                    "hid_ref_id": r'id="hidRefId"\s+value="([^"]+)"',
                    "hid_student_id": r'id="hidStudentId"\s+value="([^"]+)"',
                    "hid_pass_line": r'id="hidPassLine"\s+value="([^"]+)"',
                    "hid_study_time": r'id="hidStudyTime"\s+value="([^"]+)"',
                    "hid_session_id": r'id="hidSessionID"\s+value="([^"]+)"',
                }
                
                extracted = {}
                for key, pattern in patterns.items():
                    match = re.search(pattern, html)
                    if match:
                        extracted[key] = match.group(1)
                    else:
                        logger.warning(f"未找到字段 {key}")
                        # 不保存调试HTML到文件
                        logger.warning(f"课程 {course_id} 参数解析失败，跳过该课程")
                        return None
                
                logger.info(f"课程 {course_id} 参数获取成功")
                return extracted
                
        except Exception as e:
            logger.error(f"获取课程 {course_id} 参数时出错: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    async def submit_progress(self, session: aiohttp.ClientSession, video_params: Dict[str, str], 
                            current_seconds: int, max_retries: int = 3) -> bool:
        """提交学习进度 - 限制每次最大提交时间为60秒"""
        # 限制每次提交的最大时间为60秒
        submit_seconds = min(current_seconds, 60)
        
        url = f"{self.base_url}/Study/updateTime.ashx"  # 正确的URL路径
        query_params = {
            "Id": video_params["hid_new_id"],
            "pTime": str(submit_seconds),
            "Mins": video_params["hid_pass_line"],
            "refId": video_params["hid_ref_id"],
            "StudentId": video_params["hid_student_id"],
            "StydyTime": video_params["hid_study_time"],  # 注意拼写：StydyTime
            "SessionId": video_params["hid_session_id"]
        }
        
        # 添加Referer头
        headers = self.session_headers.copy()
        headers["Referer"] = f"{self.base_url}/Study/LibraryStudy.aspx?Id={video_params['hid_ref_id']}&PlanId=32"
        
        # 记录提交信息
        if current_seconds > 60:
            logger.info(f"提交进度: {submit_seconds}秒 (总共需要 {current_seconds}秒)")
        else:
            logger.info(f"提交进度: {submit_seconds}秒")
        
        for attempt in range(max_retries):
            try:
                # 添加随机延迟避免过于规律
                delay = random.uniform(0.1, 0.5)
                await asyncio.sleep(delay)
                
                async with session.get(url, params=query_params, headers=headers) as response:
                    if response.status == 200:
                        response_text = await response.text()
                        # 检查响应内容是否包含成功标记
                        if "success" in response_text.lower() or len(response_text) < 100:
                            logger.info(f"进度提交成功: {submit_seconds}秒 ({submit_seconds/60:.1f}分钟)")
                        else:
                            logger.info(f"进度提交成功: {submit_seconds}秒, 响应: {response_text[:100]}...")
                        return True
                    else:
                        logger.warning(f"进度提交失败，状态码: {response.status}, 尝试 {attempt+1}/{max_retries}")
                        
            except Exception as e:
                logger.error(f"提交进度时出错: {e}, 尝试 {attempt+1}/{max_retries}")
            
            # 指数退避重试
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt + random.uniform(0, 1)
                await asyncio.sleep(wait_time)
        
        logger.error(f"进度提交失败，已重试 {max_retries} 次")
        return False
    
    async def video_update_worker(self, session: aiohttp.ClientSession, course: VideoCourse, 
                                video_params: Dict[str, str], start_delay: float = 0):
        """单个视频的更新工作器 - 每分钟提交60秒"""
        # 等待初始延迟（用于交错启动）
        if start_delay > 0:
            await asyncio.sleep(start_delay)
        
        logger.info(f"开始处理视频: {course.course_name} (延迟: {start_delay:.1f}秒)")
        
        required_seconds = course.required_seconds
        remaining_seconds = required_seconds
        total_submitted = 0
        submission_count = 0
        
        logger.info(f"视频 [{course.course_name}] 需要完成 {required_seconds}秒 ({required_seconds/60:.1f}分钟)")
        
        # 每分钟提交60秒，直到完成所需总时间
        while remaining_seconds > 0:
            submission_count += 1
            
            # 每分钟提交60秒（或剩余不足60秒时提交剩余时间）
            submit_seconds = min(remaining_seconds, 60)
            
            # 第一次请求更新时间会被判为无效，所以第一次提交1秒（避免0秒可能被拒绝）
            if submission_count == 1:
                submit_seconds = 1
                logger.info(f"视频 [{course.course_name}] 第 {submission_count} 次提交（首次提交1秒，避免无效更新）")
            
            # 提交进度
            success = await self.submit_progress(session, video_params, submit_seconds)
            
            if success:
                # 只有非首次提交才计入总时长（第一次提交无效）
                if submission_count > 1:
                    total_submitted += submit_seconds
                    remaining_seconds -= submit_seconds
                
                logger.info(f"视频 [{course.course_name}] 第 {submission_count} 次提交成功: {submit_seconds}秒")
                logger.info(f"  累计提交: {total_submitted}秒 ({total_submitted/60:.1f}分钟), 剩余: {remaining_seconds}秒 ({remaining_seconds/60:.1f}分钟)")
                
                # 如果还有剩余时间，等待60秒后再继续提交
                if remaining_seconds > 0:
                    wait_time = 60.0  # 固定等待60秒
                    logger.info(f"  等待 {wait_time:.0f}秒后继续提交...")
                    await asyncio.sleep(wait_time)
            else:
                logger.error(f"视频 [{course.course_name}] 第 {submission_count} 次提交失败")
                # 失败后等待更长时间再重试
                wait_time = random.uniform(10.0, 30.0)
                logger.info(f"  等待 {wait_time:.1f}秒后重试...")
                await asyncio.sleep(wait_time)
        
        logger.info(f"视频 [{course.course_name}] 完成！总共提交 {submission_count} 次，累计 {total_submitted}秒 ({total_submitted/60:.1f}分钟)")
        return total_submitted
    
    async def run(self, course_list_html_path: Optional[str] = None, use_api: bool = True, 
                 allow_file_fallback: bool = True):
        """主运行函数
        
        Args:
            course_list_html_path: 课程列表HTML文件路径（如果use_api=False或API失败时回退）
            use_api: 是否从API获取课程列表，如果为False则从文件读取
            allow_file_fallback: 当use_api=True且API返回空列表时，是否允许回退到文件读取
        """
        logger.info("开始视频学习自动化脚本")
        
        # 检查是否有Cookie
        if not self.session_cookies:
            # 尝试从现有配置文件加载完整Cookie
            cookies = self.load_cookies_from_file("config.json")
            if cookies:
                self.session_cookies = cookies
                logger.info("从配置文件加载完整Cookie成功")
            else:
                logger.error("未设置Cookie，请先设置Cookie")
                return
        
        # 1. 获取课程列表
        courses = []
        
        if use_api:
            logger.info("从API获取课程列表...")
            
            # 创建会话用于获取课程列表
            connector = aiohttp.TCPConnector(limit=40)
            timeout = aiohttp.ClientTimeout(total=30)
            session_headers = self.session_headers.copy()
            if self.cookie_header:
                session_headers["Cookie"] = self.cookie_header
            
            async with aiohttp.ClientSession(
                headers=session_headers,
                connector=connector,
                timeout=timeout
            ) as session:
                courses = await self.fetch_course_list_from_api(session)
            
            # 如果API返回空列表，但有文件路径且允许回退，则尝试从文件读取
            if not courses and course_list_html_path and allow_file_fallback:
                logger.info("API未返回课程，尝试从文件读取课程列表...")
                try:
                    with open(course_list_html_path, 'r', encoding='utf-8') as f:
                        html_content = f.read()
                    courses = self.parse_course_list_html(html_content)
                    logger.info(f"从文件读取到 {len(courses)} 个课程")
                except Exception as e:
                    logger.error(f"读取课程列表文件失败: {e}")
            elif not courses and not allow_file_fallback:
                logger.error("API未返回课程，且不允许文件回退")
                return
        elif course_list_html_path:
            logger.info(f"从文件读取课程列表: {course_list_html_path}")
            try:
                with open(course_list_html_path, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                courses = self.parse_course_list_html(html_content)
            except Exception as e:
                logger.error(f"读取课程列表文件失败: {e}")
                return
        else:
            logger.error("当use_api=False时，必须提供课程列表HTML文件路径")
            return
        
        if not courses:
            logger.info("没有找到未完成的课程")
            return
        
        # 2. 创建会话
        connector = aiohttp.TCPConnector(limit=40)  # 限制并发连接数，支持最多30个并发课程
        timeout = aiohttp.ClientTimeout(total=30)
        
        # 复制头部并手动添加Cookie头
        session_headers = self.session_headers.copy()
        if self.cookie_header:
            session_headers["Cookie"] = self.cookie_header
            logger.debug("已手动添加Cookie头到会话")
        
        async with aiohttp.ClientSession(
            headers=session_headers,
            connector=connector,
            timeout=timeout
        ) as session:
            
            # 3. 为每个课程获取参数
            tasks = []
            course_params_map = {}
            
            for course in courses:
                params = await self.fetch_video_params(session, course.course_id)
                if params:
                    course_params_map[course.course_id] = (course, params)
                else:
                    logger.error(f"无法获取课程 {course.course_name} 的参数，跳过")
            
            if not course_params_map:
                logger.error("没有成功获取任何课程的参数")
                return
            
            logger.info(f"成功获取 {len(course_params_map)} 个课程的参数")
            
            # 4. 启动所有视频更新任务（交错启动）
            worker_tasks = []
            
            # 限制最多30个并发课程
            course_items = list(course_params_map.items())
            if len(course_items) > 30:
                logger.warning(f"发现 {len(course_items)} 个课程，超过30个并发限制，只处理前30个课程")
                course_items = course_items[:30]
            
            for idx, (course_id, (course, params)) in enumerate(course_items):
                start_delay = idx * 1.0  # 每个任务延迟1秒启动，实现交错
                task = asyncio.create_task(
                    self.video_update_worker(session, course, params, start_delay)
                )
                worker_tasks.append(task)
                logger.info(f"调度视频 [{course.course_name}]，启动延迟: {start_delay:.1f}秒")
            
            # 5. 等待所有任务完成
            try:
                results = await asyncio.gather(*worker_tasks, return_exceptions=True)
                
                total_submitted = 0
                successful = 0
                for idx, result in enumerate(results):
                    if isinstance(result, Exception):
                        logger.error(f"任务 {idx} 失败: {result}")
                    elif isinstance(result, int):
                        total_submitted += result
                        successful += 1
                    else:
                        logger.warning(f"任务 {idx} 返回未知类型: {type(result)}")
                
                logger.info(f"所有任务完成，成功处理 {successful}/{len(worker_tasks)} 个视频，总共提交 {total_submitted} 秒学习时长")
                
            except KeyboardInterrupt:
                logger.info("收到中断信号，正在停止...")
                for task in worker_tasks:
                    task.cancel()
                await asyncio.gather(*worker_tasks, return_exceptions=True)
                logger.info("已停止所有任务")
            except Exception as e:
                logger.error(f"运行过程中出错: {e}")

def login_with_fixed_screentype(username: str, password: str) -> Optional[Dict[str, str]]:
    """使用修复的screenType登录"""
    print("使用修复的screenType登录...")
    
    base_url = "http://www.gaoxiaokaoshi.com"
    
    # 创建会话
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Origin": base_url,
        "Referer": f"{base_url}/Login.aspx",
    })
    
    # 1. 访问登录页面获取初始Cookie
    print("1. 访问登录页面...")
    login_page_url = f"{base_url}/Login.aspx"
    try:
        response = session.get(login_page_url, timeout=10)
        
        if response.status_code != 200:
            print(f"访问登录页面失败: {response.status_code}")
            return None
        
        print(f"初始Cookie: {list(session.cookies.get_dict().keys())}")
    except Exception as e:
        print(f"访问登录页面出错: {e}")
        return None
    
    # 2. 提交登录表单 - 尝试不同的screenType值
    print("2. 提交登录信息（尝试不同screenType）...")
    login_post_url = f"{base_url}/HidLogin.aspx"
    
    # 尝试不同的screenType值
    screen_type_tests = [
        "",          # 空字符串
        "1280",      # 1280
        "default",   # default
        "1",         # 1
        "1024",      # 1024
        "1366",      # 1366
        "1920",      # 1920
    ]
    
    for screen_type in screen_type_tests:
        # 登录表单数据
        form_data = {
            "name": username,
            "pw": password,
            "btnSubmit": "  "  # 两个空格
        }
        
        # 如果screen_type不为空，添加到表单数据
        if screen_type:
            form_data["screenType"] = screen_type
        
        print(f"  尝试screenType: '{screen_type}'")
        
        try:
            response = session.post(login_post_url, data=form_data, timeout=10, allow_redirects=True)
            print(f"  响应状态码: {response.status_code}")
            print(f"  当前Cookie: {list(session.cookies.get_dict().keys())}")
            
            # 检查是否登录成功
            if response.status_code == 200:
                # 尝试访问主页面验证登录
                mainpage_url = f"{base_url}/Homes/MainPage.aspx?menu=3&subMenu=4"
                mainpage_response = session.get(mainpage_url, timeout=10)
                
                if mainpage_response.status_code == 200:
                    if "我的课程" in mainpage_response.text or "LibraryStudyList" in mainpage_response.text:
                        print(f"  登录成功！使用的screenType: '{screen_type}'")
                        
                        # 获取完整的Cookie
                        cookies = session.cookies.get_dict()
                        print(f"  获取到Cookie数量: {len(cookies)}")
                        
                        # 检查是否有ASP.NET_SessionId
                        if "ASP.NET_SessionId" in cookies:
                            print(f"  ASP.NET_SessionId: {cookies['ASP.NET_SessionId'][:20]}...")
                        
                        return cookies
                    else:
                        print("  登录失败：无法访问课程页面")
                else:
                    print(f"  访问主页面失败: {mainpage_response.status_code}")
            else:
                print(f"  登录请求失败: {response.status_code}")
                
        except Exception as e:
            print(f"  登录过程中出错: {e}")
        
        # 短暂延迟
        time.sleep(1)
    
    print("所有screenType尝试都失败")
    return None

async def main():
    """主函数"""
    print("=" * 60)
    print("视频学习自动化脚本")
    print("=" * 60)
    
    # 课程列表文件路径
    course_list_path = "考试平台_files/LibraryStudyList.html"
    
    if not os.path.exists(course_list_path):
        print(f"错误: 课程列表文件不存在: {course_list_path}")
        return
    
    # 方法1：直接使用现有配置文件中的Cookie
    print("\n=== 方法1：使用现有配置文件中的Cookie ===")
    
    # 创建学习器实例
    learner = VideoAutoLearner(base_url="http://www.gaoxiaokaoshi.com")
    
    # 尝试从现有配置文件加载完整Cookie
    cookies = learner.load_cookies_from_file("config.json")
    
    if cookies:
        print(f"成功加载现有Cookie，数量: {len(cookies)}")
        learner.set_cookies(cookies)
        
        # 运行视频学习
        print("\n开始视频学习...")
        print("脚本将在后台运行，按 Ctrl+C 停止")
        print("日志将输出到控制台")
        print("-" * 60)
        
        try:
            await learner.run(course_list_path, use_api=True, allow_file_fallback=True)
            print("\n视频学习完成！")
            return
        except KeyboardInterrupt:
            print("\n程序被用户中断")
            return
        except Exception as e:
            print(f"\n使用现有Cookie运行出错: {e}")
    
    # 方法2：如果现有Cookie无效，提示用户重新登录
    print("\n=== 方法2：重新登录获取新Cookie ===")
    print("当前Cookie已失效，需要重新登录获取新Cookie")
    print("\n请使用TUI进行登录操作：")
    print("1. 运行: python video_learner_tui.py")
    print("2. 选择: '配置Cookie' → '重新登录获取新Cookie'")
    print("3. 输入您的账号密码")
    print("\n或手动获取Cookie：")
    print("1. 登录网站获取新Cookie")
    print("2. 在TUI中选择'配置Cookie' → '手动输入Cookie'")
    print("3. 粘贴新Cookie")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"\n程序运行出错: {e}")
        import traceback
        traceback.print_exc()