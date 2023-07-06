import os

import openai
from flask import request

from chatbot import ChatBot


def exeute(req: dict) -> str:
    openai.api_key = os.getenv("OPENAI_API_KEY")

    c = ChatBot()
    product = req.get("product", "チャット")

    res = (
        c.completion(
            f"""${product}について教えてください。
        """
        )
        + "\n"
    )
    return res


def main(request: request) -> str:
    req = request.get_json()
    return exeute(req)
