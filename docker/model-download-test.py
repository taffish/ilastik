"""离线 TLS loopback + 纯合成 ZIP；不解析、下载或运行生产模型。"""
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import ssl
import subprocess
import tempfile
import threading


def run(args, *, env=None, status=0, marker=None):
    result = subprocess.run(args, env=env, text=True, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, timeout=90)
    if result.returncode != status or (marker and marker not in result.stdout):
        raise AssertionError(f"stage={args[0]} expected={status} actual={result.returncode}\n{result.stdout[-8000:]}")
    return result.stdout


with tempfile.TemporaryDirectory(prefix="taf-ilastik-download-") as name:
    work = Path(name)
    run(["python", "/usr/share/ilastik-taffish/model-fixture.py", str(work)])
    payload = (work / "model.zip").read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    run(["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-days", "1",
         "-subj", "/CN=localhost", "-addext", "subjectAltName=IP:127.0.0.1",
         "-keyout", str(work / "key.pem"), "-out", str(work / "cert.pem")])
    requests = []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            offset = 0
            requested_range = self.headers.get("Range")
            if requested_range:
                offset = int(requested_range.removeprefix("bytes=").split("-")[0])
            requests.append(offset)
            self.send_response(206 if requested_range else 200)
            self.send_header("Content-Length", str(len(payload) - offset))
            if requested_range:
                self.send_header("Content-Range", f"bytes {offset}-{len(payload)-1}/{len(payload)}")
            self.end_headers()
            self.wfile.write(payload[offset:])

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(work / "cert.pem", work / "key.pem")
    server.socket = context.wrap_socket(server.socket, server_side=True)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        root = work / "prepared" / "1.4.2"
        env = dict(os.environ, CURL_CA_BUNDLE=str(work / "cert.pem"))
        command = ["ilastik-models", "--model-id", "tiny-download", "--model-root", str(root),
                   "--url", f"https://127.0.0.1:{server.server_port}/fixed.zip",
                   "--sha256", digest, "--archive-bytes", str(len(payload)),
                   "--expected-license", "CC0-1.0"]
        run(command + ["--dry-run"], env=env, marker="explicit download plan")
        assert not requests and not root.exists(), "dry-run performed I/O"
        run(command, env=env, status=1, marker="requires --confirm-authorized-download")
        assert not requests
        cache = root.parent / ".ilastik-downloads"
        cache.mkdir(parents=True)
        (cache / f"{digest}.part").write_bytes(payload[:100])
        run(command + ["--confirm-authorized-download"], env=env, marker="Prepared ilastik model root")
        assert requests == [100], requests
        manifest = json.loads((root / ".taffish/models/tiny-download.json").read_text())
        assert manifest["resource_acquisition"] == "explicit-https-archive-download"
        run(command + ["--confirm-authorized-download"], env=env, marker="Already installed and verified")
        assert requests == [100], "verified cache was downloaded again"
        run(["ilastik-models", "--verify-only", "--model-root", str(root)], marker="Verified")
        (cache / f"{digest}.zip").write_bytes(b"bad cache")
        run(command + ["--confirm-authorized-download"], env=env, status=1, marker="corrupt cache")
        assert requests == [100], "corrupt cache was silently retried"
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=3)
print("ilastik TLS download/resume/cache/integrity/authorization contract ok; synthetic fixture only")
