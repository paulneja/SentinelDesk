import shutil
import ipaddress

def is_localhost(target: str) -> bool:
    t = (target or "").strip().lower()
    if t in ("localhost", "127.0.0.1", "::1"):
        return True
    try:
        ip = ipaddress.ip_address(t)
        return ip.is_loopback
    except Exception:
        return False

def find_nmap_in_path() -> str | None:
    p = shutil.which("nmap")
    return p

def parse_ports(text: str) -> list[int]:
    """
    Accepts: "80,443,8080" or "1-1024" or "22,80,8000-8100"
    """
    s = (text or "").strip()
    if not s:
        return list(range(1, 1025))

    ports: set[int] = set()
    parts = [p.strip() for p in s.split(",") if p.strip()]
    for p in parts:
        if "-" in p:
            a, b = p.split("-", 1)
            lo, hi = int(a.strip()), int(b.strip())
            if lo > hi:
                lo, hi = hi, lo
            lo = max(1, lo); hi = min(65535, hi)
            for x in range(lo, hi + 1):
                ports.add(x)
        else:
            x = int(p)
            if 1 <= x <= 65535:
                ports.add(x)

    return sorted(ports)
