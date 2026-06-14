import pytest
from harness.tools.registry import ToolRegistry
from harness.tools.builtin.file_ops import register_file_tools


class TestFileOps:
    @pytest.fixture
    def registry(self):
        reg = ToolRegistry()
        register_file_tools(reg)
        return reg

    def test_write_and_read_file(self, registry, tmp_path):
        path = str(tmp_path / "test.txt")
        registry.execute("write_file", {"path": path, "content": "Hello World"})
        result = registry.execute("read_file", {"path": path})
        assert result == "Hello World"

    def test_edit_file(self, registry, tmp_path):
        path = str(tmp_path / "test.py")
        registry.execute("write_file", {"path": path, "content": "def foo():\n    return 1"})
        registry.execute("edit_file", {"path": path, "old_string": "return 1", "new_string": "return 42"})
        result = registry.execute("read_file", {"path": path})
        assert "return 42" in result

    def test_read_nonexistent(self, registry):
        result = registry.execute("read_file", {"path": "/nonexistent/file.txt"})
        assert "Error" in result
