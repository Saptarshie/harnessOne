import pytest
from harness.session.manager import SessionManager
from harness.session.session import Session


class TestSessionManager:
    def test_create_session(self, tmp_path):
        mgr = SessionManager(str(tmp_path))
        sid = mgr.create_session()
        assert sid is not None
        assert mgr.load_session(sid) is not None

    def test_save_and_load(self, tmp_path):
        mgr = SessionManager(str(tmp_path))
        session = Session()
        session.add_user_message("Hello")
        mgr.save_session(session)
        loaded = mgr.load_session(session.id)
        assert loaded.messages[0].content == "Hello"

    def test_list_sessions(self, tmp_path):
        mgr = SessionManager(str(tmp_path))
        mgr.create_session()
        mgr.create_session()
        sessions = mgr.list_sessions()
        assert len(sessions) == 2

    def test_delete_session(self, tmp_path):
        mgr = SessionManager(str(tmp_path))
        sid = mgr.create_session()
        mgr.delete_session(sid)
        assert mgr.load_session(sid) is None

    def test_auto_save(self, tmp_path):
        mgr = SessionManager(str(tmp_path), auto_save=True)
        session = Session()
        session.add_user_message("Test")
        mgr.save_session(session)
        loaded = mgr.load_session(session.id)
        assert loaded is not None
