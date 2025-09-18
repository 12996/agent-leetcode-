import re
from playwright.sync_api import sync_playwright, expect
from playwright.sync_api import Page
import subprocess
import os
import time
# 添加socket模块用于检查端口
import socket

class LeetCodeOperator:
    def __init__(self):
        self start_chrome_with_debug()
    def check_success():
    #    page.goto(url=url)
        result = page.locator("div.items-center").filter(has_text="通过的测试用例").nth(0).locator("span").nth(0)
        print(result.inner_text())
        if result.inner_text().find("通过") != -1:
        return "通过"
        else:
        message = page.locator("div.break-all").nth(0)
        return f"未通过:{message.text_content()}"
        
    def upload_code(page:Page, code: str, url: str) -> None:
        """
        提交代码，并返回判题结果
        """
        page.goto(url=url)
        input = page.get_by_role("textbox", name="Editor content;Press Alt+F1")
        input.press("CapsLock")
        page.wait_for_timeout(15000)
        input.clear()
        input.press_sequentially(code, delay=100, timeout=60000)
        page.keyboard.press("Control+Enter")  

        message = check_success()
        return message

    def get_description(url: str) -> str:
        """
        得到题目描述信息
        """
        user_manual_input = "http://localhost:9222/"
        with sync_playwright() as playwright:
            browser = playwright.chromium.connect_over_cdp(user_manual_input)
            context = browser.contexts[0]
            page = context.pages[0]
            page.goto(url=url)
            element = page.locator("[data-track-load='description_content']")
            res = element.inner_text()

            page.close()
            context.close()

        return res
    def get_question_slove(url: str) -> None:
        """
        根据url获取题目题解
        """
        user_manual_input = "http://localhost:9222/"
        with sync_playwright() as playwright:
            browser = playwright.chromium.connect_over_cdp(user_manual_input)
            context = browser.contexts[0]
            page = context.pages[0]
            url = url + "/solution/"
            page.goto(url, timeout=30000)
            # page.get_by_text("题解").nth(1).click()
            page.locator("span").filter(has_text="Python3").click()
            # 等待特定元素出现
            page.wait_for_selector("div.transition-opacity > div.relative > div.flex-col > div.group", timeout=30000)
            # 获取所有又带group属性的div元素
            locators = page.locator("div.transition-opacity > div.relative > div.flex-col > div.group")
            div_list = locators.all()
            # 查看获取元素数量
            print("题解数量：", locators.count())
            div_list[0].click()
            page.wait_for_selector("div.break-words", timeout=10000)
            content = page.locator("div.break-words").filter(has_text="python")
            res = content.inner_text()
            page.close()
            context.close()
            browser.close()
            
        return res

    def get_page():
        """
        返回一个可以操作的page对象
        可以供函数调用进行浏览器操作
        """
        user_manual_input = "http://localhost:9222/"
        with sync_playwright() as playwright:
            browser = playwright.chromium.connect_over_cdp(user_manual_input)
            context = browser.contexts[0]
            page = context.pages[0]
            get_question_slove(page, url)
            return page
        
    def start_manual_browser():

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

        def start_chrome_with_debug():
            """
            启动带调试端口的 Chrome 浏览器
            """
            # 检查9222端口是否被占用
            debug_port = 9222
            if is_port_in_use(debug_port):
                print(f"错误：端口 {debug_port} 已被占用，可能 Chrome 浏览器已经在运行")
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
                process = subprocess.Popen(chrome_cmd)
                # 等待一段时间让程序运行
                time.sleep(2)
                print("\nChrome 浏览器已成功启动")
                print("调试端口:", debug_port)
                return process
            except Exception as e:
                print(f"启动 Chrome 浏览器时出错: {e}")
                return False

    if __name__ == "__main__":
        start_manual_browser()
        url = "https://leetcode.cn/problems/minimum-operations-to-transform-string/"
        code = """class Solution:
        def minOperations(self, s: str) -> int:
            # 'z' 的下一个字符是 '{'
            min_c = min((c for c in s if c != 'a'), default='{')
            return ord('{') - ord(min_c)
    """
        print(get_description(url))
        # print(upload_code(code=code, url=url))
        print(get_question_slove(url=url))
    