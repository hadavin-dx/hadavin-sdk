import fcntl, socket, struct, sys, os
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
ifr = struct.pack("16sH14s", b"lo", 0, b"")
cur = struct.unpack("16sH14s", fcntl.ioctl(s, 0x8913, ifr))[1]
fcntl.ioctl(s, 0x8914, struct.pack("16sH14s", b"lo", cur | 1 | 0x40, b""))
os.execvp(sys.argv[1], sys.argv[1:])
