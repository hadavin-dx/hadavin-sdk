import logging, threading, http.client, io
from hadavin_sdk.approvals.receiver import serve
buf = io.StringIO(); h = logging.StreamHandler(buf); h.setLevel(logging.DEBUG)
lg = logging.getLogger("hadavin_sdk.receiver"); lg.addHandler(h); lg.setLevel(logging.DEBUG)
srv = serve(None, port=0); t = threading.Thread(target=srv.serve_forever, daemon=True); t.start()
port = srv.server_address[1]
secret = "AKIA" + "IOSFODNN7EXAMPLE"
c = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
c.request("POST", "/slack/actions?t=" + secret, body=b"", headers={"Content-Length": "0"}); print("status", c.getresponse().status); c.close()
c = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
c.putrequest("POST", "/x"); c.putheader("Content-Length","0"); c.endheaders()  # control
print("status2", c.getresponse().status); c.close()
# malformed request line holding the key
import socket
s = socket.create_connection(("127.0.0.1", port), timeout=5); s.sendall(("GARBAGE " + secret + " HTTP/9\r\n\r\n").encode()); s.recv(1000); s.close()
srv.shutdown(); srv.server_close()
out = buf.getvalue(); print(out); print("KEY IN LOG:", secret in out, "count", out.count(secret))
