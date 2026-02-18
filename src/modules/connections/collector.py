import os
import socket
import psutil

def _proto(sock_type):
    if sock_type == socket.SOCK_STREAM:
        return "TCP"
    if sock_type == socket.SOCK_DGRAM:
        return "UDP"
    return "?"

def _addr(a):
    if not a:
        return ""
    try:
        return f"{a.ip}:{a.port}"
    except Exception:
        return str(a)

def _safe(proc, fn, default=""):
    try:
        return fn(proc) or default
    except Exception:
        return default

def collect_connections(include_udp=True):
    # kind="all" returns tcp+udp, but can be heavier; still OK for LAN scale
    kind = "all" if include_udp else "tcp"
    try:
        conns = psutil.net_connections(kind=kind)
    except Exception:
        conns = []

    proc_cache = {}
    rows = []

    for c in conns:
        proto = _proto(c.type)
        if (not include_udp) and proto == "UDP":
            continue

        laddr = _addr(c.laddr)
        raddr = _addr(c.raddr) if c.raddr else ""
        status = c.status if proto == "TCP" else ""
        pid = c.pid if c.pid is not None else None

        pname = puser = pexe = ""

        if pid is not None:
            if pid in proc_cache:
                pname, puser, pexe = proc_cache[pid]
            else:
                try:
                    p = psutil.Process(pid)
                    pname = _safe(p, lambda x: x.name(), "")
                    puser = _safe(p, lambda x: x.username(), "")
                    pexe  = _safe(p, lambda x: x.exe(), "")
                except Exception:
                    pname = puser = pexe = ""
                proc_cache[pid] = (pname, puser, pexe)

        rows.append({
            "Proto": proto,
            "State": status,
            "Local": laddr,
            "Remote": raddr,
            "PID": "" if pid is None else str(pid),
            "Process": pname,
            "User": puser,
            "Path": pexe,
        })

    # Sort: established, listen, others
    def k(r):
        st = r["State"]
        pr = 2
        if r["Proto"] == "TCP":
            if st == "ESTABLISHED": pr = 0
            elif st == "LISTEN": pr = 1
        return (pr, r["Process"], r["PID"], r["Local"])

    rows.sort(key=k)
    return rows
