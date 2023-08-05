import os

import dotenv
import slack_sdk

dotenv.load_dotenv(verbose=True)

client = slack_sdk.WebClient(token=os.environ.get("SLACK_BOT_TOKEN"))


channel_id = "C05GDA42HJ5"
message_ts = "1690789293.047379"
result = client.chat_postMessage(
    channel=channel_id, thread_ts=message_ts, text="Hello again :wave:"
)
