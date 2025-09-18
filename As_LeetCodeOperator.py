import re
from typing import Any, Callable, List, cast
import logging
from xml.sax.xmlreader import Locator
from playwright.async_api import async_playwright, expect
from playwright.async_api import Page, Browser, BrowserContext
from camel.toolkits import FunctionTool
import subprocess
import os
import time
import socket


class AsLeetCodeOperator:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.chrome_process = None
        self.idx_now_solve = 0

    async def start_chrome_with_debug(self):
        """
        启动带调试端口的 Chrome 浏览器
        """
        def is_port_in_use(port):
            """
            检查指定端口是否被占用
            """
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.bind(('localhost', port))
                    return False
                except OSError:
                    return True

        # 检查9222端口是否被占用
        debug_port = 9222
        if is_port_in_use(debug_port):
            print(f"端口 {debug_port} 已被占用，可能 Chrome 浏览器已经在运行")
            return None

        # Chrome 可执行文件路径
        chrome_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        ]

        chrome_exe = None
        for path in chrome_paths:
            if os.path.exists(path):
                chrome_exe = path
                break

        if not chrome_exe:
            print("错误：找不到 Chrome 浏览器可执行文件")
            return None

        # 用户数据目录
        user_data_dir = os.path.join(os.getcwd(), "user_data")
        os.makedirs(user_data_dir, exist_ok=True)

        # 构建命令行参数
        chrome_cmd = [
            chrome_exe,
            f"--remote-debugging-port={debug_port}",
            f"--user-data-dir={user_data_dir}",
            "--no-first-run",
            "--no-default-browser-check"
        ]

        print("Chrome 可执行文件路径:", chrome_exe)
        print("用户数据目录:", user_data_dir)
        print("启动命令:", " ".join(chrome_cmd))

        try:
            # 启动 Chrome 浏览器
            self.chrome_process = subprocess.Popen(chrome_cmd)
            # 等待一段时间让程序运行
            time.sleep(2)
            print("\nChrome 浏览器已成功启动")
            print("调试端口:", debug_port)
            return self.chrome_process
        except Exception as e:
            print(f"启动 Chrome 浏览器时出错: {e}")
            return False

    async def init_browser(self):
        """
        初始化浏览器连接
        """
        user_manual_input = "http://localhost:9222/"
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.connect_over_cdp(user_manual_input)
        self.context = self.browser.contexts[0]
        self.page = self.context.pages[0]

    async def check_success(self):
        """
        检查代码执行结果
        """
        try:
            result = self.page.locator("div.items-center").filter(has_text="通过的测试用例").nth(0).locator("span").nth(0)
            result_text = await result.inner_text()
            print(result_text)
            if result_text.find("通过") != -1:
                return "通过"
            else:
                message = self.page.locator("div.break-all").nth(0)
                return f"未通过:{await message.text_content()}"
        except Exception as e:
            return f"检查结果时出错: {str(e)}"

    async def input_code_for_leetcode(self, element, code: str, delay: int = 100, timeout: int = 30000):
        await element.focus()
        await element.clear()
        """输入代码并运行"""
        lines = code.splitlines(True)
        for line in lines:
            if "page.keyboard.press" in line:
                operator, num = line.split(",")
                num = int(num.strip())
                for _ in range(num):
                    await self.page.keyboard.press('Backspace')
            else:
                await element.press_sequentially(line, delay=delay, timeout=timeout)

    async def submit_code(self, code: str, url: str) -> str:
        """
        根据题目url提交代码, 并返回判题结果
        """
        await self.page.goto(url=url)
        input_elem = self.page.get_by_role("textbox", name="Editor content;Press Alt+F1")
        await input_elem.press("CapsLock")
        await self.page.wait_for_timeout(15000)
        await input_elem.clear()
        await self.input_code_for_leetcode(input_elem, code, 100, 30000)
        await self.page.keyboard.press("Control+Enter")

        message = await self.check_success()
        return message

    async def get_question_description(self, url: str) -> str:
        """
        根据url得到题目描述信息
        """
        await self.page.goto(url=url)
        element = self.page.locator("[data-track-load='description_content']")
        return await element.inner_text()

    async def get_question_solution(self, url: str) -> str:
        """
        根据题目url获取题目题解信息
        """
        solution_url = url + "/solution/"
        await self.page.goto(solution_url, timeout=30000)
        await self.page.locator("span").filter(has_text="Python3").click()
        # 等待特定元素出现
        await self.page.wait_for_selector(
            "div.transition-opacity > div.relative > div.flex-col > div.group", 
            timeout=30000
        )
        # 获取所有又带group属性的div元素
        locators = self.page.locator("div.transition-opacity > div.relative > div.flex-col > div.group")
        div_list = await locators.all()
        # 查看获取元素数量
        count = await locators.count()
        print("题解数量：", count)
        if count < self.idx_now_solve:
            return "你已看完所有题解如果还没有思路请返回题解中的python3代码"
        await div_list[self.idx_now_solve].click()
        self.idx_now_solve += 1
        await self.page.wait_for_selector("div.break-words", timeout=10000)
        content = self.page.locator("div.break-words").filter(has_text="python")
        return await content.inner_text()

    async def close(self):
        """
        关闭浏览器和playwright资源
        """
        try:
            if self.page:
                await self.page.close()
                self.page = None
        except Exception as e:
            print(f"关闭page时出错: {e}")

        try:
            if self.context:
                await self.context.close()
                self.context = None
        except Exception as e:
            print(f"关闭context时出错: {e}")

        try:
            if self.browser:
                await self.browser.close()
                self.browser = None
        except Exception as e:
            print(f"关闭browser时出错: {e}")

        try:
            if self.playwright:
                await self.playwright.stop()
                self.playwright = None
        except Exception as e:
            print(f"停止playwright时出错: {e}")

        try:
            if self.chrome_process:
                self.chrome_process.terminate()
                self.chrome_process = None
        except Exception as e:
            print(f"终止chrome进程时出错: {e}")
    
    def get_tools(self) -> List[FunctionTool]:
        r"""Get available function tools
        based on enabled_tools configuration."""
        # Map tool names to their corresponding methods
        tool_map = {
            "get_question_solution": self.get_question_solution,
            "get_question_description": self.get_question_description,
            "submit_code": self.submit_code,
        }

        enabled_tools = []

        for tool_name in tool_map.keys():
            tool = FunctionTool(
                cast(Callable[..., Any], tool_map[tool_name])
            )
            enabled_tools.append(tool)

        logging.info(f"Returning {len(enabled_tools)} enabled tools")
        return enabled_tools