import pytest
from harness.session.session import Session, Message


class TestMessage:
    def test_create_user_message(self):
        msg = Message(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"
        assert msg.timestamp is not None

    def test_create_tool_message(self):
        msg = Message(role="tool", content="file contents", tool_call_id="tc-123")
        assert msg.tool_call_id == "tc-123"

    def test_to_dict(self):
        msg = Message(role="user", content="Hello")
        d = msg.to_dict()
        assert d["role"] == "user"
        assert d["content"] == "Hello"

    def test_from_dict(self):
        d = {"role": "user", "content": "Hello", "timestamp": "2026-01-01T00:00:00Z"}
        msg = Message.from_dict(d)
        assert msg.content == "Hello"


class TestSession:
    def test_create_session(self):
        session = Session()
        assert session.id is not None
        assert len(session.messages) == 0

    def test_add_messages(self):
        session = Session()
        session.add_user_message("Hello")
        session.add_assistant_message("Hi there!")
        assert len(session.messages) == 2
        assert session.messages[0].role == "user"
        assert session.messages[1].role == "assistant"

    def test_add_tool_call_and_result(self):
        session = Session()
        session.add_user_message("Read file")
        session.add_assistant_message("", tool_calls=[{"id": "tc-1", "name": "read_file", "arguments": {"path": "test.py"}}])
        session.add_tool_result("tc-1", "file contents")
        assert len(session.messages) == 3
        assert session.messages[2].role == "tool"

    def test_to_dict_roundtrip(self):
        session = Session()
        session.add_user_message("Hello")
        session.add_assistant_message("Hi!")
        d = session.to_dict()
        restored = Session.from_dict(d)
        assert len(restored.messages) == 2
        assert restored.messages[0].content == "Hello"

    def test_auto_title(self):
        session = Session()
        session.add_user_message("Fix the DDP memory leak in training script")
        assert "DDP" in session.title or "memory" in session.title
