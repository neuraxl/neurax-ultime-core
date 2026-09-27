from app.data_intelligence import persist_changes


class FakeConnection:
    def __init__(self):
        self.calls = []

    def execute(self, sql, params):
        self.calls.append((sql, params))


def test_persist_changes_records_added_updated_removed():
    conn = FakeConnection()
    before = {
        "1": {"id": "1", "name": "A", "region": "R1"},
        "2": {"id": "2", "name": "B", "region": "R1"},
    }
    after = {
        "1": {"id": "1", "name": "A2", "region": "R1"},
        "3": {"id": "3", "name": "C", "region": "R2"},
    }

    changes = persist_changes(conn, "facilities", before, after, 42)

    assert [c["change_type"] for c in changes] == ["updated", "removed", "added"]
    assert len(conn.calls) == 3
    assert all(call[1][-1] == 42 for call in conn.calls)
