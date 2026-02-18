from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox,
    QSpinBox, QDoubleSpinBox, QSplitter, QTableView, QTextEdit, QMessageBox,
    QFileDialog, QDialog, QDialogButtonBox
)

from modules.ports.utils import parse_ports, find_nmap_in_path
from modules.ports.worker import PortsWorker

# Persistente solo en sesión (se resetea al cerrar la app)
INSECURE_ACTIVE = False

COLS = ["Host", "Port", "State", "Service", "Confidence", "PID", "Process"]

class PortsModel(QAbstractTableModel):
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
        return COLS[section] if orientation == Qt.Horizontal else str(section + 1)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        r = self.rows[index.row()]
        key = COLS[index.column()]
        if role == Qt.DisplayRole:
            return str(r.get(key, ""))
        return None

    def set_rows(self, rows):
        self.beginResetModel()
        self.rows = rows
        self.endResetModel()

    def get(self, i):
        if 0 <= i < len(self.rows):
            return self.rows[i]
        return None


class InsecureDialog(QDialog):
    """
    3 CONFIRMAR.
    """
    def __init__(self, step: int):
        super().__init__()
        self.step = step
        self.setModal(True)
        self.setMinimumWidth(640)

        lay = QVBoxLayout(self)
        title = QLabel("MODO INSEGURO")
        title.setFont(QFont("Segoe UI", 13, QFont.Bold))
        title.setStyleSheet("color:#ff6b6b;")
        lay.addWidget(title)

        if step == 1:
            self.setWindowTitle("Advertencia 1/3")
            txt = (
                "Esto habilita acciones de escaneo activo.\n\n"
                "En el caso de uso, aunque sea una red local, podés:\n"
                "- Generar registros en sistemas de seguridad (IDS/Firewall)\n"
                "- Provocar bloqueos automáticos o restricciones por IP\n"
                "- Ser interpretado como comportamiento hostil y ocacionar consecuencias/acciones legales\n\n"
                "Si no tenés autorización explícita, no continúes."
            )
        elif step == 2:
            self.setWindowTitle("Advertencia 2/3")
            txt = (
                "Este modo NO es para aprender ni para jugar.\n\n"
                "Si ejecutás comandos 'porque sí', el programa asume que:\n"
                "- Entendés exactamente lo que estás haciendo\n"
                "- Aceptás consecuencias técnicas y LEGALES\n"
                "- No necesitás que te simplifiquen nada\n\n"
                "No hay presets. No hay ayudas y aceptas total responsabilidad."
            )
        else:
            self.setWindowTitle("Advertencia 3/3")
            txt = (
                "Última confirmación.\n\n"
                "Para habilitar MODO INSEGURO en esta sesión:\n"
                "Escribí exactamente: CONFIRMAR\n\n"
                "Se mantendrá ACTIVO hasta que cierres el programa."
            )

        msg = QLabel(txt)
        msg.setWordWrap(True)
        msg.setStyleSheet("color:#e9edf5;")
        lay.addWidget(msg)

        self.edit = None
        if step == 3:
            self.edit = QLineEdit()
            self.edit.setPlaceholderText("CONFIRMAR")
            lay.addWidget(self.edit)

        bb = QDialogButtonBox(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        lay.addWidget(bb)

    def confirmed(self) -> bool:
        if self.step != 3:
            return True
        return (self.edit.text().strip() if self.edit else "") == "CONFIRMAR"


class PortsPage(QFrame):
    def __init__(self):
        super().__init__()
        self.setObjectName("page")
        self.worker = None

        outer = QVBoxLayout(self)
        outer.setContentsMargins(18, 18, 18, 18)
        outer.setSpacing(12)

        # Banner Modo Inseguro
        self.banner = QLabel("")
        self.banner.setVisible(False)
        self.banner.setStyleSheet(
            "padding:10px; border-radius:10px;"
            "background:#2b1010; color:#ff6b6b; font-weight:700;"
        )
        outer.addWidget(self.banner)

        title = QLabel("Puertos")
        title.setObjectName("pagetitle")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        outer.addWidget(title)

        sub = QLabel("Escaneo TCP local (localhost) con motor nativo o Nmap (solo en Modo Inseguro).")
        sub.setObjectName("pagesub")
        sub.setWordWrap(True)
        outer.addWidget(sub)

        controls = QFrame()
        controls.setObjectName("panel")
        c = QHBoxLayout(controls)
        c.setContentsMargins(12, 12, 12, 12)
        c.setSpacing(10)

        # Target fijo por seguridad: localhost (igual a lo que venís mostrando con nmap)
        self.lbl_target = QLabel("Target: 127.0.0.1 (localhost)")
        self.lbl_target.setStyleSheet("color:#e9edf5;")

        # Puertos: presets + custom
        self.cmb_ports = QComboBox()
        self.cmb_ports.addItems(["1-1024", "TODOS TCP (1-65535)", "Custom…"])

        self.ed_ports = QLineEdit("1-1024")
        self.ed_ports.setPlaceholderText("Ej: 22,80,443 o 8000-8100")
        self.ed_ports.setVisible(False)

        # Engine: nmap no aparece hasta activar inseguro
        self.cmb_engine = QComboBox()
        self.cmb_engine.addItems(["NATIVE"])  # NMAP se agrega solo cuando se habilita inseguro

        # Config nativo (preciso y configurable)
        self.spn_workers = QSpinBox()
        self.spn_workers.setRange(10, 1200)
        self.spn_workers.setValue(250)

        self.spn_connect = QDoubleSpinBox()
        self.spn_connect.setRange(0.05, 6.0)
        self.spn_connect.setDecimals(2)
        self.spn_connect.setValue(0.50)
        self.spn_connect.setSingleStep(0.05)

        self.spn_probe = QDoubleSpinBox()
        self.spn_probe.setRange(0.05, 10.0)
        self.spn_probe.setDecimals(2)
        self.spn_probe.setValue(1.10)
        self.spn_probe.setSingleStep(0.05)

        # Botón modo inseguro
        self.btn_insecure = QPushButton("Activar Modo Inseguro")
        self.btn_insecure.clicked.connect(self.activate_insecure)

        self.btn_run = QPushButton("Escanear")
        self.btn_run.clicked.connect(self.run)

        c.addWidget(self.lbl_target, 2)
        c.addWidget(QLabel("Puertos:"))
        c.addWidget(self.cmb_ports)
        c.addWidget(self.ed_ports, 2)
        c.addWidget(QLabel("Engine:"))
        c.addWidget(self.cmb_engine)
        c.addWidget(QLabel("Workers:"))
        c.addWidget(self.spn_workers)
        c.addWidget(QLabel("Connect s:"))
        c.addWidget(self.spn_connect)
        c.addWidget(QLabel("Probe s:"))
        c.addWidget(self.spn_probe)
        c.addWidget(self.btn_insecure)
        c.addWidget(self.btn_run)

        outer.addWidget(controls)

        # Panel Nmap (solo visible si engine NMAP)
        nmap_panel = QFrame()
        nmap_panel.setObjectName("panel")
        n = QHBoxLayout(nmap_panel)
        n.setContentsMargins(12, 12, 12, 12)
        n.setSpacing(10)

        self.ed_nmap = QLineEdit()
        self.ed_nmap.setPlaceholderText("Ruta a nmap.exe (o vacío para buscar en PATH)")
        self.btn_pick = QPushButton("Elegir…")
        self.btn_pick.clicked.connect(self.pick_nmap)

        self.ed_args = QLineEdit("-sV -p 1-1024 -oN -")
        self.ed_args.setPlaceholderText("Argumentos (profesional). Ej: -sV -p 1-65535")

        self.lbl_pro = QLabel("NMAP — SOLO USO PROFESIONAL.")
        self.lbl_pro.setStyleSheet("color:#ffb3b3; font-weight:700;")

        n.addWidget(self.lbl_pro, 2)
        n.addWidget(QLabel("nmap.exe:"))
        n.addWidget(self.ed_nmap, 2)
        n.addWidget(self.btn_pick)
        n.addWidget(QLabel("args:"))
        n.addWidget(self.ed_args, 3)

        outer.addWidget(nmap_panel)
        self.nmap_panel = nmap_panel
        self.nmap_panel.setVisible(False)

        self.lbl_status = QLabel("Listo.")
        self.lbl_status.setStyleSheet("color:#aab3c5;")
        outer.addWidget(self.lbl_status)

        split = QSplitter(Qt.Horizontal)

        left = QFrame()
        left.setObjectName("panel")
        l = QVBoxLayout(left)
        l.setContentsMargins(12, 12, 12, 12)
        l.setSpacing(10)

        self.model = PortsModel()
        self.table = QTableView()
        self.table.setModel(self.model)
        self.table.setSelectionBehavior(QTableView.SelectRows)
        self.table.setSelectionMode(QTableView.SingleSelection)
        self.table.setSortingEnabled(True)
        self.table.clicked.connect(self.on_select)

        self.table.setColumnWidth(0, 140)
        self.table.setColumnWidth(1, 80)
        self.table.setColumnWidth(2, 90)
        self.table.setColumnWidth(3, 180)
        self.table.setColumnWidth(4, 120)
        self.table.setColumnWidth(5, 80)
        self.table.setColumnWidth(6, 260)

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

        self.detail = QTextEdit()
        self.detail.setReadOnly(True)
        r.addWidget(self.detail, 1)

        self.nmap_out = QTextEdit()
        self.nmap_out.setReadOnly(True)
        self.nmap_out.setPlaceholderText("Salida cruda de escaneo.")
        r.addWidget(self.nmap_out, 1)

        split.addWidget(right)
        split.setStretchFactor(0, 3)
        split.setStretchFactor(1, 2)

        outer.addWidget(split, 1)

        # hooks UI
        self.cmb_ports.currentIndexChanged.connect(self.sync_ports_ui)
        self.cmb_engine.currentIndexChanged.connect(self.sync_engine_ui)
        self.sync_ports_ui()
        self.sync_engine_ui()
        self.refresh_insecure_ui()

    def sync_ports_ui(self):
        mode = self.cmb_ports.currentText()
        is_custom = mode.startswith("Custom")
        self.ed_ports.setVisible(is_custom)

        if not is_custom:
            if mode.startswith("1-1024"):
                self.ed_ports.setText("1-1024")
            else:
                self.ed_ports.setText("1-65535")

    def sync_engine_ui(self):
        eng = self.cmb_engine.currentText()
        self.nmap_panel.setVisible(eng == "NMAP")
        # si es nmap, no tiene sentido workers/connect/probe (eso lo maneja nmap)
        is_nmap = (eng == "NMAP")
        self.spn_workers.setEnabled(not is_nmap)
        self.spn_connect.setEnabled(not is_nmap)
        self.spn_probe.setEnabled(not is_nmap)

    def refresh_insecure_ui(self):
        global INSECURE_ACTIVE

        if INSECURE_ACTIVE:
            self.banner.setText("MODO INSEGURO ACTIVO")
            self.banner.setVisible(True)
            self.btn_insecure.setEnabled(False)

            # habilitar NMAP en selector si todavía no existe
            if self.cmb_engine.findText("NMAP") == -1:
                self.cmb_engine.addItem("NMAP")

            # autocompletar ruta nmap si está en PATH
            if not self.ed_nmap.text().strip():
                p = find_nmap_in_path()
                if p:
                    self.ed_nmap.setText(p)
        else:
            self.banner.setVisible(False)
            self.btn_insecure.setEnabled(True)

            # ocultar NMAP totalmente
            idx = self.cmb_engine.findText("NMAP")
            if idx != -1:
                # si estaba seleccionado, volver a NATIVE
                if self.cmb_engine.currentText() == "NMAP":
                    self.cmb_engine.setCurrentText("NATIVE")
                self.cmb_engine.removeItem(idx)

        self.sync_engine_ui()

    def activate_insecure(self):
        global INSECURE_ACTIVE
        if INSECURE_ACTIVE:
            return

        d1 = InsecureDialog(1)
        if d1.exec() != QDialog.Accepted:
            return

        d2 = InsecureDialog(2)
        if d2.exec() != QDialog.Accepted:
            return

        d3 = InsecureDialog(3)
        if d3.exec() != QDialog.Accepted or not d3.confirmed():
            QMessageBox.warning(self, "Modo Inseguro", "No confirmado. Modo Inseguro NO activado.")
            return

        INSECURE_ACTIVE = True
        self.refresh_insecure_ui()
        self.lbl_status.setText("Modo Inseguro activado (persistente hasta reiniciar).")
        QMessageBox.critical(
    self,
    "MODO INSEGURO ACTIVADO",
    "Bienvenido al MODO INSEGURO.\n\n"
    "El escaneo activo con Nmap ha sido habilitado.\n\n"
    "Ahora puede ejecutar escaneos sobre objetivos definidos por el usuario.\n"
    "Estos escaneos pueden generar tráfico visible, registros en sistemas remotos\n"
    "y alertas automáticas en infraestructuras protegidas.\n\n"
    "Para desbloquear el potencial completo:\n"
    "• Ejecute SentinelDesk como Administrador.\n"
    "• Asegúrese de tener Npcap correctamente instalado.\n\n"
    "Sin privilegios elevados o sin Npcap, ciertas capacidades avanzadas\n"
    "(SYN scan, detección de sistema operativo, funciones NSE específicas)\n"
    "no estarán disponibles.\n\n"
    "Toda responsabilidad derivada del uso de este modo recae exclusivamente en el usuario.\n\n"
    "Utilícelo bajo su propio riesgo."
)

    def pick_nmap(self):
        f, _ = QFileDialog.getOpenFileName(self, "Seleccionar nmap.exe", "", "nmap.exe (nmap.exe)")
        if f:
            self.ed_nmap.setText(f)

    def run(self):
        if self.worker and self.worker.isRunning():
            return

        global INSECURE_ACTIVE

        engine = self.cmb_engine.currentText()  # NATIVE / NMAP
        ports_text = self.ed_ports.text().strip()
        ports = parse_ports(ports_text)

        # Gate duro: NMAP solo si inseguro activo
        if engine == "NMAP" and not INSECURE_ACTIVE:
            QMessageBox.warning(self, "Nmap", "Nmap solo está disponible si activás Modo Inseguro.")
            self.cmb_engine.setCurrentText("NATIVE")
            return

        self.model.set_rows([])
        self.detail.clear()
        self.nmap_out.clear()
        self.lbl_status.setText("Iniciando…")

        self.btn_run.setEnabled(False)

        self.worker = PortsWorker(
            engine=engine,
            ports=ports,
            timeout_connect=float(self.spn_connect.value()),
            timeout_probe=float(self.spn_probe.value()),
            workers=int(self.spn_workers.value()),
            nmap_path=self.ed_nmap.text().strip(),
            nmap_args=self.ed_args.text().strip(),
        )
        self.worker.progress.connect(self.lbl_status.setText)
        self.worker.result.connect(self.on_rows)
        self.worker.nmap_output.connect(self.on_nmap_out)
        self.worker.error.connect(self.on_error)
        self.worker.finished.connect(lambda: self.btn_run.setEnabled(True))
        self.worker.start()

    def on_rows(self, rows):
        self.model.set_rows(rows)
        if rows:
            self.table.selectRow(0)
            self.show(rows[0])
        else:
            self.detail.setPlainText("Sin resultados.")

    def on_nmap_out(self, txt: str):
        self.nmap_out.append(txt)

    def on_error(self, msg: str):
        QMessageBox.warning(self, "Puertos", msg)
        self.lbl_status.setText("Error.")

    def on_select(self, idx):
        r = self.model.get(idx.row())
        if r:
            self.show(r)

    def show(self, r):
        txt = (
            f"Host: {r.get('Host','')}\n"
            f"Port: {r.get('Port','')}\n"
            f"State: {r.get('State','')}\n"
            f"Service: {r.get('Service','')}\n"
            f"Confidence: {r.get('Confidence','')}\n"
            f"PID: {r.get('PID','')}\n"
            f"Process: {r.get('Process','')}\n"
            f"User: {r.get('User','')}\n"
            f"Path: {r.get('Path','')}\n"
        )
        if r.get("Notes"):
            txt += f"\nNotes:\n{r['Notes']}\n"
        if r.get("Evidence"):
            txt += f"\nEvidence:\n{r['Evidence']}\n"
        self.detail.setPlainText(txt)
