import psutil
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QSizePolicy

def badge(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setFont(QFont("Segoe UI", 9))
    lbl.setObjectName("badge")
    lbl.setAlignment(Qt.AlignCenter)
    lbl.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    return lbl

class TopBar(QFrame):
    def __init__(self, app_name: str):
        super().__init__()
        self.setObjectName("topbar")

        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 10, 14, 10)
        lay.setSpacing(10)

        self.title = QLabel(app_name)
        self.title.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.title.setObjectName("apptitle")

        lay.addWidget(self.title)
        lay.addStretch(1)

        self.cpu = badge("CPU: —")
        self.ram = badge("RAM: —")
        self.integrity = badge("INTEGRITY: —")

        lay.addWidget(self.cpu)
        lay.addWidget(self.ram)
        lay.addWidget(self.integrity)

        try:
            psutil.cpu_percent(interval=None)
        except Exception:
            pass

        self.timer = QTimer(self)
        self.timer.setInterval(700)
        self.timer.timeout.connect(self.update_stats)
        self.timer.start()
        self.update_stats()

    def update_stats(self):
        cpu = psutil.cpu_percent(interval=None)
        ram = psutil.virtual_memory().percent

        self.cpu.setText(f"CPU: {cpu:.0f}%")
        self.ram.setText(f"RAM: {ram:.0f}%")

        if cpu >= 97:
            self.integrity.setText("INTEGRITY: HIGH CPU")
            self.integrity.setProperty("sev", "warn")
        elif ram >= 95:
            self.integrity.setText("INTEGRITY: LOW RAM")
            self.integrity.setProperty("sev", "warn")
        else:
            self.integrity.setText("INTEGRITY: OK")
            self.integrity.setProperty("sev", "ok")

        self.integrity.style().unpolish(self.integrity)
        self.integrity.style().polish(self.integrity)
