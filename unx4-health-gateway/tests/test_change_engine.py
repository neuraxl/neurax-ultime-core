from app.change_engine import diff_records

def test_added_updated_removed():
    before={"1":{"name":"A","region":"01"},"2":{"name":"B"}}
    after={"1":{"name":"A2","region":"01"},"3":{"name":"C"}}
    events=diff_records(before,after)
    assert [(e["entity_id"],e["change_type"]) for e in events] == [
        ("1","updated"),("2","removed"),("3","added")
    ]
    assert events[0]["changed_fields"] == ["name"]
