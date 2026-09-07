"""Exercise shutdown before Xvfb's first readiness poll can record endpoints."""
import json
import os
from pathlib import Path
import pty
import select
import signal
import sys
import tempfile
import time


with tempfile.TemporaryDirectory(prefix="ilastik-early-interrupt-", dir="/tmp") as name:
    root = Path(name)
    shim = root / "Xvfb"
    shim.write_text("""#!/opt/ilastik/bin/python
import json, os, signal, socket, sys, time
from pathlib import Path
root = Path(os.environ['ILASTIK_EARLY_TEST_ROOT'])
display = sys.argv[1][1:]
lock = Path('/tmp/.X' + display + '-lock')
endpoint = Path('/tmp/.X11-unix/X' + display)
time.sleep(0.25)
server = socket.socket(socket.AF_UNIX)
server.bind(str(endpoint))
lock.write_text(str(os.getpid()) + '\\n')
def stop(signum, frame):
    lock.unlink()
    # Simulate a server that cleans its lock but leaves its socket on early exit.
    sys.exit(0)
signal.signal(signal.SIGTERM, stop)
(root / 'child.json').write_text(json.dumps({'pid': os.getpid(), 'start': Path('/proc/self/stat').read_text().split()[21]}))
while True:
    signal.pause()
""")
    shim.chmod(0o700)
    for index, requested in enumerate((signal.SIGINT, signal.SIGTERM)):
        display = 25 + index
        endpoint = Path(f"/tmp/.X11-unix/X{display}")
        lock = Path(f"/tmp/.X{display}-lock")
        assert not endpoint.exists() and not lock.exists()
        env = dict(os.environ, PATH=str(root) + ':' + os.environ['PATH'],
                   ILASTIK_EARLY_TEST_ROOT=str(root))
        pid, fd = pty.fork()
        if pid == 0:
            args = ['ilastik-gui', '--display', ':' + str(display), '--geometry', '1000x720',
                    '--port', str(5825 + index), '--vnc-port', str(5925 + index)]
            os.execvpe(args[0], args, env)
        started = time.monotonic()
        sent = None
        status = None
        output = bytearray()
        try:
            while time.monotonic() - started < 18:
                if select.select([fd], [], [], 0.01)[0]:
                    try:
                        output.extend(os.read(fd, 65536))
                    except OSError:
                        pass
                if sent is None and b'Internal session logs:' in output and (root / 'child.json').exists():
                    assert b'is ready.' not in output
                    if requested == signal.SIGINT:
                        os.write(fd, b'\x03')
                    else:
                        os.killpg(pid, signal.SIGTERM)
                    sent = time.monotonic()
                done, raw = os.waitpid(pid, os.WNOHANG)
                if done:
                    status = os.waitstatus_to_exitcode(raw)
                    break
            assert status == (130 if requested == signal.SIGINT else 143), (status, output.decode(errors='replace'))
            assert sent is not None and time.monotonic() - sent < 10
            assert b'Stopping ilastik GUI (' in output and b'is ready.' not in output
            assert not endpoint.exists() and not lock.exists(), ('stale display endpoint', display)
            child_record = root / 'child.json'
            if child_record.exists():
                child = json.loads(child_record.read_text())
                proc = Path('/proc') / str(child['pid']) / 'stat'
                assert not proc.exists() or proc.read_text().split()[21] != child['start']
                child_record.unlink()
            print('PASS early real PTY signal', requested.name, 'status', status, 'no display endpoints')
        finally:
            if status is None:
                os.killpg(pid, signal.SIGTERM)
                os.waitpid(pid, 0)
            os.close(fd)
