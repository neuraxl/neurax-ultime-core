import json
from typing import Any

def changed_fields(before: dict[str, Any] | None, after: dict[str, Any] | None) -> list[str]:
    if before is None:
        return list((after or {}).keys())
    if after is None:
        return list(before.keys())
    keys=set(before) | set(after)
    return sorted(k for k in keys if before.get(k) != after.get(k))

def canonical_record(row: dict[str, Any]) -> dict[str, Any]:
    return json.loads(json.dumps(row, default=str, sort_keys=True))

def diff_records(before: dict[str, dict[str, Any]], after: dict[str, dict[str, Any]]):
    events=[]
    for entity_id in sorted(set(before) | set(after)):
        b=canonical_record(before[entity_id]) if entity_id in before else None
        a=canonical_record(after[entity_id]) if entity_id in after else None
        if b is None:
            events.append({"entity_id":entity_id,"change_type":"added","changed_fields":changed_fields(None,a),"before":None,"after":a})
        elif a is None:
            events.append({"entity_id":entity_id,"change_type":"removed","changed_fields":changed_fields(b,None),"before":b,"after":None})
        else:
            fields=changed_fields(b,a)
            if fields:
                events.append({"entity_id":entity_id,"change_type":"updated","changed_fields":fields,"before":b,"after":a})
    return events
