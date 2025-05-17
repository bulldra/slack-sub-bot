[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/bulldra/slack-sub-bot)

## 変更点

* メールを受信して投稿したメッセージに対して自動的にSlackのブックマークを追加し、未読管理をしやすくしました.

## Setup

1. Install dependencies

```bash
pip install -r src/requirements.txt
```

2. Prepare environment variables

Set the `SECRETS` environment variable with a JSON string containing keys like
`SLACK_BOT_TOKEN`, `SLACK_USER_TOKEN` and `OPENAI_API_KEY`.

Example:

```bash
export SECRETS='{"SLACK_BOT_TOKEN":"xoxb-...","SLACK_USER_TOKEN":"xoxp-...","OPENAI_API_KEY":"sk-..."}'
```

3. Run tests

```bash
pytest
```

## Usage

Deploy the Cloud Function with `deploy.sh` or invoke `main` locally for testing.
