import socket
from concurrent.futures import ThreadPoolExecutor, as_completed
from modules.ports.fingerprint import fingerprint_localhost

def _is_open_local(port: int, timeout: float) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=timeout):
            return True
    except Exception:
        return False

def native_scan_localhost(ports: list[int], timeout_connect: float, timeout_probe: float, workers: int, progress_cb=None):
    """
    Returns list of dict rows.
    """
    rows = []
    total = len(ports)
    done = 0

    def job(p: int):
        if not _is_open_local(p, timeout_connect):
            return None
        svc, conf, notes, evidence = fingerprint_localhost(p, timeout=timeout_probe)
        return {
            "Host": "127.0.0.1",
            "Port": p,
            "State": "OPEN",
            "Service": svc,
            "Confidence": conf,
            "PID": "",
            "Process": "",
            "User": "",
            "Path": "",
            "Evidence": evidence[:2000],
            "Notes": notes
        }

    with ThreadPoolExecutor(max_workers=max(1, workers)) as ex:
        futs = [ex.submit(job, p) for p in ports]
        for fut in as_completed(futs):
            done += 1
            if progress_cb and (done % 200 == 0 or done == total):
                progress_cb(f"Progreso: {done}/{total}")
            r = fut.result()
            if r:
                rows.append(r)

    rows.sort(key=lambda r: r["Port"])
    return rows
