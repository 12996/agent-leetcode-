class SubmitStatus:

    SUCCESS = "通过"
    ERROR = "提交未通过"
    VIP = "会员专享"

    def __init__(self, message: str):
        self._message = message

    def message(self) -> str:
        return self._message