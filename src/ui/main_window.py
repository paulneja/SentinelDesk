from pathlib import Path

from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget, QFrame, QLabel
)
from modules.files.page import FilesPage
from ui.topbar import TopBar
from ui.rightnav import RightNav
from modules.terminal.page import TerminalPage

from modules.logs.page import LogsPage
from modules.connections.page import ConnectionsPage
from modules.ports.page import PortsPage

APP_NAME = "SentinelDesk"


class PlaceholderPage(QWidget):
    def __init__(self, title: str, subtitle: str):
        super().__init__()

        from PySide6.QtWidgets import QScrollArea
        from PySide6.QtCore import Qt

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        container = QFrame()
        container.setObjectName("page")

        inner_layout = QVBoxLayout(container)
        inner_layout.setContentsMargins(18, 18, 18, 18)
        inner_layout.setSpacing(12)

        t = QLabel(title)
        t.setObjectName("pagetitle")
        t.setFont(QFont("Segoe UI", 18, QFont.Bold))

        s = QLabel(subtitle)
        s.setObjectName("pagesub")
        s.setWordWrap(True)
        s.setTextInteractionFlags(Qt.TextSelectableByMouse)

        inner_layout.addWidget(t)
        inner_layout.addWidget(s)
        inner_layout.addStretch(1)

        scroll.setWidget(container)
        main_layout.addWidget(scroll)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle(APP_NAME)
        self.resize(1350, 820)

        central = QWidget()
        root = QVBoxLayout(central)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(12)

        # Top bar
        self.top = TopBar(APP_NAME)
        root.addWidget(self.top)

        # Body
        body = QHBoxLayout()
        body.setSpacing(12)
        root.addLayout(body, 1)

        self.stack = QStackedWidget()

        self.nav = RightNav()
        self.nav.setFixedWidth(240)

        # Pages (order MUST match rightnav)
        self.page_dashboard = PlaceholderPage(
    "Dashboard",
    """SentinelDesk — Lastest Version 1.0 Stable

Bienvenido a SentinelDesk.

SentinelDesk es una herramienta de inspección y análisis local diseñada para ofrecer visibilidad técnica real sobre el estado del sistema, la actividad de red y el comportamiento de archivos. No automatiza decisiones. No suaviza advertencias. Ofrece información estructurada y control total.

────────────────────────────────────────────

MÓDULOS INCLUIDOS

Logs
• Parseo estructurado
• Clasificación por severidad
• Reglas internas de categorización

Conexiones
• Listado TCP/UDP en tiempo real
• Identificación de proceso, PID y usuario

Puertos
• Motor Nativo optimizado (localhost)
• Motor Nmap profesional (Modo Inseguro)
• Identificación por fingerprint
• Separación estricta entre modo seguro e inseguro

Archivos
• Análisis técnico en streaming
• SHA256 / MD5
• Entropía
• Strings preview controlado
• Límite 500MB para estabilidad

Terminal
• Ejecución directa PowerShell
• Historial de comandos
• Captura en vivo stdout/stderr

────────────────────────────────────────────

Correcciones clave en 1.0:
• Eliminado crash por manejo incorrecto de eventos
• Eliminado escaneo involuntario en motor Nmap
• Optimización de threads y estabilidad UI
• Corrección de imports en motor Nmap
• Control persistente del Modo Inseguro
• Eliminación de bloqueos por lectura masiva

SentinelDesk 1.0 Stable está activo.
"""
)

        self.page_logs = LogsPage()
        self.page_connections = ConnectionsPage()
        self.page_ports = PortsPage()
        self.page_files = FilesPage()
        self.page_terminal = TerminalPage()

        self.stack.addWidget(self.page_dashboard)    # 0
        self.stack.addWidget(self.page_logs)         # 1
        self.stack.addWidget(self.page_connections)  # 2
        self.stack.addWidget(self.page_ports)        # 3
        self.stack.addWidget(self.page_files)        # 4
        self.stack.addWidget(self.page_terminal)     # 5

        body.addWidget(self.stack, 1)
        body.addWidget(self.nav)

        self.setCentralWidget(central)

        # Load theme
        qss = Path(__file__).resolve().parent / "theme.qss"
        if qss.exists():
            self.setStyleSheet(qss.read_text(encoding="utf-8"))

        # Navigation wiring
        self.nav.list.currentRowChanged.connect(self.stack.setCurrentIndex)
