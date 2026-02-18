import os
import math
import hashlib
import mimetypes
from pathlib import Path

MAX_BYTES = int(0.5 * 1024 * 1024 * 1024)  # 0.5 GB

# Límites seguros (no colapsa aunque el archivo sea enorme)
HASH_CHUNK = 1024 * 1024          # 1 MB
ENTROPY_CHUNK = 1024 * 1024       # 1 MB
STRINGS_CHUNK = 1024 * 1024       # 1 MB
HEX_PREVIEW_BYTES = 64 * 1024     # 64 KB
STRINGS_MAX = 2000                # preview
MIN_STRING_LEN = 4                # strings mínimas


def fmt_bytes(n: int) -> str:
    if n < 1024:
        return f"{n} B"
    units = ["KB", "MB", "GB", "TB"]
    x = float(n)
    for u in units:
        x /= 1024.0
        if x < 1024.0:
            return f"{x:.2f} {u}"
    return f"{x:.2f} PB"


def file_times(path: str) -> dict:
    st = os.stat(path)
    # Windows: st_ctime suele ser "creation time" (en Unix es change time).
    # Igual lo mostramos como "Creación" porque tu target es Win11.
    return {
        "Creación": st.st_ctime,
        "Modificación": st.st_mtime,
        "Acceso": st.st_atime,
    }


def detect_mime(path: str) -> str:
    # MIME por extensión (rápido). Después lo complementamos por firma simple.
    mt, _ = mimetypes.guess_type(path)
    if not mt:
        mt = "application/octet-stream"
    sig = sniff_signature(path)
    if sig:
        return f"{mt} ({sig})"
    return mt


def sniff_signature(path: str) -> str:
    # Firma rápida: no pretende ser infalible, solo dar señales útiles.
    try:
        with open(path, "rb") as f:
            b = f.read(16)
    except Exception:
        return ""

    if b.startswith(b"MZ"):
        return "PE/MZ"
    if b.startswith(b"\x7FELF"):
        return "ELF"
    if b.startswith(b"PK\x03\x04"):
        return "ZIP"
    if b.startswith(b"%PDF"):
        return "PDF"
    if b.startswith(b"\x89PNG\r\n\x1a\n"):
        return "PNG"
    if b[:3] == b"\xFF\xD8\xFF":
        return "JPEG"
    if b.startswith(b"GIF87a") or b.startswith(b"GIF89a"):
        return "GIF"
    if b.startswith(b"Rar!\x1a\x07\x00") or b.startswith(b"Rar!\x1a\x07\x01\x00"):
        return "RAR"
    return ""


def compute_hashes_stream(path: str, progress_cb=None) -> dict:
    total = os.path.getsize(path)
    done = 0

    md5 = hashlib.md5()
    sha256 = hashlib.sha256()

    with open(path, "rb") as f:
        while True:
            chunk = f.read(HASH_CHUNK)
            if not chunk:
                break
            md5.update(chunk)
            sha256.update(chunk)
            done += len(chunk)
            if progress_cb and total > 0:
                progress_cb(done, total)

    return {
        "MD5": md5.hexdigest(),
        "SHA256": sha256.hexdigest(),
    }


def entropy_stream(path: str, max_bytes: int | None = None) -> float:
    # Shannon entropy (0..8 para bytes)
    counts = [0] * 256
    total = 0

    limit = max_bytes if max_bytes is not None else os.path.getsize(path)

    with open(path, "rb") as f:
        while total < limit:
            chunk = f.read(min(ENTROPY_CHUNK, limit - total))
            if not chunk:
                break
            for x in chunk:
                counts[x] += 1
            total += len(chunk)

    if total == 0:
        return 0.0

    ent = 0.0
    for c in counts:
        if c:
            p = c / total
            ent -= p * math.log2(p)
    return float(ent)


def extract_strings_preview(path: str, max_strings: int = STRINGS_MAX) -> list[str]:
    # Extrae strings ASCII visibles, en streaming, y corta en max_strings.
    # No guarda todo el archivo, no explota memoria.
    out: list[str] = []
    buf = bytearray()

    def flush():
        nonlocal buf
        if len(buf) >= MIN_STRING_LEN:
            try:
                out.append(buf.decode("ascii", errors="ignore"))
            except Exception:
                pass
        buf = bytearray()

    with open(path, "rb") as f:
        while len(out) < max_strings:
            chunk = f.read(STRINGS_CHUNK)
            if not chunk:
                break
            for b in chunk:
                if 32 <= b <= 126:  # printable ascii
                    buf.append(b)
                    if len(buf) > 4096:  # evita strings infinitas
                        flush()
                        if len(out) >= max_strings:
                            break
                else:
                    flush()
                    if len(out) >= max_strings:
                        break

    flush()
    return out[:max_strings]


def read_hex_preview(path: str, n: int = HEX_PREVIEW_BYTES) -> bytes:
    with open(path, "rb") as f:
        return f.read(n)


def is_pe(path: str) -> bool:
    try:
        with open(path, "rb") as f:
            return f.read(2) == b"MZ"
    except Exception:
        return False


def pe_basic_info(path: str) -> dict:
    """
    PE info básico sin librerías externas.
    No es forense completo: solo cosas útiles.
    """
    info = {}
    try:
        with open(path, "rb") as f:
            mz = f.read(64)
            if len(mz) < 64 or mz[:2] != b"MZ":
                return {}

            e_lfanew = int.from_bytes(mz[0x3C:0x40], "little", signed=False)
            f.seek(e_lfanew)
            sig = f.read(4)
            if sig != b"PE\0\0":
                return {}

            file_header = f.read(20)
            machine = int.from_bytes(file_header[0:2], "little")
            n_sections = int.from_bytes(file_header[2:4], "little")
            ts = int.from_bytes(file_header[4:8], "little")
            opt_size = int.from_bytes(file_header[16:18], "little")

            info["PE.Machine"] = {
                0x014c: "x86",
                0x8664: "x64",
                0x01c0: "ARM",
                0xAA64: "ARM64",
            }.get(machine, hex(machine))
            info["PE.Sections"] = str(n_sections)
            info["PE.Timestamp"] = str(ts)
            info["PE.OptionalHeaderSize"] = str(opt_size)

            # Optional header magic
            opt = f.read(opt_size)
            if len(opt) >= 2:
                magic = int.from_bytes(opt[0:2], "little")
                info["PE.OptionalMagic"] = {0x10b: "PE32", 0x20b: "PE32+"}.get(magic, hex(magic))

    except Exception:
        return {}

    return info
