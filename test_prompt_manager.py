"""프롬프트 관리 프로그램의 핵심 기능 테스트."""

import unittest
from io import StringIO
from unittest.mock import patch

import prompt_manager


class PromptManagerTest(unittest.TestCase):
    def setUp(self):
        self.prompts = prompt_manager.create_default_prompts()

    def test_default_prompts_are_at_least_three(self):
        self.assertGreaterEqual(len(self.prompts), 3)

    @patch("builtins.input", side_effect=["새 제목", "새 내용", "자동화"])
    def test_add_prompt(self, _mock_input):
        prompt_manager.add_prompt(self.prompts)
        self.assertEqual(len(self.prompts), 4)
        self.assertEqual(self.prompts[-1]["title"], "새 제목")
        self.assertFalse(self.prompts[-1]["favorite"])

    @patch("builtins.input", side_effect=["", "정상 입력"])
    def test_empty_input_is_requested_again(self, _mock_input):
        with patch("sys.stdout", new=StringIO()):
            value = prompt_manager.get_non_empty_input("값: ")
        self.assertEqual(value, "정상 입력")

    def test_prompt_list_shows_title_and_category(self):
        output = StringIO()
        with patch("sys.stdout", new=output):
            prompt_manager.show_prompt_list(self.prompts)
        self.assertIn("블로그 글 작성 도우미", output.getvalue())
        self.assertIn("텍스트 생성", output.getvalue())

    @patch("builtins.input", return_value="블로그")
    def test_search_prompts(self, _mock_input):
        output = StringIO()
        with patch("sys.stdout", new=output):
            prompt_manager.search_prompts(self.prompts)
        self.assertIn("블로그 글 작성 도우미", output.getvalue())

    @patch("builtins.input", return_value="1")
    def test_toggle_favorite(self, _mock_input):
        self.assertFalse(self.prompts[0]["favorite"])
        with patch("sys.stdout", new=StringIO()):
            prompt_manager.toggle_favorite(self.prompts)
        self.assertTrue(self.prompts[0]["favorite"])


if __name__ == "__main__":
    unittest.main()
