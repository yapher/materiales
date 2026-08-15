from pathlib import Path
import base64

# ==========================================================
# CONFIGURACIÓN GENERAL
# ==========================================================

# Carpeta del proyecto
RAIZ = Path(__file__).resolve().parent

# Archivo de salida
SALIDA = RAIZ / "Proyecto_Completo.txt"
SALIDA_RESOLUTA = SALIDA.resolve()

# Si está en True, los archivos binarios se exportan como base64.
# Atención: puede generar un archivo enorme si hay .xlsx, .pkl, .zip, imágenes, etc.
INCLUIR_BINARIOS_BASE64 = False

# Carpetas a ignorar
IGNORAR_CARPETAS = {
    ".git",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    ".idea",
    ".vscode",
    "node_modules",
    "dist",
    "build",
    "instance",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".eggs",
    "site-packages",
}

# Archivos a ignorar
IGNORAR_ARCHIVOS = {
    ".DS_Store",
    "Thumbs.db",
    "desktop.ini",
    "Proyecto_Completo.txt",
    "exportar_proyecto_output.txt",
}

# Extensiones que se consideran texto / código
EXTENSIONES_TEXTO = {
    ".py",
    ".html",
    ".css",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".json",
    ".txt",
    ".md",
    ".rst",
    ".yml",
    ".yaml",
    ".toml",
    ".ini",
    ".cfg",
    ".conf",
    ".env",
    ".csv",
    ".tsv",
    ".sql",
    ".xml",
    ".bat",
    ".sh",
    ".ps1",
    ".gitignore",
    ".dockerignore",
    ".dockerfile",
    ".log",
    ".svg",
    ".example",
    ".sample",
    ".properties",
}

# Archivos especiales que pueden no tener extensión clara
ARCHIVOS_TEXTO_ESPECIALES = {
    ".gitignore",
    ".dockerignore",
    ".env",
    ".env.example",
    ".flaskenv",
    ".editorconfig",
    "Procfile",
    "Dockerfile",
    "Makefile",
    "LICENSE",
    "runtime.txt",
    "requirements.txt",
}

# Extensiones binarias comunes
EXTENSIONES_BINARIAS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".ico",
    ".webp",
    ".bmp",
    ".pdf",
    ".xlsx",
    ".xls",
    ".doc",
    ".docx",
    ".pkl",
    ".joblib",
    ".zip",
    ".gz",
    ".tar",
    ".7z",
    ".rar",
    ".sqlite",
    ".sqlite3",
    ".pyc",
    ".pyo",
    ".pyd",
    ".woff",
    ".woff2",
    ".ttf",
    ".otf",
    ".eot",
    ".mp4",
    ".mp3",
    ".avi",
    ".mov",
}


# ==========================================================
# FUNCIONES AUXILIARES
# ==========================================================

def debe_ignorarse(ruta: Path) -> bool:
    """
    Determina si una carpeta o archivo debe ignorarse.
    """
    try:
        if ruta.resolve() == SALIDA_RESOLUTA:
            return True
    except OSError:
        pass

    try:
        rel = ruta.relative_to(RAIZ)
    except ValueError:
        return True

    partes = rel.parts

    if ruta.is_dir():
        # Ignorar carpetas prohibidas en cualquier nivel.
        if any(parte in IGNORAR_CARPETAS for parte in partes):
            return True
    else:
        # Ignorar archivos dentro de carpetas prohibidas.
        if any(parte in IGNORAR_CARPETAS for parte in partes[:-1]):
            return True

    if ruta.name in IGNORAR_ARCHIVOS:
        return True

    return False


def parece_binaria(ruta: Path) -> bool:
    """
    Intenta detectar si un archivo es binario.
    Si tiene BOM de texto, lo considera texto.
    """
    if ruta.suffix.lower() in EXTENSIONES_BINARIAS:
        return True

    try:
        with ruta.open("rb") as fh:
            chunk = fh.read(8192)
    except OSError:
        return True

    # BOM comunes de texto.
    if chunk.startswith((b"\xef\xbb\xbf", b"\xff\xfe", b"\xfe\xff")):
        return False

    # Muchos binarios tienen bytes nulos.
    if b"\x00" in chunk:
        return True

    return False


def es_texto(ruta: Path) -> bool:
    """
    Determina si un archivo se debe exportar como texto.
    """
    suffix = ruta.suffix.lower()

    if suffix in EXTENSIONES_TEXTO:
        return True

    if ruta.name in ARCHIVOS_TEXTO_ESPECIALES:
        return True

    # Cualquier archivo .env* se considera texto.
    if ruta.name.startswith(".env"):
        return True

    if parece_binaria(ruta):
        return False

    return True


def leer_texto(ruta: Path) -> str:
    """
    Lee un archivo probando varias codificaciones.
    Esto ayuda con archivos UTF-8, UTF-8 BOM, UTF-16, Latin-1, etc.
    """
    raw = ruta.read_bytes()

    if not raw:
        return ""

    # UTF-8 con BOM
    if raw.startswith(b"\xef\xbb\xbf"):
        return raw.decode("utf-8-sig", errors="replace")

    # UTF-16 LE / BE
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        return raw.decode("utf-16", errors="replace")

    encodings = [
        "utf-8",
        "utf-16",
        "cp1252",
        "latin-1",
    ]

    for enc in encodings:
        try:
            return raw.decode(enc)
        except (UnicodeDecodeError, UnicodeError):
            pass

    return raw.decode("latin-1", errors="replace")


def escribir_seccion(archivo, ruta_relativa: str, contenido: str = "", nota: str = None):
    """
    Escribe una sección de archivo dentro del export.
    """
    archivo.write("\n")
    archivo.write("=" * 80 + "\n")
    archivo.write(ruta_relativa + "\n")
    archivo.write("=" * 80 + "\n\n")

    if nota:
        archivo.write(nota + "\n\n")

    if contenido:
        archivo.write(contenido)
        if not contenido.endswith("\n"):
            archivo.write("\n")


def dibujar_arbol(carpeta: Path, archivo, prefijo: str = "") -> None:
    """
    Dibuja el árbol del proyecto.
    """
    try:
        elementos = sorted(
            carpeta.iterdir(),
            key=lambda x: (x.is_file(), x.name.lower())
        )
    except OSError:
        return

    elementos = [
        e for e in elementos
        if not debe_ignorarse(e)
    ]

    for i, elemento in enumerate(elementos):
        ultimo = i == len(elementos) - 1
        rama = "└── " if ultimo else "├── "

        archivo.write(prefijo + rama + elemento.name + "\n")

        if elemento.is_dir():
            extension = "    " if ultimo else "│   "
            dibujar_arbol(elemento, archivo, prefijo + extension)


def obtener_archivos():
    """
    Obtiene todos los archivos válidos del proyecto.
    """
    archivos = []

    for f in RAIZ.rglob("*"):
        if f.is_file() and not debe_ignorarse(f):
            archivos.append(f)

    return sorted(
        archivos,
        key=lambda p: p.relative_to(RAIZ).as_posix().lower()
    )


# ==========================================================
# EXPORTACIÓN PRINCIPAL
# ==========================================================

def main():
    exportados = 0
    binarios_omitidos = 0
    errores = 0

    with SALIDA.open("w", encoding="utf-8", newline="\n") as archivo:

        archivo.write("=" * 80 + "\n")
        archivo.write("ARBOL DEL PROYECTO\n")
        archivo.write("=" * 80 + "\n\n")

        archivo.write(RAIZ.name + "\n")
        dibujar_arbol(RAIZ, archivo)

        archivo.write("\n\n")
        archivo.write("=" * 80 + "\n")
        archivo.write("CONTENIDO DE LOS ARCHIVOS\n")
        archivo.write("=" * 80 + "\n\n")

        for f in obtener_archivos():

            rel = f.relative_to(RAIZ).as_posix()

            try:
                if es_texto(f):
                    contenido = leer_texto(f)
                    escribir_seccion(archivo, rel, contenido=contenido)
                    exportados += 1

                elif INCLUIR_BINARIOS_BASE64:
                    b64 = base64.encodebytes(f.read_bytes()).decode("ascii")
                    contenido = "<<BASE64>>\n" + b64 + "<<FIN_BASE64>>\n"
                    nota = (
                        f"Archivo binario exportado como base64 "
                        f"({f.suffix.lower() or 'sin extensión'}). "
                        "Para restaurarlo, decodificar el bloque entre "
                        "<<BASE64>> y <<FIN_BASE64>>."
                    )
                    escribir_seccion(archivo, rel, contenido=contenido, nota=nota)
                    exportados += 1

                else:
                    nota = (
                        f"<<ARCHIVO BINARIO OMITIDO: "
                        f"{f.suffix.lower() or 'sin extensión'}>>\n"
                        "Si necesitás incluirlo en el export, poné: "
                        "INCLUIR_BINARIOS_BASE64 = True"
                    )
                    escribir_seccion(archivo, rel, contenido="", nota=nota)
                    binarios_omitidos += 1

            except Exception as e:
                escribir_seccion(
                    archivo,
                    rel,
                    contenido="",
                    nota=f"<<ERROR AL LEER: {e}>>"
                )
                errores += 1

    print(f"Archivo generado: {SALIDA}")
    print(f"Archivos de texto exportados: {exportados}")
    print(f"Archivos binarios omitidos: {binarios_omitidos}")
    print(f"Errores: {errores}")


if __name__ == "__main__":
    main()