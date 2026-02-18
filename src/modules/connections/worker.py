from PySide6.QtCore import QThread, Signal
from modules.connections.collector import collect_connections

class ConnectionsWorker(QThread):
    result = Signal(list)     # list[dict]
    error = Signal(str)

    def __init__(self, include_udp: bool, query_text: str, hide_listen: bool, hide_localhost_remote: bool):
        super().__init__()
        self.include_udp = include_udp
        self.query_text = (query_text or "").strip().lower()
        self.hide_listen = hide_listen
        self.hide_localhost_remote = hide_localhost_remote

    def run(self):
        try:
            rows = collect_connections(include_udp=self.include_udp)

            # filters (cheap)
            out = []
            for r in rows:
                if self.hide_listen and r["State"] == "LISTEN":
                    continue
                if self.hide_localhost_remote:
                    rem = r["Remote"]
                    if rem.startswith("127.0.0.1:") or rem.startswith("::1:") or rem.startswith("[::1]:"):
                        continue

                if self.query_text:
                    blob = " | ".join([
                        r["Proto"], r["State"], r["Local"], r["Remote"],
                        r["PID"], r["Process"], r["User"], r["Path"]
                    ]).lower()
                    if self.query_text not in blob:
                        continue

                out.append(r)

            self.result.emit(out)
        except Exception as e:
            self.error.emit(str(e))
