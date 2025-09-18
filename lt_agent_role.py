from camel.agents import ChatAgent
from camel.models import ModelFactory
from camel.types import ModelPlatformType
from camel.toolkits import FunctionTool
from LeetCodeOperator import LeetCodeOperator
from As_LeetCodeOperator import AsLeetCodeOperator
from camel.societies import RolePlaying



import os
from dotenv import load_dotenv
load_dotenv()

MODESCOPE_API_KEY = os.getenv("MODELSCOPE_API")

glm_model = ModelFactory.create(
    model_platform=ModelPlatformType.MODELSCOPE,
    model_type="ZhipuAI/GLM-4.5",
    api_key=MODESCOPE_API_KEY,
    model_config_dict={"temperature": 0.1, "max_tokens": 8192, "top_p": 0.9}
)

model = ModelFactory.create(
    model_platform=ModelPlatformType.INTERNLM,
    model_type="internlm2.5-latest",
    api_key=os.getenv('shusheng')
)

leetCodeOperator = LeetCodeOperator()

question_url = "https://leetcode.cn/problems/count-bowl-subarrays/description/"
task_prompt = f"""
请用python3解决该网页{question_url}的算法题
    1.你需要仔细阅读题目描述,理解完题目后开始思考
    2.思考完成后开始编写代码
    你需要注意你是在编辑器中编码的如果你想要让你的代码正确的缩进你需要使用self.page.keyboard.press('backspace')来让你的
    光标位置前进到该行的首位,其次每次回车前要加上空格不然会导致代码格式错误。
    示例：
    源代码:
    '''class Solution:
    def convert(self, s: str, numRows: int) -> str:
        if numRows == 1 or numRows >= len(s):
            return s
        rows = [''] * numRows
        curRow = 0
        goingDown = False
        for char in s:
            rows[curRow] += char
            if curRow == 0 or curRow == numRows - 1:
                goingDown = not goingDown
            curRow += 1 if goingDown else -1
        return ''.join(rows)
    '''
    你应该输出的代码:
    '''class Solution:
    self.page.keyboard.press('backspace'), 1
    def convert(self, s: str, numRows: int) -> str:
    self.page.keyboard.press('backspace'), 2
        if numRows == 1 or numRows >= len(s):
        self.page.keyboard.press('backspace'), 3
            return s
        self.page.keyboard.press('backspace'), 2
        rows = [''] * numRows
        self.page.keyboard.press('backspace'), 2
        curRow = 0
        self.page.keyboard.press('backspace'), 2
        goingDown = False
        self.page.keyboard.press('backspace'), 2
        for char in s:
        self.page.keyboard.press('backspace'), 3
            rows[curRow] += char
            self.page.keyboard.press('backspace'), 3
            if curRow == 0 or curRow == numRows - 1:
            self.page.keyboard.press('backspace'), 4
                goingDown = not goingDown
            self.page.keyboard.press('backspace'), 3
            curRow += 1 if goingDown else -1
            self.page.keyboard.press('backspace'), 2
        return ''.join(rows) 
    '''
    5.确定代码没问题,提交代码
    6. 如果代码通过则任务完成
    7. 如果代码没有通过，调用题解开始查看该题的思路
    8. 根据错误信息和思路重新编写代码再提交
    9.如果未完成则重复2-9步骤,完成后退出
    tips:
    你必须要根据错误信息调整自己的操作
    """
def get_kargs(asLeetCodeOperator: AsLeetCodeOperator):
    r"""
    获取角色扮演的参数
    """
    task_kwargs = {
        "task_prompt": task_prompt,
        "with_task_specify": True,
        "task_specify_agent_kwargs": dict(model=model),
    }

    user_kwargs = {
        "user_role_name": "一个经验丰富的leetcode竞赛选手",
        "user_agent_kwargs": {"model": model},
    }
   
    assistant_kwargs = {
        "assistant_role_name": "可以操作leetcode网页的最优秀的python代码编辑专家",
        "assistant_agent_kwargs": {"model": ChatAgent(
            model=glm_model,
            tools=[*asLeetCodeOperator.get_tools()],
            output_language='中文'
        )},
    }

    return task_kwargs, user_kwargs, assistant_kwargs

def is_terminated(response):
    r"""
    当会话终止时给出对应的信息
    """
    if response.terminated:
        role = response.msg.role_type.name if response.msg.role_type else "None"
        reason = response.info["termination_reasons"]
        print(f"AI {role} 因为 {reason} 终止")

    return response.terminated

def run(society, round_limit: int = 10) -> None:
    r"""
    运行一个多轮对话，直到达到回合限制或会话终止。
    """
    input_msg = society.init_chat()
    for _ in range(round_limit):
        usr_response, assistant_response = society.step(input_msg)
        if is_terminated(usr_response) or is_terminated(assistant_response):
            break
        print(f"用户给出的信息： {usr_response.msg.content}.\n")
        if "CAMEL_TASK_DONE" in usr_response.msg.content:
            print("任务完成，结束对话。")
            break
        print(f"助手给出的信息： {assistant_response.msg.content}.\n")

        input_msg = assistant_response.msg
    return None

async def main():
    asLeetCodeOperator = AsLeetCodeOperator()
    # 初始化浏览器
    await asLeetCodeOperator.start_chrome_with_debug()
    await asLeetCodeOperator.init_browser()

    task_kwargs, user_kwargs, assistant_kwargs = get_kargs(asLeetCodeOperator=asLeetCodeOperator)

    society = RolePlaying(
        **task_kwargs,
        **user_kwargs,
        **assistant_kwargs,
        output_language='中文' 
    )
    
    # 确保在程序结束时关闭浏览器
    try:
        run(society)
    finally:
        await asLeetCodeOperator.close()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())