import subprocess
from PySide6.QtCore import QThread, Signal
from modules.logs.parser import parse_wevtutil_text

class LogsWorker(QThread):
    result = Signal(list)         # list[LogEvent]
    error = Signal(str)

    def __init__(self, channel: str, count: int, level_filter: str, query_text: str):
        super().__init__()
        self.channel = channel
        self.count = count
        self.level_filter = (level_filter or "ALL").upper()
        self.query_text = (query_text or "").strip().lower()

    def run(self):
        try:
            # Read most recent N events, newest first
            cmd = ["wevtutil", "qe", self.channel, f"/c:{self.count}", "/rd:true", "/f:text"]
            p = subprocess.run(cmd, capture_output=True, text=True, timeout=12)

            if p.returncode != 0:
                err = (p.stderr or p.stdout or "").strip()
                if not err:
                    err = f"wevtutil error (code {p.returncode})"
                self.error.emit(err)
                return

            events = parse_wevtutil_text(self.channel, p.stdout or "")

            # Apply filters here (cheap)
            if self.level_filter != "ALL":
                events = [e for e in events if (e.level or "").upper().startswith(self.level_filter)]

            if self.query_text:
                q = self.query_text
                def hit(e):
                    blob = f"{e.time}\n{e.level}\n{e.source}\n{e.event_id}\n{e.message}\n{e.raw}".lower()
                    return q in blob
                events = [e for e in events if hit(e)]

            self.result.emit(events)
        except subprocess.TimeoutExpired:
            self.error.emit("Timeout leyendo eventos (wevtutil tardó demasiado).")
        except Exception as e:
            self.error.emit(str(e))
