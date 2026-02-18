import socket
import ssl

def _recv(sock, n=4096):
    try:
        return sock.recv(n)
    except Exception:
        return b""

def _decode(b: bytes) -> str:
    try:
        return b.decode("utf-8", errors="replace")
    except Exception:
        return repr(b)

def _is_http(b: bytes) -> bool:
    u = b.upper()
    return u.startswith(b"HTTP/") or b"SERVER:" in u or b"CONTENT-TYPE" in u or b"<!DOCTYPE HTML" in u

def probe_http(ip: str, port: int, timeout: float):
    with socket.create_connection((ip, port), timeout=timeout) as s:
        s.settimeout(timeout)
        s.sendall(b"HEAD / HTTP/1.1\r\nHost: localhost\r\nUser-Agent: SentinelDesk\r\nConnection: close\r\n\r\n")
        b = _recv(s, 4096)
        if b and _is_http(b):
            txt = _decode(b)
            server = ""
            for line in txt.splitlines():
                if line.lower().startswith("server:"):
                    server = line.split(":", 1)[1].strip()
                    break
            notes = f"server={server}" if server else ""
            return True, "HTTP", "CONFIRMED", notes, txt
    return False, "", "", "", ""

def probe_tls(ip: str, port: int, timeout: float):
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with socket.create_connection((ip, port), timeout=timeout) as raw:
            raw.settimeout(timeout)
            with ctx.wrap_socket(raw, server_hostname="localhost") as s:
                # If handshake ok => TLS
                cert = s.getpeercert()
                notes = "TLS handshake ok"
                if cert:
                    notes = "TLS cert present"
                # try HTTPS HEAD
                try:
                    s.sendall(b"HEAD / HTTP/1.1\r\nHost: localhost\r\nUser-Agent: SentinelDesk\r\nConnection: close\r\n\r\n")
                    b = _recv(s, 4096)
                    if b and _is_http(b):
                        return True, "HTTPS", "CONFIRMED", notes, _decode(b)
                except Exception:
                    pass
                return True, "TLS", "CONFIRMED", notes, ""
    except Exception:
        return False, "", "", "", ""

def probe_ssh(ip: str, port: int, timeout: float):
    try:
        with socket.create_connection((ip, port), timeout=timeout) as s:
            s.settimeout(timeout)
            b = _recv(s, 256)
            if b and b.upper().startswith(b"SSH-"):
                return True, "SSH", "CONFIRMED", "", _decode(b)
    except Exception:
        pass
    return False, "", "", "", ""

def probe_rdp(ip: str, port: int, timeout: float):
    """
    Minimal RDP cookie probe (best-effort).
    """
    pkt = b"\x03\x00\x00\x13\x0e\xd0\x00\x00\x12\x34\x00\x02\x00\x08\x00\x02\x00\x00\x00"
    try:
        with socket.create_connection((ip, port), timeout=timeout) as s:
            s.settimeout(timeout)
            s.sendall(pkt)
            b = _recv(s, 64)
            if b and b.startswith(b"\x03\x00"):
                return True, "RDP", "CONFIRMED", "RDP-like response", b.hex()
    except Exception:
        pass
    return False, "", "", "", ""

def fingerprint_localhost(port: int, timeout: float = 0.6):
    ip = "127.0.0.1"

    # 1) SSH
    ok, svc, conf, notes, ev = probe_ssh(ip, port, timeout)
    if ok: return svc, conf, notes, ev

    # 2) TLS/HTTPS
    ok, svc, conf, notes, ev = probe_tls(ip, port, timeout)
    if ok: return svc, conf, notes, ev

    # 3) HTTP
    ok, svc, conf, notes, ev = probe_http(ip, port, timeout)
    if ok: return svc, conf, notes, ev

    # 4) RDP
    ok, svc, conf, notes, ev = probe_rdp(ip, port, timeout)
    if ok: return svc, conf, notes, ev

    # 5) fallback banner
    try:
        with socket.create_connection((ip, port), timeout=timeout) as s:
            s.settimeout(timeout)
            b = _recv(s, 512)
            if b:
                return "UNKNOWN", "PROBABLE", "banner present", _decode(b)
    except Exception:
        pass

    return "UNKNOWN", "UNKNOWN", "", ""
