import os
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex, QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QSplitter, QTableView, QTextEdit, QMessageBox, QCheckBox, QSpinBox, QMenu
)

from modules.connections.worker import ConnectionsWorker

COLS = ["Proto", "State", "Local", "Remote", "PID", "Process"]

class ConnModel(QAbstractTableModel):
    def __init__(self):
        super().__init__()
        self.rows = []

    def rowCount(self, parent=QModelIndex()):
        return len(self.rows)

    def columnCount(self, parent=QModelIndex()):
        return len(COLS)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            return COLS[section]
        return str(section + 1)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        r = self.rows[index.row()]
        c = index.column()
        if role == Qt.DisplayRole:
            key = COLS[c]
            return r.get(key, "")
        return None

    def set_rows(self, rows):
        self.beginResetModel()
        self.rows = rows
        self.endResetModel()

    def get(self, i):
        if 0 <= i < len(self.rows):
            return self.rows[i]
        return None


class ConnectionsPage(QFrame):
    def __init__(self):
        super().__init__()
        self.setObjectName("page")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(18, 18, 18, 18)
        outer.setSpacing(12)

        title = QLabel("Conexiones")
        title.setObjectName("pagetitle")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        outer.addWidget(title)

        sub = QLabel("Monitoreo TCP/UDP en vivo con proceso, ruta y usuario. Sin congelar la UI.")
        sub.setObjectName("pagesub")
        sub.setWordWrap(True)
        outer.addWidget(sub)

        # Controls panel
        controls = QFrame()
        controls.setObjectName("panel")
        c = QHBoxLayout(controls)
        c.setContentsMargins(12, 12, 12, 12)
        c.setSpacing(10)

        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("Filtrar (pid / proceso / ip:puerto / ruta / estado...)")

        self.chk_udp = QCheckBox("UDP")
        self.chk_udp.setChecked(True)

        self.chk_hide_listen = QCheckBox("Ocultar LISTEN")
        self.chk_hide_listen.setChecked(False)

        self.chk_hide_local = QCheckBox("Ocultar remoto localhost")
        self.chk_hide_local.setChecked(True)

        self.spn_ms = QSpinBox()
        self.spn_ms.setRange(300, 60000)
        self.spn_ms.setValue(1500)

        self.chk_auto = QCheckBox("Auto")
        self.chk_auto.setChecked(True)

        self.btn_refresh = QPushButton("Refrescar")
        self.btn_refresh.clicked.connect(self.refresh)

        c.addWidget(self.txt_search, 2)
        c.addWidget(self.chk_udp)
        c.addWidget(self.chk_hide_listen)
        c.addWidget(self.chk_hide_local)
        c.addWidget(QLabel("ms:")); c.addWidget(self.spn_ms)
        c.addWidget(self.chk_auto)
        c.addWidget(self.btn_refresh)

        outer.addWidget(controls)

        # Split: table + details
        split = QSplitter(Qt.Horizontal)

        left = QFrame()
        left.setObjectName("panel")
        l = QVBoxLayout(left)
        l.setContentsMargins(12, 12, 12, 12)
        l.setSpacing(10)

        self.model = ConnModel()
        self.table = QTableView()
        self.table.setModel(self.model)
        self.table.setSelectionBehavior(QTableView.SelectRows)
        self.table.setSelectionMode(QTableView.SingleSelection)
        self.table.setSortingEnabled(True)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.open_menu)

        self.table.setColumnWidth(0, 70)
        self.table.setColumnWidth(1, 120)
        self.table.setColumnWidth(2, 240)
        self.table.setColumnWidth(3, 260)
        self.table.setColumnWidth(4, 80)
        self.table.setColumnWidth(5, 220)

        self.table.clicked.connect(self.on_select)

        l.addWidget(self.table, 1)
        split.addWidget(left)

        right = QFrame()
        right.setObjectName("panel")
        r = QVBoxLayout(right)
        r.setContentsMargins(12, 12, 12, 12)
        r.setSpacing(10)

        head = QLabel("Detalle")
        head.setFont(QFont("Segoe UI", 12, QFont.Bold))
        head.setStyleSheet("color:#e9edf5;")
        r.addWidget(head)

        self.txt_detail = QTextEdit()
        self.txt_detail.setReadOnly(True)
        r.addWidget(self.txt_detail, 1)

        split.addWidget(right)
        split.setStretchFactor(0, 3)
        split.setStretchFactor(1, 2)

        outer.addWidget(split, 1)

        self.worker = None

        # Auto refresh timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(self.spn_ms.value())

        self.spn_ms.valueChanged.connect(lambda v: self.timer.setInterval(int(v)))
        self.txt_search.textChanged.connect(lambda _=None: self._maybe_quick_refresh())
        self.chk_udp.stateChanged.connect(lambda _=None: self._maybe_quick_refresh())
        self.chk_hide_listen.stateChanged.connect(lambda _=None: self._maybe_quick_refresh())
        self.chk_hide_local.stateChanged.connect(lambda _=None: self._maybe_quick_refresh())
        self.chk_auto.stateChanged.connect(lambda _=None: self._tick())

        self.refresh()

    def _tick(self):
        if self.chk_auto.isChecked():
            self.refresh()

    def _maybe_quick_refresh(self):
        # Don’t spam if a refresh is running, just trigger next tick quickly
        if self.worker and self.worker.isRunning():
            return
        self.refresh()

    def refresh(self):
        if self.worker and self.worker.isRunning():
            return

        self.btn_refresh.setEnabled(False)
        self.worker = ConnectionsWorker(
            include_udp=self.chk_udp.isChecked(),
            query_text=self.txt_search.text(),
            hide_listen=self.chk_hide_listen.isChecked(),
            hide_localhost_remote=self.chk_hide_local.isChecked()
        )
        self.worker.result.connect(self.on_result)
        self.worker.error.connect(self.on_error)
        self.worker.finished.connect(lambda: self.btn_refresh.setEnabled(True))
        self.worker.start()

    def on_result(self, rows):
        self.model.set_rows(rows)
        if rows:
            self.table.selectRow(0)
            self.show_row(rows[0])
        else:
            self.txt_detail.setPlainText("No hay conexiones con esos filtros.")

    def on_error(self, err: str):
        self.model.set_rows([])
        self.txt_detail.setPlainText(f"Error leyendo conexiones:\n\n{err}\n\nTip: ejecutar como Administrador muestra más procesos/conexiones.")
        QMessageBox.warning(self, "Conexiones", err)

    def on_select(self, idx):
        r = self.model.get(idx.row())
        if r:
            self.show_row(r)

    def show_row(self, r):
        # Pull full row from internal dict if exists
        # We stored more keys (User, Path) in worker
        proto = r.get("Proto","")
        st = r.get("State","")
        loc = r.get("Local","")
        rem = r.get("Remote","")
        pid = r.get("PID","")
        proc = r.get("Process","")

        # Best effort: find the full original row by matching key tuple
        # (The model has full dict already)
        user = r.get("User","") if "User" in r else ""
        path = r.get("Path","") if "Path" in r else ""

        txt = (
            f"Proto: {proto}\nState: {st}\n\n"
            f"Local:  {loc}\nRemote: {rem}\n\n"
            f"PID: {pid}\nProcess: {proc}\nUser: {user}\nPath: {path}\n"
        )
        self.txt_detail.setPlainText(txt)

    def selected_row(self):
        sel = self.table.selectionModel().selectedRows()
        if not sel:
            return None
        return self.model.get(sel[0].row())

    def open_menu(self, pos):
        r = self.selected_row()
        menu = QMenu(self)

        act_copy_remote = menu.addAction("Copiar remoto")
        act_copy_path = menu.addAction("Copiar ruta del proceso")
        act_open_folder = menu.addAction("Abrir carpeta del proceso")

        def do_copy_remote():
            if not r: return
            QApplication = __import__("PySide6.QtWidgets", fromlist=["QApplication"]).QApplication
            QApplication.clipboard().setText(r.get("Remote",""))

        def do_copy_path():
            if not r: return
            QApplication = __import__("PySide6.QtWidgets", fromlist=["QApplication"]).QApplication
            QApplication.clipboard().setText(r.get("Path",""))

        def do_open_folder():
            if not r: return
            p = r.get("Path","")
            if p and os.path.exists(p):
                os.startfile(os.path.dirname(p))

        act_copy_remote.triggered.connect(do_copy_remote)
        act_copy_path.triggered.connect(do_copy_path)
        act_open_folder.triggered.connect(do_open_folder)

        menu.exec(self.table.viewport().mapToGlobal(pos))
