from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QComboBox, QSpinBox, QLineEdit, QPushButton,
    QSplitter, QTableView, QTextEdit, QMessageBox, QCheckBox
)

from modules.logs.worker import LogsWorker

COLS = ["Time", "Lvl", "Cat", "Score", "Source", "EventID"]

class LogsTableModel(QAbstractTableModel):
    def __init__(self):
        super().__init__()
        self.events = []

    def rowCount(self, parent=QModelIndex()):
        return len(self.events)

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
        e = self.events[index.row()]
        col = index.column()

        if role == Qt.DisplayRole:
            if col == 0: return e.time
            if col == 1: return e.level
            if col == 2: return e.category
            if col == 3: return str(e.score)
            if col == 4: return e.source
            if col == 5: return e.event_id
        return None

    def set_events(self, evs):
        self.beginResetModel()
        self.events = evs
        self.endResetModel()

    def get(self, row: int):
        if 0 <= row < len(self.events):
            return self.events[row]
        return None


class LogsPage(QFrame):
    def __init__(self):
        super().__init__()
        self.setObjectName("page")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(18, 18, 18, 18)
        outer.setSpacing(12)

        title = QLabel("Logs")
        title.setObjectName("pagetitle")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        outer.addWidget(title)

        sub = QLabel("Eventos de Windows categorizados (leve → crítico) con acciones sugeridas. Sin freezes.")
        sub.setObjectName("pagesub")
        sub.setWordWrap(True)
        outer.addWidget(sub)

        # Controls panel
        controls = QFrame()
        controls.setObjectName("panel")
        c = QHBoxLayout(controls)
        c.setContentsMargins(12, 12, 12, 12)
        c.setSpacing(10)

        self.cmb_channel = QComboBox()
        self.cmb_channel.addItems([
            "System",
            "Application",
            "Security",
            "Microsoft-Windows-Windows Defender/Operational",
            "Microsoft-Windows-PowerShell/Operational",
        ])

        self.cmb_level = QComboBox()
        self.cmb_level.addItems(["ALL", "Information", "Warning", "Error", "Critical"])

        self.spn_count = QSpinBox()
        self.spn_count.setRange(50, 5000)
        self.spn_count.setValue(300)

        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("Buscar texto (source, mensaje, event id...)")

        self.btn_refresh = QPushButton("Refrescar")
        self.btn_refresh.clicked.connect(self.refresh)

        self.chk_auto = QCheckBox("Auto")
        self.chk_auto.setChecked(False)

        c.addWidget(QLabel("Canal:")); c.addWidget(self.cmb_channel, 1)
        c.addWidget(QLabel("Nivel:")); c.addWidget(self.cmb_level)
        c.addWidget(QLabel("Cantidad:")); c.addWidget(self.spn_count)
        c.addWidget(self.txt_search, 2)
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

        self.model = LogsTableModel()
        self.table = QTableView()
        self.table.setModel(self.model)
        self.table.setSelectionBehavior(QTableView.SelectRows)
        self.table.setSelectionMode(QTableView.SingleSelection)
        self.table.setSortingEnabled(True)

        # Nice widths
        self.table.setColumnWidth(0, 160)
        self.table.setColumnWidth(1, 90)
        self.table.setColumnWidth(2, 90)
        self.table.setColumnWidth(3, 70)
        self.table.setColumnWidth(4, 200)
        self.table.setColumnWidth(5, 80)

        self.table.clicked.connect(self.on_select)

        l.addWidget(self.table, 1)
        split.addWidget(left)

        right = QFrame()
        right.setObjectName("panel")
        r = QVBoxLayout(right)
        r.setContentsMargins(12, 12, 12, 12)
        r.setSpacing(10)

        self.lbl_head = QLabel("Detalle")
        self.lbl_head.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.lbl_head.setStyleSheet("color:#e9edf5;")
        r.addWidget(self.lbl_head)

        self.txt_detail = QTextEdit()
        self.txt_detail.setReadOnly(True)
        r.addWidget(self.txt_detail, 1)

        split.addWidget(right)
        split.setStretchFactor(0, 3)
        split.setStretchFactor(1, 2)

        outer.addWidget(split, 1)

        self.worker = None
        self.refresh()

    def refresh(self):
        if self.worker and self.worker.isRunning():
            return

        self.btn_refresh.setEnabled(False)
        channel = self.cmb_channel.currentText()
        count = int(self.spn_count.value())
        level = self.cmb_level.currentText()
        query = self.txt_search.text()

        self.worker = LogsWorker(channel, count, level, query)
        self.worker.result.connect(self.on_result)
        self.worker.error.connect(self.on_error)
        self.worker.finished.connect(lambda: self.btn_refresh.setEnabled(True))
        self.worker.start()

    def on_result(self, events):
        self.model.set_events(events)
        if events:
            self.table.selectRow(0)
            self.show_event(events[0])
        else:
            self.txt_detail.setPlainText("No hay eventos con esos filtros.")

    def on_error(self, err: str):
        self.model.set_events([])
        self.txt_detail.setPlainText(f"Error leyendo eventos:\n\n{err}\n\nTip: 'Security' puede requerir ejecutar como Administrador.")
        QMessageBox.warning(self, "Logs", err)

    def on_select(self, idx):
        e = self.model.get(idx.row())
        if e:
            self.show_event(e)

    def show_event(self, e):
        # Compact + useful
        header = f"[{e.category}] score={e.score} | {e.level} | {e.source} | EventID={e.event_id}\nTime: {e.time}\nChannel: {e.channel}\n"
        action = f"\nSuggested action:\n- {e.action_hint}\n" if e.action_hint else ""
        body = f"\nMessage:\n{e.message}\n\nRaw:\n{e.raw}"
        self.txt_detail.setPlainText(header + action + body)
