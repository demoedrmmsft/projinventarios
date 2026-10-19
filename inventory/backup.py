import json
import sqlite3
import tempfile
from contextlib import closing
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


def create_backup(database_path, secret_path, destination):
    database_path, destination = Path(database_path), Path(destination)
    if not database_path.is_file():
        raise ValueError("No existe la base de datos para respaldar.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as directory:
        snapshot = Path(directory) / "inventory.sqlite3"
        with closing(sqlite3.connect(database_path)) as source, closing(sqlite3.connect(snapshot)) as target:
            source.backup(target)
            if target.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise ValueError("El respaldo no paso la comprobacion de integridad.")
        with ZipFile(destination, "x", compression=ZIP_DEFLATED) as archive:
            archive.write(snapshot, "inventory.sqlite3")
            archive.write(secret_path, "secret.key")
            archive.writestr("manifest.json", json.dumps({"format": 1, "database": "SQLite", "includes_mail_tokens": False}))
        with ZipFile(destination) as archive:
            restored = Path(directory) / "restored.sqlite3"
            restored.write_bytes(archive.read("inventory.sqlite3"))
            with closing(sqlite3.connect(restored)) as restored_connection:
                if restored_connection.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                    raise ValueError("Fallo la prueba de lectura del respaldo restaurado.")
    return destination