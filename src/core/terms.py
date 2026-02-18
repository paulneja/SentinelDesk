import json
import os
from pathlib import Path
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel,
    QTextEdit, QPushButton, QHBoxLayout
)
from PySide6.QtCore import Qt


# -------------------------------
# Texto de términos
# -------------------------------
TERMS_TEXT = """
SentinelDesk — Términos y Condiciones de Uso

Copyright (C) 2026 PaulNeja & PN Security

SentinelDesk es software libre distribuido bajo la Licencia Pública General GNU (GPL v3 o posterior).
Su utilización implica la aceptación plena e incondicional de las siguientes disposiciones.

1. Naturaleza del Software

SentinelDesk es una herramienta técnica de análisis, diagnóstico y evaluación de sistemas.
Está destinada exclusivamente a auditorías defensivas, análisis en entornos propios o en sistemas donde el usuario posea autorización expresa y verificable.

No ha sido diseñada ni autorizada para la ejecución de actividades ofensivas, intrusivas o ilegales.

2. Advertencia de Uso y Responsabilidad Absoluta

El uso indebido de esta herramienta puede:

Constituir delito informático.

Generar responsabilidad penal.

Activar mecanismos automáticos de defensa en redes y sistemas.

Producir registros forenses permanentes.

Ser detectado por sistemas de monitoreo y correlación de eventos (SIEM).

Activar alertas en proveedores de servicios de Internet.

Generar bloqueo de cuentas, dispositivos o direcciones IP.

El desarrollador no controla ni supervisa el uso que cada usuario realice del software.

Cualquier utilización fuera de entornos propios o sin autorización expresa del titular del sistema auditado es responsabilidad exclusiva del usuario.

El desarrollador (PaulNeja & PN Security) se deslinda de toda responsabilidad civil, penal o administrativa derivada del uso indebido, imprudente o ilegal del software.

3. Prohibición de Actividades Ilegales

Se prohíbe expresamente utilizar SentinelDesk para:

Acceder a sistemas sin autorización.

Realizar escaneos no consentidos.

Ejecutar pruebas de intrusión en infraestructuras de terceros.

Interferir, degradar o interrumpir servicios.

Vulnerar privacidad o confidencialidad de datos.

La simple intención de utilizar la herramienta con fines hostiles constituye una violación de estas condiciones.

El usuario declara comprender que las actividades mencionadas pueden estar tipificadas como delito en múltiples jurisdicciones.

4. Exclusión de Garantías

SentinelDesk se distribuye “tal cual”, sin garantía alguna, explícita o implícita.

No se garantiza:

Ausencia de errores.

Funcionamiento ininterrumpido.

Exactitud de resultados.

Idoneidad para un propósito específico.

El uso del software se realiza bajo riesgo exclusivo del usuario.

5. Licencia y Redistribución

SentinelDesk se distribuye bajo la Licencia Pública General GNU (GPL v3 o posterior), lo que permite:

Uso personal o comercial.

Modificación del código.

Redistribución.

Siempre que:

Se mantenga esta misma licencia.

Se preserve el aviso de copyright.

Se proporcione acceso al código fuente en caso de redistribución.

La autoría de PaulNeja & PN Security no podrá ser eliminada ni alterada.

6. Funcionalidades Avanzadas y Modo Experimental

El software puede incluir funciones avanzadas que:

Generen tráfico de red identificable.

Produzcan registros en sistemas de monitoreo.

Sean interpretadas como actividad de reconocimiento.

El usuario declara comprender plenamente las implicaciones técnicas y legales del uso de dichas funciones.

7. Aceptación

Al utilizar SentinelDesk, el usuario confirma:

Haber leído y comprendido este documento.

Aceptar todas las condiciones sin reserva.

Asumir total responsabilidad por el uso del software.

Si no está de acuerdo con estas condiciones, debe abstenerse de utilizar el programa.
"""


# -------------------------------
# Ruta segura en AppData
# -------------------------------
def get_config_path():
    base = Path(os.getenv("APPDATA")) / "SentinelDesk"
    base.mkdir(parents=True, exist_ok=True)
    return base / "config.json"


# -------------------------------
# Verificación aceptación
# -------------------------------
def terms_already_accepted():
    path = get_config_path()
    if not path.exists():
        return False
    try:
        data = json.loads(path.read_text())
        return data.get("terms_accepted", False)
    except:
        return False


# -------------------------------
# Guardar aceptación
# -------------------------------
def save_terms_acceptance():
    path = get_config_path()
    data = {"terms_accepted": True}
    path.write_text(json.dumps(data, indent=2))


# -------------------------------
# Diálogo
# -------------------------------
class TermsDialog(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Términos y Condiciones")
        self.setMinimumSize(720, 520)

        layout = QVBoxLayout(self)

        title = QLabel("SentinelDesk — Términos y Condiciones")
        title.setStyleSheet("font-size:16px; font-weight:bold;")
        layout.addWidget(title)

        text = QTextEdit()
        text.setReadOnly(True)
        text.setPlainText(TERMS_TEXT)
        layout.addWidget(text)

        buttons = QHBoxLayout()

        btn_decline = QPushButton("Rechazar")
        btn_accept = QPushButton("Aceptar")

        btn_decline.clicked.connect(self.reject)
        btn_accept.clicked.connect(self.accept)

        buttons.addWidget(btn_decline)
        buttons.addWidget(btn_accept)

        layout.addLayout(buttons)
