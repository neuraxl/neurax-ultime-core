import json
from typing import Any

def changed_fields(before: dict[str, Any] | None, after: dict[str, Any] | None) -> list[str]:
    if before is None:
        return list((after or {}).keys())
    if after is None:
        return list(before.keys())
    keys=set(before) | set(after)
    return sorted(k for k in keys if before.get(k) != after.get(k))

def diff_records(before: dict[str, dict[str, Any]], after: dict[str, dict[str, Any]]):
    events=[]
    for entity_id in sorted(set(before) | set(after)):
        b=before.get(entity_id)
        a=after.get(entity_id)
        if b is None:
            events.append({"entity_id":entity_id,"change_type":"added","changed_fields":changed_fields(None,a),"before":None,"after":a})
        elif a is None:
            events.append({"entity_id":entity_id,"change_type":"removed","changed_fields":changed_fields(b,None),"before":b,"after":None})
        else:
            fields=changed_fields(b,a)
            if fields:
                events.append({"entity_id":entity_id,"change_type":"updated","changed_fields":fields,"before":b,"after":a})
    return events
