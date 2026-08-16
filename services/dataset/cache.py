"""
Cache en memoria de datasets por usuario.

Mantiene los DataFrames cargados y firmas de archivo para
detectar cambios en disco sin releer en cada request.
"""

import os
import threading

# ==========================================================
# CACHE DATASET POR USUARIO (en memoria del proceso)
# ==========================================================
_datasets = {}
_dataset_firmas = {}
_lock_dataset = threading.Lock()


def _firma_archivo(ruta):
    """
    Devuelve una firma simple del archivo basada en
    fecha de modificación y tamaño.

    Sirve para saber si el Excel cambió en disco.
    """
    try:
        st = os.stat(ruta)

        mtime = getattr(st, "st_mtime_ns", None)
        if mtime is None:
            mtime = int(st.st_mtime * 1_000_000_000)

        return (mtime, st.st_size)
    except OSError:
        return None