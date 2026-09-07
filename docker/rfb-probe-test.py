"""Offline protocol fixtures for the internal readiness probe, not GUI proof."""
from contextlib import contextmanager
from pathlib import Path
import runpy
import socket
import struct
import threading
import time

probe = runpy.run_path(str(Path(__file__).with_name("rfb-probe.py")))["probe"]


@contextmanager
def server(mode):
    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    listener.listen(1)
    listener.settimeout(2)
    stop = threading.Event()
    errors = []

    def handle():
        try:
            with listener.accept()[0] as connection:
                connection.settimeout(2)
                if mode == "silent":
                    stop.wait(2)
                    return
                greeting = b"HTTP/1.1 200" if mode == "bad-greeting" else b"RFB 003.008\n"
                for byte in greeting:  # exercise fragmented reads
                    connection.sendall(bytes([byte]))
                if mode == "bad-greeting":
                    return
                version = bytearray()
                while len(version) < 12:
                    version.extend(connection.recv(12 - len(version)))
                assert version == b"RFB 003.008\n"
                if mode == "refused":
                    connection.sendall(b"\x00")
                    return
                auth = mode == "password"
                connection.sendall(b"\x01\x02" if auth else b"\x01\x01")
                selected = connection.recv(1)
                if not selected:
                    return
                if auth:
                    assert selected == b"\x02"
                    connection.sendall(bytes(range(16)))
                    return
                assert selected == b"\x01"
                connection.sendall(b"\0\0\0\1" if mode == "security-failed" else b"\0\0\0\0")
                if mode == "security-failed":
                    return
                assert connection.recv(1) == b"\x01"
                width = 800 if mode == "wrong-size" else 1000
                name_size = 4097 if mode == "large-name" else 4
                connection.sendall(struct.pack("!HH16sI", width, 720, bytes(16), name_size))
                if mode != "large-name":
                    connection.sendall(b"test")
        except (ConnectionError, OSError):
            pass  # negative probes deliberately close an incomplete session
        except Exception as error:
            errors.append(error)

    thread = threading.Thread(target=handle)
    thread.start()
    try:
        yield listener.getsockname()[1]
    finally:
        stop.set()
        listener.close()
        thread.join(3)
        assert not thread.is_alive(), "protocol fixture thread leaked"
        assert not errors, errors


for mode in ("normal", "password"):
    with server(mode) as port:
        result = probe(port, 1000, 720, password=mode == "password")
        assert result.startswith("RFB ready:"), result
        print("PASS", mode, result)

for mode, expected in (
    ("bad-greeting", "greeting"), ("refused", "refused"),
    ("security-failed", "security negotiation failed"),
    ("wrong-size", "framebuffer"), ("large-name", "name"),
):
    with server(mode) as port:
        try:
            probe(port, 1000, 720)
        except ValueError as error:
            assert expected in str(error), (mode, error)
        else:
            raise AssertionError("accepted " + mode)
        print("PASS rejection", mode)

with server("normal") as port:
    try:
        probe(port, 1000, 720, password=True)
    except ValueError as error:
        assert "security offer" in str(error)
    else:
        raise AssertionError("accepted mismatched authentication")
    print("PASS rejection mismatched-authentication")

with server("silent") as port:
    start = time.monotonic()
    try:
        probe(port, 1000, 720, timeout=0.15)
    except TimeoutError:
        assert time.monotonic() - start < 1
    else:
        raise AssertionError("accepted listening socket without RFB")
    print("PASS bounded silent-listener rejection")
