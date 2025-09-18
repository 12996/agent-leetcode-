import json
from camel.agents import ChatAgent
from camel.models import ModelFactory
from camel.types import ModelPlatformType
from LeetCodeOperator import LeetCodeOperator


import os
from dotenv import load_dotenv
load_dotenv()

MODESCOPE_API_KEY = os.getenv("MODELSCOPE_API")

glm_model = ModelFactory.create(
    model_platform=ModelPlatformType.MODELSCOPE,
    model_type="ZhipuAI/GLM-4.5",
    api_key=MODESCOPE_API_KEY,
    model_config_dict={"temperature": 0.1, "max_tokens": 8192}
)

model = ModelFactory.create(
    model_platform=ModelPlatformType.INTERNLM,
    model_type="intern-s1",
    api_key=os.getenv('shusheng'),
    model_config_dict={"temperature": 0.1}
)


                 
leetCodeOperator = LeetCodeOperator()
agent = ChatAgent(
    system_message="你是一个出色的leetcode竞赛选手, 你的任务是:完成网页题目代码的编写并提交，当提交返回success时结束任务,永远不要破坏输出格式不要输出多个答案， 注意：当判断代码正确时结束任务,",
    model=model,
    tools=[*leetCodeOperator.get_tools()],
    max_iteration=3,
)

def task_prompt(url, is_submit=False):
    question_solution = "get_question_solution"

    if is_submit:
        question_solution = leetCodeOperator.get_question_solution()

    task_prompt_str = f"""
    请用python3解决该网页{url}的算法题
        1.你需要仔细阅读题目和题解描述，理解完题目后开始思考
        2.思考完成后开始编写代码(请注意leetcode代码前两行是固定格式)
        代码请以class Solution: 开头
        示例：
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
        5.确定代码没问题,提交代码
        6. 提交代码通过,任务结束
        7. 如果没有通过, 获取题解{question_solution}开始查看该题的思路
        8. 然后根据题解信息和报错信息重新编写代码再提交
        tips:
        提交代码通过后任务结束
    """  
    return task_prompt_str

if __name__ == "__main__":
    question_txt = r"F:\python_P\project\camel-ai_agent\question.txt"
    question_message_list = []
    with open(question_txt, "r", encoding="utf-8") as f:
        for line in f.readlines():
            question_message_list.append(json.loads(line))
    print(f"{question_message_list[0].get("submit_status", "")}")

    try:
        for i in range(len(question_message_list)):
            question = question_message_list[i]
            agent.reset()
            leetCodeOperator.set_url(question["url"])
            task_prompt_str = task_prompt(question["url"])
            if question.get("submit_status") == "提交未通过":
                task_prompt_str = task_prompt(question["url"])
            if question.get("submit_status") == "通过":
                continue

            status = leetCodeOperator.check_submit_status()
            if status == "通过" or status == "会员专享":
                question.update({"submit_status": status})
                question_message_list[i] = question
                continue
            response = agent.step(task_prompt_str)
            # print(response.msgs[0].content if response.msgs else "<no response>")
            # print(response.info['tool_calls'])
            question["submit_status"] = leetCodeOperator.check_submit_status()
            question_message_list[i] = question
    except Exception as e:
        print(e)
    finally:
        with open(question_txt, "w", encoding="utf-8") as f:
            for question in question_message_list:
                f.write(json.dumps(question, ensure_ascii=False) + "\n") 
        leetCodeOperator.close()