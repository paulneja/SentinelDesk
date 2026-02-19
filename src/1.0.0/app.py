from PySide6.QtWidgets import QDialog
from ui.main_window import MainWindow
from core.terms import (
    terms_already_accepted,
    save_terms_acceptance,
    TermsDialog
)

APP_VERSION = "1.0"

# IMPORTANTE: mantener referencia viva
_main_window = None


def start_application():
    """
    Controla términos y abre la ventana principal.
    Retorna la MainWindow si continúa, o None si debe cerrarse.
    """
    global _main_window

    # -------------------------------
    # Verificar aceptación previa
    # -------------------------------
    try:
        accepted = terms_already_accepted()
    except Exception:
        accepted = False

    # -------------------------------
    # Mostrar términos si no aceptados
    # -------------------------------
    if not accepted:
        dialog = TermsDialog()
        result = dialog.exec()

        if result != QDialog.Accepted:
            return None

        try:
            save_terms_acceptance()
        except Exception:
            return None

    # -------------------------------
    # Abrir ventana principal
    # -------------------------------
    _main_window = MainWindow()
    _main_window.show()

    return _main_window
