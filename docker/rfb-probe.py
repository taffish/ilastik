"""Bounded localhost RFB 3.8 readiness, without a browser or external network."""
import argparse
import socket
import struct
import sys
import time


def probe(port, width, height, password=False, timeout=2.0):
    deadline = time.monotonic() + timeout
    with socket.create_connection(("127.0.0.1", port), timeout=timeout) as connection:
        def remaining():
            value = deadline - time.monotonic()
            if value <= 0:
                raise TimeoutError("RFB handshake deadline exceeded")
            connection.settimeout(value)

        def receive(size):
            result = bytearray()
            while len(result) < size:
                remaining()
                chunk = connection.recv(size - len(result))
                if not chunk:
                    raise ValueError("incomplete RFB handshake")
                result.extend(chunk)
            return bytes(result)

        def send(data):
            remaining()
            connection.sendall(data)

        if receive(12) != b"RFB 003.008\n":
            raise ValueError("expected RFB 3.8 server greeting")
        send(b"RFB 003.008\n")
        count = receive(1)[0]
        if count == 0:
            raise ValueError("RFB server refused security negotiation")
        types = receive(count)
        expected = 2 if password else 1
        if expected not in types:
            raise ValueError("RFB security offer does not match this session")
        send(bytes([expected]))
        if password:
            # Do not read/log a secret or bypass authentication. A real challenge
            # proves the password path responds; user authentication stays in VNC.
            receive(16)
            return "RFB ready: 3.8 security=vnc-auth challenge-ready"
        if receive(4) != b"\0\0\0\0":
            raise ValueError("RFB security negotiation failed")
        send(b"\x01")  # Shared ClientInit: never evict an existing viewer.
        header = receive(24)
        actual_width, actual_height = struct.unpack("!HH", header[:4])
        name_size = struct.unpack("!I", header[20:24])[0]
        if name_size > 4096:
            raise ValueError("RFB desktop name exceeds readiness bound")
        receive(name_size)
        if (actual_width, actual_height) != (width, height):
            raise ValueError("RFB framebuffer does not match virtual desktop")
        return f"RFB ready: 3.8 security=none framebuffer={width}x{height}"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("port", type=int)
    parser.add_argument("width", type=int)
    parser.add_argument("height", type=int)
    parser.add_argument("--password", action="store_true")
    args = parser.parse_args()
    if not 1 <= args.port <= 65535 or args.width < 1 or args.height < 1:
        parser.error("expected valid port and positive framebuffer dimensions")
    try:
        print(probe(args.port, args.width, args.height, args.password), flush=True)
    except (OSError, ValueError) as error:
        print(f"RFB not ready: {error}", file=sys.stderr, flush=True)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
