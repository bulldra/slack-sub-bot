import os

import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.environ["x-api-key"]

url = "https://chatai-48uaurqq.an.gateway.dev/planning"
header = {"x-api-key": api_key, "Content-Type": "application/json"}
payload = {"product": "MVNO携帯電話"}

res = requests.post(url, headers=header, json=payload)
print(res.text)
