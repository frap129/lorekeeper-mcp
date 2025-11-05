"""Tests to verify project directory structure is correctly created."""

from pathlib import Path


class TestProjectStructure:
    """Test that all required directories and files exist."""

    def test_source_directories_exist(self):
        """Source directories should exist."""
        required_dirs = [
            "src/lorekeeper_mcp",
            "src/lorekeeper_mcp/tools",
            "src/lorekeeper_mcp/cache",
            "src/lorekeeper_mcp/api_clients",
        ]
        for dir_path in required_dirs:
            assert Path(dir_path).is_dir(), f"Directory {dir_path} should exist"

    def test_source_init_files_exist(self):
        """All source __init__.py files should exist."""
        required_files = [
            "src/lorekeeper_mcp/__init__.py",
            "src/lorekeeper_mcp/tools/__init__.py",
            "src/lorekeeper_mcp/cache/__init__.py",
            "src/lorekeeper_mcp/api_clients/__init__.py",
        ]
        for file_path in required_files:
            assert Path(file_path).is_file(), f"File {file_path} should exist"

    def test_test_directories_exist(self):
        """Test directories should exist."""
        required_dirs = [
            "tests",
            "tests/test_cache",
        ]
        for dir_path in required_dirs:
            assert Path(dir_path).is_dir(), f"Directory {dir_path} should exist"

    def test_test_init_files_exist(self):
        """All test __init__.py files should exist."""
        required_files = [
            "tests/__init__.py",
            "tests/test_cache/__init__.py",
        ]
        for file_path in required_files:
            assert Path(file_path).is_file(), f"File {file_path} should exist"

    def test_data_directory_exists(self):
        """Data directory should exist with .gitkeep."""
        assert Path("data").is_dir(), "Directory data should exist"
        assert Path("data/.gitkeep").is_file(), "File data/.gitkeep should exist"

    def test_gitignore_content(self):
        """GitIgnore should contain required content."""
        gitignore_path = Path(".gitignore")
        assert gitignore_path.is_file(), ".gitignore should exist"

        content = gitignore_path.read_text()

        required_lines = [
            "# Data directory (except .gitkeep)",
            "data/*",
            "!data/.gitkeep",
            "# Python",
            "__pycache__/",
            "*.py[cod]",
            "*$py.class",
            ".pytest_cache/",
            ".coverage",
            "htmlcov/",
            "# Environment",
            ".env",
            ".venv/",
            "venv/",
            "# IDE",
            ".vscode/",
            ".idea/",
            "*.swp",
            "*.swo",
        ]

        for line in required_lines:
            assert line in content, f".gitignore should contain '{line}'"
