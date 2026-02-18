import os
from PySide6.QtCore import QThread, Signal
from modules.files import utils


class FilesWorker(QThread):
    progress = Signal(str)
    result = Signal(dict)
    error = Signal(str)

    def __init__(self, path: str):
        super().__init__()
        self.path = path

    def run(self):
        try:
            p = self.path
            if not p or not os.path.isfile(p):
                self.error.emit("Archivo inválido.")
                return

            size = os.path.getsize(p)
            if size > utils.MAX_BYTES:
                self.error.emit(f"Archivo demasiado grande ({utils.fmt_bytes(size)}). Máximo: 0.5 GB.")
                return

            # Básico inmediato
            self.progress.emit("Leyendo metadatos…")
            meta = {
                "Nombre": os.path.basename(p),
                "Ruta": p,
                "Tamaño": f"{utils.fmt_bytes(size)} ({size} bytes)",
                "MIME": utils.detect_mime(p),
            }

            t = utils.file_times(p)
            meta["Creación (epoch)"] = str(int(t["Creación"]))
            meta["Modificación (epoch)"] = str(int(t["Modificación"]))
            meta["Acceso (epoch)"] = str(int(t["Acceso"]))

            # Hashes (streaming + progreso)
            def cb(done, total):
                pct = int((done / total) * 100) if total else 0
                self.progress.emit(f"Hashing… {pct}%")

            hashes = utils.compute_hashes_stream(p, progress_cb=cb)
            meta.update(hashes)

            # Entropía (streaming)
            self.progress.emit("Calculando entropía…")
            ent = utils.entropy_stream(p)
            meta["Entropía (0-8)"] = f"{ent:.3f}"

            # Strings preview
            self.progress.emit("Extrayendo strings (preview)…")
            strings = utils.extract_strings_preview(p)

            # Hex preview
            self.progress.emit("Cargando hex preview…")
            hex_bytes = utils.read_hex_preview(p)

            # PE info básico
            pe = {}
            if utils.is_pe(p):
                self.progress.emit("Detectado PE. Leyendo cabecera…")
                pe = utils.pe_basic_info(p)

            self.result.emit({
                "meta": meta,
                "strings": strings,
                "hex": hex_bytes,
                "pe": pe
            })
            self.progress.emit("Listo.")

        except Exception as e:
            self.error.emit(str(e))
