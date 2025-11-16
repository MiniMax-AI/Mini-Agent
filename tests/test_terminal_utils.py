"""Tests for terminal_utils module."""

import pytest

from ye_linghua.utils import (
    calculate_display_width,
    pad_to_width,
    truncate_with_ellipsis,
)


class TestCalculateDisplayWidth:
    """Tests for calculate_display_width function."""

    def test_ascii_text(self):
        """Test ASCII text width calculation."""
        assert calculate_display_width("Hello") == 5
        assert calculate_display_width("World") == 5
        assert calculate_display_width("Test 123") == 8

    def test_empty_string(self):
        """Test empty string."""
        assert calculate_display_width("") == 0

    def test_emoji(self):
        """Test emoji width (should count as 2)."""
        assert calculate_display_width("🤖") == 2
        assert calculate_display_width("💭") == 2
        assert calculate_display_width("🤖 Agent") == 8  # 2 + 1 + 5

    def test_chinese_characters(self):
        """Test Chinese characters (each counts as 2)."""
        assert calculate_display_width("你好") == 4
        assert calculate_display_width("你好世界") == 8
        assert calculate_display_width("中文") == 4

    def test_japanese_characters(self):
        """Test Japanese characters."""
        assert calculate_display_width("日本語") == 6  # 3 chars * 2

    def test_mixed_content(self):
        """Test mixed ASCII and wide characters."""
        assert calculate_display_width("Hello 你好") == 10  # 5 + 1 + 4
        assert calculate_display_width("Test 🤖") == 7  # 4 + 1 + 2

    def test_ansi_codes_ignored(self):
        """Test that ANSI escape codes are not counted."""
        colored = "\033[31mRed\033[0m"
        assert calculate_display_width(colored) == 3

        colored_emoji = "\033[31m🤖\033[0m"
        assert calculate_display_width(colored_emoji) == 2

    def test_combining_characters(self):
        """Test combining characters (should not add width)."""
        # é = e + combining acute accent
        e_with_accent = "e\u0301"
        assert calculate_display_width(e_with_accent) == 1

    def test_complex_ansi_sequences(self):
        """Test complex ANSI sequences."""
        text = "\033[1m\033[36mBold Cyan\033[0m"
        assert calculate_display_width(text) == 9  # "Bold Cyan"


class TestTruncateWithEllipsis:
    """Tests for truncate_with_ellipsis function."""

    def test_no_truncation_needed(self):
        """Test when text fits within width."""
        assert truncate_with_ellipsis("Hello", 10) == "Hello"
        assert truncate_with_ellipsis("Test", 5) == "Test"

    def test_exact_fit(self):
        """Test when text exactly fits."""
        assert truncate_with_ellipsis("Hello", 5) == "Hello"

    def test_ascii_truncation(self):
        """Test truncation of ASCII text."""
        assert truncate_with_ellipsis("Hello World", 8) == "Hello W…"
        assert truncate_with_ellipsis("Testing", 4) == "Tes…"

    def test_chinese_truncation(self):
        """Test truncation with Chinese characters."""
        result = truncate_with_ellipsis("你好世界", 5)
        # Should be: 你好 (4 width) + … (1 width) = 5
        assert calculate_display_width(result) <= 5
        assert "…" in result

    def test_emoji_truncation(self):
        """Test truncation with emoji."""
        result = truncate_with_ellipsis("🤖🤖🤖", 3)
        # Should be: 🤖 (2 width) + … (1 width) = 3
        assert calculate_display_width(result) <= 3

    def test_zero_width(self):
        """Test with zero width."""
        assert truncate_with_ellipsis("Hello", 0) == ""

    def test_width_one(self):
        """Test with width of 1."""
        result = truncate_with_ellipsis("Hello", 1)
        assert len(result) <= 1

    def test_ansi_codes_removed(self):
        """Test that ANSI codes are removed during truncation."""
        colored = "\033[31mHello World\033[0m"
        result = truncate_with_ellipsis(colored, 8)
        # ANSI codes should be removed
        assert "\033[" not in result
        assert "…" in result


class TestPadToWidth:
    """Tests for pad_to_width function."""

    def test_left_align(self):
        """Test left alignment (default)."""
        result = pad_to_width("Hello", 10)
        assert result == "Hello     "
        assert len(result) == 10

    def test_right_align(self):
        """Test right alignment."""
        result = pad_to_width("Hello", 10, align="right")
        assert result == "     Hello"
        assert len(result) == 10

    def test_center_align(self):
        """Test center alignment."""
        result = pad_to_width("Test", 10, align="center")
        assert result == "   Test   "
        assert len(result) == 10

    def test_center_align_odd(self):
        """Test center alignment with odd padding."""
        result = pad_to_width("Hi", 7, align="center")
        # Should be: "  Hi   " or "   Hi  " (either is acceptable)
        assert "Hi" in result
        assert len(result) == 7

    def test_chinese_padding(self):
        """Test padding with Chinese characters."""
        result = pad_to_width("你好", 10)
        # "你好" is 4 display width, so needs 6 spaces
        assert calculate_display_width(result) == 10

    def test_emoji_padding(self):
        """Test padding with emoji."""
        result = pad_to_width("🤖", 10)
        # "🤖" is 2 display width, so needs 8 spaces
        assert calculate_display_width(result) == 10

    def test_no_padding_needed(self):
        """Test when text already reaches target width."""
        result = pad_to_width("Hello", 5)
        assert result == "Hello"

    def test_text_exceeds_width(self):
        """Test when text exceeds target width."""
        result = pad_to_width("Hello World", 5)
        assert result == "Hello World"  # No truncation, just return as-is

    def test_invalid_align(self):
        """Test invalid alignment value."""
        with pytest.raises(ValueError, match="Invalid align value"):
            pad_to_width("Test", 10, align="invalid")

    def test_custom_fill_char(self):
        """Test custom fill character."""
        result = pad_to_width("Test", 10, fill_char="-")
        assert result == "Test------"


class TestRealWorldScenarios:
    """Tests for real-world usage scenarios."""

    def test_step_header(self):
        """Test Step header formatting (from agent.py)."""
        step = 1
        max_steps = 50
        step_text = f"💭 Step {step}/{max_steps}"

        width = calculate_display_width(step_text)
        # "💭" (2) + " Step 1/50" (10) = 12
        assert width == 12

    def test_session_info_model(self):
        """Test Session Info model line."""
        model = "minimax-01"
        line = f"Model: {model}"
        width = calculate_display_width(line)
        # Should calculate correctly regardless of model name
        assert width > 0

    def test_chinese_model_name(self):
        """Test with Chinese model name."""
        model = "模型-01"
        line = f"Model: {model}"
        width = calculate_display_width(line)
        # "Model: " (7) + "模型-01" (2+2+3) = 14
        assert width == 14

    def test_banner_text(self):
        """Test banner text from cli.py."""
        banner = "🤖 Mini Agent - Multi-turn Interactive Session"
        width = calculate_display_width(banner)
        # "🤖" (2) + " Mini Agent - Multi-turn Interactive Session" (44) = 46
        assert width == 46
