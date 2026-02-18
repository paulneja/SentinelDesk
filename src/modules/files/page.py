import os
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QFileDialog, QSplitter, QTableWidget, QTableWidgetItem, QTextEdit,
    QMessageBox
)

from modules.files.worker import FilesWorker
from modules.files.utils import MAX_BYTES, fmt_bytes


def hex_dump(data: bytes, base: int = 0) -> str:
    # Hex dump simple y rápido (preview)
    lines = []
    for i in range(0, len(data), 16):
        chunk = data[i:i+16]
        hx = " ".join(f"{b:02X}" for b in chunk)
        asc = "".join(chr(b) if 32 <= b <= 126 else "." for b in chunk)
        lines.append(f"{base+i:08X}  {hx:<47}  {asc}")
    return "\n".join(lines)


class FilesPage(QFrame):
    def __init__(self):
        super().__init__()
        self.setObjectName("page")
        self.worker = None
        self.current_path = ""

        outer = QVBoxLayout(self)
        outer.setContentsMargins(18, 18, 18, 18)
        outer.setSpacing(12)

        title = QLabel("Archivos")
        title.setObjectName("pagetitle")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        outer.addWidget(title)

        sub = QLabel("Análisis técnico de archivo (optimizado). Máximo: 0.5 GB.")
        sub.setObjectName("pagesub")
        sub.setWordWrap(True)
        outer.addWidget(sub)

        top = QFrame()
        top.setObjectName("panel")
        t = QHBoxLayout(top)
        t.setContentsMargins(12, 12, 12, 12)
        t.setSpacing(10)

        self.ed_path = QLineEdit()
        self.ed_path.setPlaceholderText("Seleccioná un archivo…")
        self.btn_pick = QPushButton("Elegir…")
        self.btn_pick.clicked.connect(self.pick_file)

        self.btn_analyze = QPushButton("Analizar")
        self.btn_analyze.clicked.connect(self.analyze)

        self.lbl_status = QLabel("Listo.")
        self.lbl_status.setStyleSheet("color:#aab3c5;")

        t.addWidget(QLabel("Archivo:"))
        t.addWidget(self.ed_path, 1)
        t.addWidget(self.btn_pick)
        t.addWidget(self.btn_analyze)

        outer.addWidget(top)
        outer.addWidget(self.lbl_status)

        split = QSplitter(Qt.Horizontal)

        left = QFrame()
        left.setObjectName("panel")
        l = QVBoxLayout(left)
        l.setContentsMargins(12, 12, 12, 12)
        l.setSpacing(10)

        head = QLabel("Metadata")
        head.setFont(QFont("Segoe UI", 12, QFont.Bold))
        head.setStyleSheet("color:#e9edf5;")
        l.addWidget(head)

        self.tbl = QTableWidget(0, 2)
        self.tbl.setHorizontalHeaderLabels(["Campo", "Valor"])
        self.tbl.horizontalHeader().setStretchLastSection(True)
        self.tbl.verticalHeader().setVisible(False)
        self.tbl.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tbl.setSelectionBehavior(QTableWidget.SelectRows)
        l.addWidget(self.tbl, 1)

        split.addWidget(left)

        right = QFrame()
        right.setObjectName("panel")
        r = QVBoxLayout(right)
        r.setContentsMargins(12, 12, 12, 12)
        r.setSpacing(10)

        head2 = QLabel("Detalle")
        head2.setFont(QFont("Segoe UI", 12, QFont.Bold))
        head2.setStyleSheet("color:#e9edf5;")
        r.addWidget(head2)

        self.txt_detail = QTextEdit()
        self.txt_detail.setReadOnly(True)
        self.txt_detail.setPlaceholderText("Detalle técnico, strings y hex preview.")
        r.addWidget(self.txt_detail, 1)

        split.addWidget(right)

        split.setStretchFactor(0, 2)
        split.setStretchFactor(1, 3)

        outer.addWidget(split, 1)

    def pick_file(self):
        f, _ = QFileDialog.getOpenFileName(self, "Seleccionar archivo", "", "Todos (*.*)")
        if f:
            self.ed_path.setText(f)

    def analyze(self):
        if self.worker and self.worker.isRunning():
            return

        path = self.ed_path.text().strip()
        if not path or not os.path.isfile(path):
            QMessageBox.warning(self, "Archivos", "Seleccioná un archivo válido.")
            return

        size = os.path.getsize(path)
        if size > MAX_BYTES:
            QMessageBox.warning(
                self,
                "Archivos",
                f"Archivo demasiado grande ({fmt_bytes(size)}).\nMáximo permitido: 0.5 GB."
            )
            return

        self.current_path = path
        self.tbl.setRowCount(0)
        self.txt_detail.clear()
        self.lbl_status.setText("Iniciando…")

        self.btn_analyze.setEnabled(False)
        self.worker = FilesWorker(path)
        self.worker.progress.connect(self.lbl_status.setText)
        self.worker.error.connect(self.on_error)
        self.worker.result.connect(self.on_result)
        self.worker.finished.connect(lambda: self.btn_analyze.setEnabled(True))
        self.worker.start()

    def on_error(self, msg: str):
        QMessageBox.warning(self, "Archivos", msg)
        self.lbl_status.setText("Error.")

    def on_result(self, payload: dict):
        meta = payload.get("meta", {})
        strings = payload.get("strings", [])
        hex_bytes = payload.get("hex", b"")
        pe = payload.get("pe", {})

        # Tabla clave/valor
        items = list(meta.items())
        # PE info al final (si existe)
        for k, v in pe.items():
            items.append((k, v))

        self.tbl.setRowCount(len(items))
        for i, (k, v) in enumerate(items):
            self.tbl.setItem(i, 0, QTableWidgetItem(str(k)))
            self.tbl.setItem(i, 1, QTableWidgetItem(str(v)))

        # Detalle: strings + hex preview
        out = []
        out.append("== STRINGS (preview) ==")
        if strings:
            out.extend(strings[:2000])
        else:
            out.append("(sin strings detectadas)")

        out.append("\n== HEX PREVIEW (64 KB) ==")
        out.append(hex_dump(hex_bytes))

        self.txt_detail.setPlainText("\n".join(out))
