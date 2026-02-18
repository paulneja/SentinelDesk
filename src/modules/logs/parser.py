import re
from dataclasses import dataclass
from modules.logs.rules import classify_event

@dataclass
class LogEvent:
    time: str
    level: str
    source: str
    event_id: str
    channel: str
    message: str
    raw: str
    score: int
    category: str
    action_hint: str

_kv = re.compile(r"^([^:]+):\s*(.*)$")

def parse_wevtutil_text(channel: str, text: str):
    """
    wevtutil /f:text returns blocks separated by blank lines.
    We'll parse common fields and keep full raw block.
    """
    events = []
    blocks = [b.strip() for b in re.split(r"\n\s*\n", text) if b.strip()]
    for blk in blocks:
        time = level = source = event_id = ""
        msg_lines = []
        # Parse line by line
        for line in blk.splitlines():
            m = _kv.match(line)
            if m:
                k = m.group(1).strip().lower()
                v = m.group(2).strip()
                if k in ("date", "date and time"):
                    time = v
                elif k in ("level",):
                    level = v
                elif k in ("source", "provider name"):
                    source = v
                elif k in ("event id",):
                    event_id = v
                else:
                    # keep other kvs as part of message? no
                    pass
            else:
                msg_lines.append(line)

        message = "\n".join(msg_lines).strip()
        score, category, action = classify_event(channel, level, event_id, message)
        events.append(LogEvent(
            time=time or "",
            level=level or "",
            source=source or "",
            event_id=event_id or "",
            channel=channel,
            message=message,
            raw=blk,
            score=score,
            category=category,
            action_hint=action
        ))
    return events
