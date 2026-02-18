import subprocess
import shlex


def run_nmap(nmap_path: str, args: str):
    """
    Ejecuta nmap exactamente con los argumentos proporcionados.
    No fuerza localhost.
    No agrega targets.
    El usuario define todo en args.
    """

    if not nmap_path:
        return 2, "", "Ruta a nmap.exe vacía."

    cmd = [nmap_path] + shlex.split(args, posix=False)

    p = subprocess.run(
        cmd,
        capture_output=True,
        text=True
    )

    return p.returncode, p.stdout or "", p.stderr or ""
