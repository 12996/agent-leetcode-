import re
from typing import Any, Callable, List, cast
from venv import logger
from xml.sax.xmlreader import Locator
from playwright.sync_api import sync_playwright, expect
from playwright.sync_api import Page, Browser, BrowserContext
from camel.toolkits import FunctionTool
import subprocess
import os
import time
import socket

from SubmitStatus import SubmitStatus

 

class LeetCodeOperator:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self._start_chrome_with_debug()
        self._init_browser()
        self.idx_now_solve = 0
        self.url = ""

    def set_url(self, url):
        self.url = url

    def _start_chrome_with_debug(self):
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
    def _input_code_for_leetcode(self, element: Locator, code: str, delay: int = 100, timeout: int = 30000):
        element.focus()
        # 验证清除效果
        current_value = element.input_value() if element.input_value() else ""
        if current_value.strip():
            # 如果还有内容，使用更强制的方法
            element.clear()

        """输入代码并运行"""
        lines = code.splitlines(True)
        space_num = 0
        for line in lines:
            # 将导包代码去除
            if "from" in line or "import" in line:
                continue
            # 清除空格
            for _ in range(space_num):
                self.page.keyboard.press("Backspace")
            match = re.match(r"^ *", line)
            space_num = len(match.group(0)) // 4
            # 判断是否是结束符号
            if len(line.strip()) == 1 and line[0] == ")" or line[0] == "]" or line[0] == "}":
                self.page.keyboard.press("ArrowDown")
                line[0] = "\n"
            # 判断回车前是否加空格
            if len(line.strip()) > 0:
                line = line.replace("\n", " \n")
            element.press_sequentially(line, delay=delay, timeout=timeout)
            line = line.strip()
            if line[-1:] == ":":
                space_num += 1


    def _init_browser(self):
        """
        初始化浏览器连接
        """
        user_manual_input = "http://localhost:9222/"
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.connect_over_cdp(user_manual_input)
        self.context = self.browser.contexts[0]
        self.page = self.context.pages[0]

    def _check_success(self):
        """
        检查代码执行结果
        """
        result = self.page.locator("div.items-center").filter(has_text="通过的测试用例").nth(0).locator("span").nth(0)
        print(result.inner_text())
        if result.inner_text().find("通过") != -1:
            return SubmitStatus.SUCCESS
        else:
            message = self.page.locator("div.gap-4 > div.gap-4").filter(has_text="通过的测试用例").nth(0)
           # message.highlight()
           # self.page.wait_for_timeout(5000)
            print("error:", message.text_content())
            return f"{SubmitStatus.ERROR} 错误信息为:{message.text_content()}"

    def _clear_lt_code(self, input: Locator):
        input.click()
        # 用来看选择元素的
        # input.highlight()
        input.press("CapsLock")
        input.press("Control+A")
        input.press("Backspace")

    def submit_code(self, code: str, url: str) -> str:
        """
        根据题目url提交代码, 并返回判题结果
        """
        self.page.goto(url=url)
        input_elem = self.page.get_by_role("textbox", name="Editor content;Press Alt+F1")
        input_elem.press("CapsLock")
        self.page.wait_for_timeout(10000)
        # 清空输入框
        self._clear_lt_code(input_elem)
        # 对力口编辑器做过适配的输入
        self._input_code_for_leetcode(input_elem, code, 100, 30000)
        # 原始输入
        # input_elem.press_sequentially(code, delay=100, timeout=60000)
        self.page.keyboard.press("Control+Enter")

        message = self._check_success()
        print(message)
        return message

    def get_question_description(self, url: str) -> str:
        """
        根据url得到题目描述信息
        """
        self.page.goto(url=url)
        element = self.page.locator("[data-track-load='description_content']")
        return element.inner_text()

    def get_question_solution(self) -> str:
        """
        获取题解信息
        """
        solution_url = self.url + "/solution/"
        self.page.goto(solution_url, timeout=30000)
        self.page.locator("span").filter(has_text="Python3").click()
        # 等待特定元素出现
        self.page.wait_for_selector(
            "div.transition-opacity > div.relative > div.flex-col > div.group", 
            timeout=30000
        )
        # 获取所有又带group属性的div元素
        locators = self.page.locator("div.transition-opacity > div.relative > div.flex-col > div.group")
        div_list = locators.all()
        # 查看获取元素数量
        print("题解数量：", locators.count())
        if locators.count() < self.idx_now_solve:
            return "你已看完所有题解如果还没有思路请返回题解中的python3代码"
        div_list[self.idx_now_solve].click()
        self.idx_now_solve += 1
        self.page.wait_for_selector("div.break-words", timeout=10000)
        content = self.page.locator("div.break-words").filter(has_text="python")
        return content.inner_text()
    
    def check_submit_status(self):
        """
        检查提交状态查看该题是否通过
        return: 通过/未通过/会员专享
        如果返回通过代表题目完成
        如果返回未通过代表题目未完成
        如果返回会员专享代表题目不需要提交代码
        """
        url = self.url + "/submissions/"
        self.page.goto(url)
        success = self.page.locator("div.flex").filter(has_text="通过")
        vip = self.page.locator("div.flex").filter(has_text="该题目是 Plus 会员专享题")
        self.page.wait_for_timeout(3000)
        # 检查是否能做
        if vip.count() > 0:
            return SubmitStatus.VIP
        # 检查是否有a题记录
        if success.count() > 0:
            return SubmitStatus.SUCCESS
        else:
            return SubmitStatus.ERROR

    def __del__(self):
        """
        析构函数，确保资源被正确释放
        """
        self.close()

    def close(self):
        """
        关闭浏览器和playwright资源
        """
        try:
            if self.page:
                self.page.close()
                self.page = None
        except Exception as e:
            print(f"关闭page时出错: {e}")

        try:
            if self.context:
                self.context.close()
                self.context = None
        except Exception as e:
            print(f"关闭context时出错: {e}")

        try:
            if self.browser:
                self.browser.close()
                self.browser = None
        except Exception as e:
            print(f"关闭browser时出错: {e}")

        try:
            if self.playwright:
                self.playwright.stop()
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
            "get_question_sloution": self.get_question_solution,
            "get_question_description": self.get_question_description,
            "submit_code": self.submit_code,
            "check_submit_status": self.check_submit_status,
        }

        enabled_tools = []


        for tool_name in tool_map.keys():
            tool = FunctionTool(
                cast(Callable[..., Any], tool_map[tool_name])
            )
            enabled_tools.append(tool)

        logger.info(f"Returning {len(enabled_tools)} enabled tools")
        return enabled_tools


# 使用示例
if __name__ == "__main__":
    operator = LeetCodeOperator()
    url = "https://leetcode.cn/problems/substring-with-concatenation-of-all-words/"
    code =  '''class Solution:\n    def isMatch(self, s: str, p: str) -> bool:\n        len_s = len(s)\n        len_p = len(p)\n        dp = [[False] * (len_p + 1) for _ in range(len_s + 1)]\n        dp[0][0] = True\n        \n        for j in range(1, len_p + 1):\n            if p[j-1] == '*':\n                dp[0][j] = dp[0][j-2]\n        \n        for i in range(1, len_s + 1):\n            for j in range(1, len_p + 1):\n                if p[j-1] == s[i-1] or p[j-1] == '.':\n                    dp[i][j] = dp[i-1][j-1]\n
   elif p[j-1] == '*':\n                    dp[i][j] = dp[i][j-2]\n                    if p[j-2] == s[i-1] or p[j-2] == '.':\n                        dp[i][j] |= dp[i-1][j]\n                else:\n                    dp[i][j] = False\n        return dp[len_s][len_p]",'''
    operator.set_url(url)
    try:
       # print(operator.get_question_solution())
        print(operator.submit_code(code=code, url=url))
       # print(operator.check_success(url=url))
    finally:
        print("over")
        #operator.close()