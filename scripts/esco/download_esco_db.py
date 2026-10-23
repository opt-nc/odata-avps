#!/usr/bin/env python3
"""Télécharge et met en cache la base DuckDB du référentiel ESCO.

Source : https://github.com/adriens/odata-esco/releases/tag/v1.0.1
(ESCO v1.2.1, français — 3 039 professions, 13 939 compétences)

La base (~108 Mo) est cachée dans ~/.cache/esco/ et n'est JAMAIS commitée.
"""
import hashlib
import os
import sys
import urllib.request

ESCO_RELEASE = "v1.0.1"
ESCO_DB_URL = (
    "https://github.com/adriens/odata-esco/releases/download/"
    f"{ESCO_RELEASE}/esco.duckdb"
)
ESCO_DB_MD5 = "1d0d334b0e9bc76a532ba848721478a8"
CACHE_DIR = os.path.expanduser(os.environ.get("ESCO_CACHE_DIR", "~/.cache/esco"))
DB_PATH = os.path.join(CACHE_DIR, "esco.duckdb")


def md5sum(path: str) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def ensure_db() -> str:
    """Retourne le chemin de la base ESCO, en la téléchargeant si nécessaire."""
    if os.path.exists(DB_PATH) and md5sum(DB_PATH) == ESCO_DB_MD5:
        return DB_PATH
    os.makedirs(CACHE_DIR, exist_ok=True)
    print(f"⬇️  Téléchargement de esco.duckdb ({ESCO_RELEASE})…", file=sys.stderr)
    tmp = DB_PATH + ".tmp"
    urllib.request.urlretrieve(ESCO_DB_URL, tmp)
    actual = md5sum(tmp)
    if actual != ESCO_DB_MD5:
        os.remove(tmp)
        raise RuntimeError(
            f"Checksum MD5 inattendu pour esco.duckdb : {actual} != {ESCO_DB_MD5}"
        )
    os.replace(tmp, DB_PATH)
    print(f"✅ Base ESCO prête : {DB_PATH}", file=sys.stderr)
    return DB_PATH


if __name__ == "__main__":
    print(ensure_db())
