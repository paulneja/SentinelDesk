def classify_event(channel: str, level: str, event_id: str, message: str):
    """
    Returns: (score 0..100, category, action_hint)
    category: INFO/WARN/ERROR/CRITICAL
    """
    lvl = (level or "").upper()
    msg = (message or "").lower()
    ch = (channel or "").lower()
    eid = (event_id or "").strip()

    # Base from level
    base = {"INFORMATION": 10, "INFO": 10, "WARNING": 35, "WARN": 35, "ERROR": 60, "CRITICAL": 90}.get(lvl, 20)
    score = base
    category = "INFO" if score < 25 else "WARN" if score < 50 else "ERROR" if score < 80 else "CRITICAL"
    action = ""

    # Obvious critical disk / filesystem hints
    if "disk" in ch or "ntfs" in msg or "storport" in msg:
        if "bad block" in msg or "corrupt" in msg or "i/o" in msg or "crc" in msg:
            score = max(score, 90); category = "CRITICAL"
            action = "Revisar disco: backups + CHKDSK + revisar cables/energía + mirar eventos repetidos."
        elif "reset" in msg or "timeout" in msg:
            score = max(score, 80); category = "CRITICAL"
            action = "Posible problema de almacenamiento/controlador. Revisar drivers + energía + revisar si se repite."

    # Unexpected shutdown hints
    if eid == "41" and "kernel-power" in msg:
        score = max(score, 75); category = "ERROR"
        action = "Apagado inesperado. Revisar fuente/UPS/cortes, y si coincide con cuelgues o temperatura."

    # Defender hints
    if "windows defender" in ch or "defender" in msg:
        if "malware" in msg or "threat" in msg or "detected" in msg:
            score = max(score, 85); category = "CRITICAL"
            action = "Amenaza detectada. Revisar detalles, aislar archivo, scan completo y verificar persistencia."

    # Service crash loop-ish hints
    if "service" in msg and ("failed" in msg or "terminated" in msg or "crash" in msg):
        score = max(score, 55); category = "ERROR"
        if not action:
            action = "Servicio fallando. Ver eventos repetidos + dependencias + reinstalar/repair si aplica."

    return score, category, action
