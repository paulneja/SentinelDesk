from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QListWidget, QListWidgetItem

class RightNav(QFrame):
    def __init__(self):
        super().__init__()
        self.setObjectName("rightnav")

        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(10)

        head = QLabel("MODOS")
        head.setFont(QFont("Segoe UI", 9, QFont.Bold))
        head.setObjectName("navhead")
        lay.addWidget(head)

        self.list = QListWidget()
        self.list.setObjectName("navlist")
        self.list.setSpacing(6)

        items = [
            ("Dashboard", "⌂"),
            ("Logs", "☰"),
            ("Conexiones", "⎈"),
            ("Puertos", "⇄"),
            ("Archivos", "▦"),
            ("Terminal", "▸"),
        ]
        for name, icon in items:
            it = QListWidgetItem(f"  {icon}  {name}")
            self.list.addItem(it)

        self.list.setCurrentRow(0)
        lay.addWidget(self.list, 1)

        foot = QLabel("Estado: activo")
        foot.setObjectName("navfoot")
        lay.addWidget(foot)

    def set_status(self, text: str):
        # optional, later
        pass
