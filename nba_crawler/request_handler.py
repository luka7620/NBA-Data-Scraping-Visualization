# -*- coding: utf-8 -*-
"""
NBA 篮球数据爬虫 - HTTP 请求模块
封装网络请求，支持重试和延迟
"""

import time
import requests
from config import HEADERS, REQUEST_TIMEOUT, REQUEST_DELAY, MAX_RETRIES, BASE_URL


class RequestHandler:
    """HTTP 请求处理器"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.last_request_time = 0
    
    def _wait_for_delay(self):
        """等待请求间隔，避免频繁访问"""
        elapsed = time.time() - self.last_request_time
        if elapsed < REQUEST_DELAY:
            time.sleep(REQUEST_DELAY - elapsed)
    
    def get(self, url, params=None, custom_headers=None):
        """
        发送 GET 请求
        
        Args:
            url: 请求地址（可以是完整URL或相对路径）
            params: URL 参数
            custom_headers: 自定义请求头（可选）
            
        Returns:
            Response 对象或 None（失败时）
        """
        # 处理相对路径
        if not url.startswith("http"):
            url = BASE_URL + url
        
        # 处理特定网站的请求头
        headers = {}
        if "basketball-reference.com" in url:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
                "Cache-Control": "max-age=0",
            }
        
        if custom_headers:
            headers.update(custom_headers)
        
        # 等待间隔
        self._wait_for_delay()
        
        # 重试机制
        for attempt in range(MAX_RETRIES):
            try:
                print(f"[请求] {url}" + (f" (重试 {attempt})" if attempt > 0 else ""))
                response = self.session.get(
                    url,
                    params=params,
                    timeout=REQUEST_TIMEOUT,
                    headers=headers if headers else None
                )
                self.last_request_time = time.time()
                
                # 检查响应状态
                if response.status_code == 200:
                    return response
                else:
                    print(f"[警告] 状态码: {response.status_code}")
                    
            except requests.exceptions.Timeout:
                print(f"[错误] 请求超时: {url}")
            except requests.exceptions.ConnectionError:
                print(f"[错误] 连接失败: {url}")
            except requests.exceptions.RequestException as e:
                print(f"[错误] 请求异常: {e}")
            
            # 重试前等待
            if attempt < MAX_RETRIES - 1:
                wait_time = (attempt + 1) * 2
                print(f"[等待] {wait_time} 秒后重试...")
                time.sleep(wait_time)
        
        print(f"[失败] 无法获取: {url}")
        return None
    
    def get_html(self, url, params=None, encoding="utf-8"):
        """
        获取页面 HTML 内容
        
        Args:
            url: 请求地址
            params: URL 参数
            encoding: 编码格式
            
        Returns:
            HTML 字符串或 None
        """
        response = self.get(url, params)
        if response:
            response.encoding = encoding
            return response.text
        return None
    
    def close(self):
        """关闭会话"""
        self.session.close()


# 创建全局请求处理器实例
request_handler = RequestHandler()


def get_page(url, params=None):
    """便捷函数：获取页面 HTML"""
    return request_handler.get_html(url, params)
