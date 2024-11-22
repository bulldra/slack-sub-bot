import json
import os

import utils.scraping_utils as scraping_utils

with open("secrets.json", "r", encoding="utf-8") as f:
    os.environ["SECRETS"] = json.dumps(json.load(f))


def test_download_audio():
    url = "https://www.youtube.com/watch?v=fpRwVhHbiPw&t=12s"
    text = scraping_utils.transcribe_youtube(url)
    print(text)
