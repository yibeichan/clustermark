"""
Test suite for EpisodeService folder parsing functionality.

Tests cover:
- SxxEyy_cluster-N format parsing
- SxxEyy_CharacterName format parsing
- Legacy cluster_N format parsing
- Fallback for unknown formats
- Case-insensitive parsing
- Security (path traversal prevention)
- Mixed format handling
"""

from unittest.mock import Mock

import pytest
from app.services.episode_service import EpisodeService


class TestFolderNameParsing:
    """Test folder name parsing with various formats."""

    def test_parse_friends_format_with_suffix_a(self):
        """
        Test parsing friends_s01e01a_cluster-XXX format.

        Expected: season=1, episode=1, cluster=730, label="cluster-730"
        Suffix 'a' should be ignored.
        """
        service = EpisodeService(Mock())
        result = service._parse_folder_name("friends_s01e01a_cluster-730")

        assert result["season"] == 1
        assert result["episode"] == 1
        assert result["cluster_number"] == 730
        assert result["label"] == "cluster-730"

    def test_parse_friends_format_with_suffix_b(self):
        """
        Test parsing friends_s01e01b_cluster-XXX format.

        Expected: season=1, episode=1, cluster=436, label="cluster-436"
        Suffix 'b' should be ignored - maps to same episode as 'a'.
        """
        service = EpisodeService(Mock())
        result = service._parse_folder_name("friends_s01e01b_cluster-436")

        assert result["season"] == 1
        assert result["episode"] == 1
        assert result["cluster_number"] == 436
        assert result["label"] == "cluster-436"

    def test_parse_friends_format_without_prefix(self):
        """
        Test parsing s01e01a_cluster-XXX format (no 'friends_' prefix).

        Expected: season=1, episode=1, cluster=25, label="cluster-25"
        """
        service = EpisodeService(Mock())
        result = service._parse_folder_name("s01e01a_cluster-25")

        assert result["season"] == 1
        assert result["episode"] == 1
        assert result["cluster_number"] == 25
        assert result["label"] == "cluster-25"

    def test_parse_friends_format_uppercase(self):
        """
        Test parsing FRIENDS_S01E01A_CLUSTER-XXX format (case-insensitive).

        Expected: season=1, episode=1, cluster=100, label="cluster-100"
        """
        service = EpisodeService(Mock())
        result = service._parse_folder_name("FRIENDS_S01E01A_CLUSTER-100")

        assert result["season"] == 1
        assert result["episode"] == 1
        assert result["cluster_number"] == 100
        assert result["label"] == "cluster-100"

    def test_parse_sxxeyy_cluster(self):
        """
        Test parsing SxxEyy_cluster-N format.

        Expected: season=1, episode=5, cluster=23, label="cluster-23"
        """
        # Use mock DB since we're only testing parser logic
        service = EpisodeService(Mock())
        result = service._parse_folder_name("S01E05_cluster-23")

        assert result["season"] == 1
        assert result["episode"] == 5
        assert result["cluster_number"] == 23
        assert result["label"] == "cluster-23"

    def test_parse_sxxeyy_character(self):
        """
        Test parsing SxxEyy_CharacterName format.

        Expected: season=1, episode=5, label="Rachel"
        """
        service = EpisodeService(Mock())
        result = service._parse_folder_name("S01E05_Rachel")

        assert result["season"] == 1
        assert result["episode"] == 5
        assert result["label"] == "Rachel"
        assert "cluster_number" not in result

    def test_parse_legacy_cluster(self):
        """
        Test parsing legacy cluster_N format.

        Expected: cluster=123, label="cluster_123"
        """
        service = EpisodeService(Mock())
        result = service._parse_folder_name("cluster_123")

        assert result["cluster_number"] == 123
        assert result["label"] == "cluster_123"
        assert "season" not in result
        assert "episode" not in result

    def test_parse_fallback(self):
        """
        Test fallback for unknown format.

        Expected: label="AnyName" (preserves original name)
        """
        service = EpisodeService(Mock())
        result = service._parse_folder_name("AnyName")

        assert result["label"] == "AnyName"
        assert "season" not in result
        assert "episode" not in result
        assert "cluster_number" not in result

    def test_case_insensitive(self):
        """
        Test case-insensitive parsing.

        Both lowercase and uppercase should work.
        """
        service = EpisodeService(Mock())

        # Lowercase
        result_lower = service._parse_folder_name("s01e05_cluster-23")
        assert result_lower["season"] == 1
        assert result_lower["episode"] == 5
        assert result_lower["cluster_number"] == 23

        # Mixed case
        result_mixed = service._parse_folder_name("S01e05_Rachel")
        assert result_mixed["season"] == 1
        assert result_mixed["episode"] == 5
        assert result_mixed["label"] == "Rachel"

    def test_parse_with_leading_zeros(self):
        """
        Test parsing with leading zeros removed.

        S01E05 should parse as season=1, episode=5 (not 01, 05)
        """
        service = EpisodeService(Mock())
        result = service._parse_folder_name("S01E05_Monica")

        assert result["season"] == 1
        assert result["episode"] == 5
        assert result["label"] == "Monica"

    def test_sanitize_path_traversal(self):
        """
        Test security: reject path traversal attempts.

        Should sanitize dangerous characters: .., /, \, null bytes
        """
        service = EpisodeService(Mock())

        # Path traversal attempts
        sanitized1 = service._sanitize_folder_name("../etc/passwd")
        assert ".." not in sanitized1
        assert "/" not in sanitized1

        sanitized2 = service._sanitize_folder_name("..\\windows\\system32")
        assert ".." not in sanitized2
        assert "\\" not in sanitized2

        # Null byte injection
        sanitized3 = service._sanitize_folder_name("cluster\x00.jpg")
        assert "\x00" not in sanitized3

    def test_multiple_underscores_in_name(self):
        """
        Test handling character names with underscores.

        Example: S01E05_Character_Name should parse correctly
        """
        service = EpisodeService(Mock())
        result = service._parse_folder_name("S01E05_Character_Name")

        assert result["season"] == 1
        assert result["episode"] == 5
        # Label should preserve underscores after SxxEyy
        assert "Character_Name" in result["label"]

    def test_empty_string(self):
        """
        Test handling empty string input.

        Should return fallback with empty label.
        """
        service = EpisodeService(Mock())
        result = service._parse_folder_name("")

        assert result["label"] == ""
        assert "season" not in result


class TestParsingEdgeCases:
    """Test edge cases and error handling."""

    def test_malformed_season_episode(self):
        """
        Test malformed SxxEyy format (non-numeric).

        Should fallback to treating as character name.
        """
        service = EpisodeService(Mock())
        result = service._parse_folder_name("SxxEyy_Rachel")

        # Should fallback since season/episode are not numeric
        assert result["label"] == "SxxEyy_Rachel"
        assert "season" not in result

    def test_cluster_with_non_numeric(self):
        """
        Test cluster_N format with non-numeric N.

        Should fallback to treating as regular name.
        """
        service = EpisodeService(Mock())
        result = service._parse_folder_name("cluster_abc")

        # Should fallback
        assert result["label"] == "cluster_abc"
        assert "cluster_number" not in result

    def test_very_long_name(self):
        """
        Test handling very long folder names (stress test).

        Should not crash, should parse or fallback gracefully.
        """
        service = EpisodeService(Mock())
        long_name = "A" * 1000
        result = service._parse_folder_name(long_name)

        assert result["label"] == long_name

    def test_special_characters_in_name(self):
        """
        Test special characters in folder names.

        Should preserve safe special characters, sanitize dangerous ones.
        """
        service = EpisodeService(Mock())
        result = service._parse_folder_name("S01E05_Rachel-Ross")

        assert result["season"] == 1
        assert result["episode"] == 5
        assert "Rachel-Ross" in result["label"]

    def test_whitespace_handling(self):
        """
        Test folder names with leading/trailing whitespace.

        Should strip whitespace before parsing.
        """
        service = EpisodeService(Mock())
        result = service._parse_folder_name("  S01E05_Monica  ")

        assert result["season"] == 1
        assert result["episode"] == 5
        assert result["label"] == "Monica"
