import os, pty, sys, select, time
ans = sys.argv[1].encode()  # only ever "n" or empty
argv = sys.argv[2:]
pid, fd = pty.fork()
if pid == 0:
    os.execvp(argv[0], argv)
out = b""; sent = False; end = time.time() + 60
while time.time() < end:
    r, _, _ = select.select([fd], [], [], 1)
    if r:
        try: d = os.read(fd, 4096)
        except OSError: break
        if not d: break
        out += d
        if b"anything else stops: " in out and not sent:
            os.write(fd, ans + b"\n"); sent = True
_, st = os.waitpid(pid, 0)
print(out.decode(errors="replace").replace("\r", "")); print("answer sent:", repr(ans), "| exit:", os.waitstatus_to_exitcode(st))
