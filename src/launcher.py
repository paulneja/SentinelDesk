import sys
import os
import ctypes

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout,
    QLabel, QPushButton
)
from PySide6.QtGui import QFont

from app import start_application

APP_NAME = "SentinelDesk"


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False


def relaunch_as_admin():
    # En frozen (PyInstaller) usar sys.executable; en dev usar el .py
    if getattr(sys, "frozen", False):
        exe_path = sys.executable
        args = "--full"
    else:
        exe_path = sys.executable
        # relanza python.exe con el script + args
        script_path = os.path.abspath(sys.argv[0])
        args = f'"{script_path}" --full'

    ctypes.windll.shell32.ShellExecuteW(
        None,
        "runas",
        exe_path,
        args,
        None,
        1
    )
    sys.exit(0)


class Launcher(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle(APP_NAME + " — Inicio")
        self.setMinimumWidth(460)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        title = QLabel("SentinelDesk 1.0 Stable")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))

        desc = QLabel(
            "Seleccione el modo de ejecución:\n\n"
            "Modo PARCIAL\n"
            "• Funcionalidad estándar\n"
            "• No requiere privilegios elevados\n\n"
            "Modo COMPLETO\n"
            "• Requiere privilegios de Administrador\n"
            "• Requiere Npcap correctamente instalado\n"
            "• Habilita capacidades avanzadas\n"
        )
        desc.setWordWrap(True)

        self.btn_partial = QPushButton("Ejecutar modo PARCIAL")
        self.btn_full = QPushButton("Ejecutar modo COMPLETO (Administrador)")

        self.btn_partial.clicked.connect(self.run_partial)
        self.btn_full.clicked.connect(self.run_full)

        layout.addWidget(title)
        layout.addWidget(desc)
        layout.addWidget(self.btn_partial)
        layout.addWidget(self.btn_full)

        # IMPORTANTE: mantener referencia viva
        self.main_window = None

    def run_partial(self):
        w = start_application()
        if w is None:
            sys.exit(0)

        self.main_window = w
        self.close()

    def run_full(self):
        if is_admin():
            w = start_application()
            if w is None:
                sys.exit(0)

            self.main_window = w
            self.close()
        else:
            relaunch_as_admin()


def main():
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))

    # Si fue relanzado con --full, arrancar directo
    if "--full" in sys.argv:
        main_window = start_application()
        if main_window is None:
            sys.exit(0)
        sys.exit(app.exec())

    launcher = Launcher()
    launcher.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
