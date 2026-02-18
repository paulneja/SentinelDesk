from PySide6.QtCore import QThread, Signal
from modules.ports.engine_native import native_scan_localhost
from modules.ports.engine_nmap import run_nmap



class PortsWorker(QThread):
    progress = Signal(str)
    result = Signal(list)         # list[dict]
    nmap_output = Signal(str)
    error = Signal(str)

    def __init__(self, engine: str, ports: list[int],
                 timeout_connect: float, timeout_probe: float, workers: int,
                 nmap_path: str, nmap_args: str):
        super().__init__()
        self.engine = engine      # "NATIVE" or "NMAP"
        self.ports = ports
        self.timeout_connect = timeout_connect
        self.timeout_probe = timeout_probe
        self.workers = workers
        self.nmap_path = nmap_path
        self.nmap_args = nmap_args

    def run(self):
        try:
            if self.engine == "NATIVE":
                self.progress.emit("Escaneando localhost (nativo)…")
                rows = native_scan_localhost(
                    ports=self.ports,
                    timeout_connect=self.timeout_connect,
                    timeout_probe=self.timeout_probe,
                    workers=self.workers,
                    progress_cb=lambda s: self.progress.emit(s)
                )
                self.result.emit(rows)
                self.progress.emit("Listo.")
                return

            # NMAP
            self.progress.emit("Ejecutando nmap (pro)…")
            rc, out, err = run_nmap(self.nmap_path, self.nmap_args)


            if out:
                self.nmap_output.emit(out)
            if err:
                self.nmap_output.emit("\n[stderr]\n" + err)

            if rc != 0:
                self.error.emit(f"nmap returncode={rc}\n{err.strip() or 'error'}")
                self.progress.emit("Error.")
                return

            self.progress.emit("Listo.")
        except Exception as e:
            self.error.emit(str(e))
