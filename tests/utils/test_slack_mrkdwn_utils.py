import unittest

import utils.slack_mrkdwn_utils as slack_mrkdwn_utils


class TestBuildTextBlocks(unittest.TestCase):
    def test_link_not_split_across_blocks(self):
        # 3000文字付近にmrkdwnリンクがまたがるテキストを作成
        base_text = "a" * 2990
        link_text = "<https://example.com|Example Link>"
        text = base_text + link_text + "b" * 20  # 合計3000文字超え

        blocks = slack_mrkdwn_utils.build_text_blocks(text)
        # 各blockのtextを連結して元のテキストと比較
        reconstructed = "".join(block["text"]["text"] for block in blocks)

        # 元テキストと復元テキストは一致すること
        self.assertEqual(reconstructed, text)

        # さらに、リンクが途中で分割されていないことを確認
        for block in blocks:
            block_text = block["text"]["text"]
            # リンクの途中で切れていれば '<' の後に '>' がないか、'>' の前に '<' がないはず
            # ここでは単純に '<' と '>' の数を比較してリンクが壊れていないかチェック
            if "<" in block_text:
                self.assertTrue(">" in block_text)

    def test_build_and_convert_mrkdwn_blocks(self):
        with open("tests/utils/test_slack_mrkdwn_utils.md", "r", encoding="utf-8") as f:
            md_text = f.read()
        blocks = slack_mrkdwn_utils.build_and_convert_mrkdwn_blocks(md_text)
        print(blocks)


if __name__ == "__main__":
    unittest.main()
