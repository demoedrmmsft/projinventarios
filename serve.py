import os

from django.contrib.staticfiles.handlers import StaticFilesHandler
from waitress import serve

from lab.wsgi import application

if __name__ == "__main__":
    port = int(os.environ.get("LAB_PORT", "8000"))
    print(f"Lote LAB: http://127.0.0.1:{port}", flush=True)
    serve(StaticFilesHandler(application), host="127.0.0.1", port=port, threads=4)