import psutil
import socket

def audit_listeners():
    """
    Returns list of dict rows for LISTEN sockets on local machine.
    No scanning. Just reads OS state.
    """
    rows = []
    try:
        conns = psutil.net_connections(kind="tcp")
    except Exception:
        conns = []

    proc_cache = {}

    for c in conns:
        if c.status != "LISTEN":
            continue
        l = c.laddr
        if not l:
            continue
        ip = getattr(l, "ip", "")
        port = getattr(l, "port", "")
        pid = c.pid

        pname = user = exe = ""
        if pid:
            if pid in proc_cache:
                pname, user, exe = proc_cache[pid]
            else:
                try:
                    p = psutil.Process(pid)
                    pname = p.name()
                    user = p.username()
                    exe = p.exe()
                except Exception:
                    pass
                proc_cache[pid] = (pname, user, exe)

        rows.append({
            "Host": ip or "0.0.0.0",
            "Port": int(port),
            "State": "LISTEN",
            "Service": "—",
            "Confidence": "—",
            "PID": str(pid or ""),
            "Process": pname,
            "User": user,
            "Path": exe,
            "Evidence": "",
            "Notes": "Listener (audit)"
        })

    rows.sort(key=lambda r: (r["Host"], r["Port"], r["Process"]))
    return rows
