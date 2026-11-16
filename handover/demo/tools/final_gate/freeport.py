import socket, sys
n = int(sys.argv[1]) if len(sys.argv) > 1 else 2; ss = []
for _ in range(n):
    s = socket.socket(); s.bind(("127.0.0.1", 0)); ss.append(s)
print(" ".join(str(s.getsockname()[1]) for s in ss))
