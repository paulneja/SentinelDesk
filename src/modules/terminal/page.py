from PySide6.QtCore import Qt, QProcess, QEvent
from PySide6.QtGui import QFont, QTextCursor
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTextEdit, QMessageBox
)

APP_PROMPT = "PS>"


class TerminalPage(QFrame):
    """
    Terminal simple:
    escribe comando -> ejecuta en PowerShell -> muestra output.
    No es shell persistente, cada comando es independiente.
    """

    def __init__(self):
        super().__init__()
        self.setObjectName("page")

        self.proc = None
        self.history = []
        self.hist_idx = -1

        outer = QVBoxLayout(self)
        outer.setContentsMargins(18, 18, 18, 18)
        outer.setSpacing(12)

        # Título
        title = QLabel("Terminal")
        title.setObjectName("pagetitle")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        outer.addWidget(title)

        sub = QLabel("PowerShell — ejecuta comandos como el usuario actual.")
        sub.setObjectName("pagesub")
        sub.setWordWrap(True)
        outer.addWidget(sub)

        # Panel superior
        top = QFrame()
        top.setObjectName("panel")
        t = QHBoxLayout(top)
        t.setContentsMargins(12, 12, 12, 12)
        t.setSpacing(10)

        self.ed_cmd = QLineEdit()
        self.ed_cmd.setPlaceholderText("Escribí un comando y presioná Enter…")
        self.ed_cmd.returnPressed.connect(self.run_command)
        self.ed_cmd.installEventFilter(self)

        self.btn_run = QPushButton("Ejecutar")
        self.btn_run.clicked.connect(self.run_command)

        self.btn_stop = QPushButton("Detener")
        self.btn_stop.clicked.connect(self.stop_command)
        self.btn_stop.setEnabled(False)

        self.btn_clear = QPushButton("Limpiar")
        self.btn_clear.clicked.connect(lambda: self.out.clear())

        self.lbl_status = QLabel("Listo.")
        self.lbl_status.setStyleSheet("color:#aab3c5;")

        t.addWidget(QLabel(APP_PROMPT))
        t.addWidget(self.ed_cmd, 1)
        t.addWidget(self.btn_run)
        t.addWidget(self.btn_stop)
        t.addWidget(self.btn_clear)

        outer.addWidget(top)
        outer.addWidget(self.lbl_status)

        # Salida
        self.out = QTextEdit()
        self.out.setReadOnly(True)
        self.out.setObjectName("panel")
        self.out.setFont(QFont("Cascadia Mono", 10))
        self.out.setPlaceholderText("Salida de PowerShell…")
        outer.addWidget(self.out, 1)

        self._append_line("SentinelDesk Terminal listo.\n")

    # ========================
    # Historial ↑ ↓
    # ========================
    def eventFilter(self, obj, event):
        if obj is self.ed_cmd and event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Up:
                self._history_up()
                return True
            if event.key() == Qt.Key_Down:
                self._history_down()
                return True
        return super().eventFilter(obj, event)

    def _history_up(self):
        if not self.history:
            return
        if self.hist_idx == -1:
            self.hist_idx = len(self.history) - 1
        else:
            self.hist_idx = max(0, self.hist_idx - 1)
        self.ed_cmd.setText(self.history[self.hist_idx])

    def _history_down(self):
        if not self.history:
            return
        if self.hist_idx == -1:
            return
        self.hist_idx += 1
        if self.hist_idx >= len(self.history):
            self.hist_idx = -1
            self.ed_cmd.clear()
        else:
            self.ed_cmd.setText(self.history[self.hist_idx])

    # ========================
    # Ejecutar comando
    # ========================
    def run_command(self):
        cmd = self.ed_cmd.text().strip()
        if not cmd:
            return

        if self.proc and self.proc.state() != QProcess.NotRunning:
            QMessageBox.warning(
                self,
                "Terminal",
                "Ya hay un comando ejecutándose."
            )
            return

        self.history.append(cmd)
        if len(self.history) > 200:
            self.history = self.history[-200:]
        self.hist_idx = -1

        self._append_line(f"\n{APP_PROMPT} {cmd}\n")

        self.proc = QProcess(self)
        self.proc.setProcessChannelMode(QProcess.SeparateChannels)

        program = "powershell.exe"
        args = ["-NoProfile", "-Command", cmd]

        self.proc.readyReadStandardOutput.connect(self._on_stdout)
        self.proc.readyReadStandardError.connect(self._on_stderr)
        self.proc.finished.connect(self._on_finished)
        self.proc.errorOccurred.connect(self._on_error)

        self.btn_run.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.lbl_status.setText("Ejecutando…")

        self.proc.start(program, args)

    def stop_command(self):
        if not self.proc:
            return
        if self.proc.state() == QProcess.NotRunning:
            return
        self.proc.kill()
        self.lbl_status.setText("Detenido.")
        self._append_line("\n[Proceso detenido]\n")

    # ========================
    # Callbacks proceso
    # ========================
    def _on_stdout(self):
        data = self.proc.readAllStandardOutput().data().decode("utf-8", errors="replace")
        if data:
            self._append_text(data)

    def _on_stderr(self):
        data = self.proc.readAllStandardError().data().decode("utf-8", errors="replace")
        if data:
            self._append_text(data)

    def _on_finished(self, code, status):
        self.btn_run.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.lbl_status.setText(f"Listo. (exit={code})")
        self._append_line(f"\n[exit={code}]\n")

    def _on_error(self, _err):
        self.btn_run.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.lbl_status.setText("Error.")
        self._append_line("\n[Error al ejecutar PowerShell]\n")

    # ========================
    # Helpers output
    # ========================
    def _append_text(self, s: str):
        self.out.moveCursor(QTextCursor.End)
        self.out.insertPlainText(s)
        self.out.moveCursor(QTextCursor.End)

    def _append_line(self, s: str):
        self._append_text(s)
