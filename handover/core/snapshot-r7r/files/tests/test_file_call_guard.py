"""Class: a script or library that reads, writes, lists, copies, opens or starts something by a path or a name given
by a person must go through `lead_desk.regfile` (a regular file or one fixed refusal; never a wait on a pipe, never a
read without a limit). This file is the guard that keeps a NEW call from slipping past that rule.

What the guard does (over src/lead_desk, load_tools, demo_only, scripts and tools; read from the code, nothing runs):
1. IMPORTS are deny-by-default: a module that can open or start things (sqlite3, subprocess, shutil, fileinput, zipfile,
   tarfile, glob, importlib, tempfile) may be imported by a file only when ALLOWED_IMPORTS names that file and module
   with a written reason.
2. CALLS AND REFERENCES: every name a file can use to reach the file system, a process or a socket is looked up after
   the import aliases are resolved (`from io import open as _o` is `io.open`; `import sqlite3 as db` is `sqlite3`). A
   call on an object whose type is not known (`Path(x).read_text()`) is matched by its method name. A hit is allowed
   only when ALLOWED_CALLS names the file and the exact text of the call with a reason.
3. REACHING A NAME WITHOUT WRITING IT: `getattr(os, "open")`, `os.__dict__`, `vars(os)`, `__builtins__`, `__import__`,
   `importlib.import_module`, `eval`, `exec` and `compile` are hits.
4. A listed reason that no longer matches any code is itself a failure (the table cannot go stale).

What it does NOT do (so that the claim is exact): it is a static reading of the text. It cannot see a name built from
pieces at run time and handed to `getattr` on an object it does not know, a call made by code outside the five folders
(the tests, the standard library), or a method name that is not in the lists below on an object of unknown type
(`obj.some_new_name(path)`). The method names that are matched on ANY object are in METHOD_NAMES; `.replace(` and
`.rename(` are matched only with exactly one argument (the form of `Path.replace` and `Path.rename`; `str.replace` takes
two); `.read()` and `.readlines()` with NO size are matched on any object (a read that waits for the end of the
stream), a read with a size is not. Standard input (`sys.stdin...`), `input()` and `breakpoint()` are hits. The planted
tree test below proves that every shape of the lists is caught: 17 shapes were added in round 7, plus the bare read.

The lists are CLOSED: they name the readers, loaders, sockets, servers and clients that exist today (parsers that take a
path, archive openers, `urlopen`, log file handlers, code loaders, `socket`, the standard servers and clients for HTTP,
SMTP, IMAP, POP, FTP). A new library that opens a path or a port under a name that is in no list is NOT seen; adding
the name to the list (and a planted case) is the fix. The guard also cannot see `server.serve_forever` handed on as a
value (only the call is matched), a name built from pieces on an object of unknown type, or code outside the five
folders. Every entry in ALLOWED_CALLS must say which port, host or file the use reaches."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]

GUARDED_FOLDERS = ("src/lead_desk", "load_tools", "demo_only", "scripts", "tools")

# -- what is matched -------------------------------------------------------------------------------------------------

# modules whose import needs a written reason (deny by default)
DENIED_MODULES = {
    "sqlite3",
    "subprocess",
    "shutil",
    "fileinput",
    "zipfile",
    "tarfile",
    "glob",
    "importlib",
    "tempfile",
}
# names of the form module.name that are hits (after alias resolution): the whole module, or the listed names
HIT_QUALIFIED = {
    "builtins.open",
    "builtins.exec",
    "builtins.eval",
    "builtins.compile",
    "urllib.request.FileHandler",
    "concurrent.futures.ProcessPoolExecutor",
    "multiprocessing.Process",
    "multiprocessing.Pool",
    "io.open",
    "io.FileIO",
    "io.open_code",
    "os.open",
    "os.fdopen",
    "os.system",
    "os.popen",
    "os.listdir",
    "os.scandir",
    "os.walk",
    "os.fwalk",
    "os.replace",
    "os.rename",
    "os.renames",
    "os.remove",
    "os.unlink",
    "os.rmdir",
    "os.removedirs",
    "os.mkdir",
    "os.makedirs",
    "os.truncate",
    "os.symlink",
    "os.link",
    "os.chmod",
    "os.chown",
    "os.startfile",
    "os.posix_spawn",
    "os.posix_spawnp",
    "os.fork",
    "os.forkpty",
    "os.mkfifo",
    "os.mknod",
    "os.utime",
    "os.dup2",
    "ssl.create_default_context",
    "importlib.import_module",
    "importlib.util.spec_from_file_location",
    "runpy.run_path",
    "runpy.run_module",
    "pickle.load",
    "pickle.loads",
    "marshal.load",
    "shelve.open",
    "socket.create_connection",
    "socket.create_server",
    "multiprocessing.Process",
    "ctypes.CDLL",
    "ctypes.cdll",
}
# more readers (R4-08): parsers and archives that take a path, loaders of code, and every way to listen, connect or
# send (a socket is a place a script can reach as surely as a file). The lists are CLOSED: a name that is not here
# is not seen (see the docstring).
HIT_QUALIFIED |= {
    "xml.etree.ElementTree.parse",
    "xml.etree.ElementTree.iterparse",
    "xml.dom.minidom.parse",
    "xml.dom.pulldom.parse",
    "xml.sax.parse",
    "configparser.ConfigParser",
    "configparser.RawConfigParser",
    "argparse.FileType",
    "gzip.GzipFile",
    "gzip.open",
    "bz2.BZ2File",
    "bz2.open",
    "lzma.LZMAFile",
    "lzma.open",
    "urllib.request.urlopen",
    "urllib.request.urlretrieve",
    "logging.FileHandler",
    "logging.handlers.RotatingFileHandler",
    "logging.handlers.TimedRotatingFileHandler",
    "logging.handlers.WatchedFileHandler",
    "linecache.getlines",
    "linecache.getline",
    "linecache.updatecache",
    "ctypes.LoadLibrary",
    "ctypes.PyDLL",
    "ctypes.WinDLL",
    "zipimport.zipimporter",
    "pickle.Unpickler",
    "operator.methodcaller",
    "socket.socket",
    "socket.socketpair",
    "socket.fromfd",
    "socketserver.TCPServer",
    "socketserver.ThreadingTCPServer",
    "socketserver.UDPServer",
    "socketserver.ThreadingUDPServer",
    "socketserver.UnixStreamServer",
    "http.server.HTTPServer",
    "http.server.ThreadingHTTPServer",
    "http.client.HTTPConnection",
    "http.client.HTTPSConnection",
    "smtplib.SMTP",
    "smtplib.SMTP_SSL",
    "smtplib.LMTP",
    "imaplib.IMAP4",
    "imaplib.IMAP4_SSL",
    "poplib.POP3",
    "poplib.POP3_SSL",
    "ftplib.FTP",
    "ftplib.FTP_TLS",
    "telnetlib.Telnet",
    "asyncio.start_server",
    "asyncio.open_connection",
    "asyncio.start_unix_server",
    "asyncio.open_unix_connection",
}
# R7: names that read standard input (a wait on a person or a pipe), stop or signal a process, look at a path without a
# regular-file check, fetch from the network, or start a debugger or an interactive prompt
HIT_QUALIFIED |= {
    "os.read",
    "os.kill",
    "os.killpg",
    "os.sendfile",
    "os.stat",
    "os.lstat",
    "os.path.getsize",
    "os.path.getmtime",
    "os.path.getatime",
    "os.path.getctime",
    "os.path.exists",
    "os.path.isfile",
    "os.path.isdir",
    "signal.pause",
    "signal.sigwait",
    "pdb.set_trace",
    "pdb.post_mortem",
    "pdb.run",
    "code.interact",
    "ssl.get_server_certificate",
    "xmlrpc.client.ServerProxy",
    "requests.get",
    "requests.post",
    "requests.put",
    "requests.patch",
    "requests.delete",
    "requests.head",
    "requests.request",
    "requests.Session",
    "httpx.get",
    "httpx.post",
    "httpx.Client",
    "select.select",
    "select.poll",
    # round 7B (review part 2, M3): name lookups that wait on a resolver, sockets made by name, a TLS context by name
    "socket.getaddrinfo",
    "socket.gethostbyname",
    "socket.gethostbyname_ex",
    "socket.gethostbyaddr",
    "socket.getnameinfo",
    "socket.getfqdn",
    "socket.create_connection",
    "socket.create_server",
    "socket.fromfd",
    "socket.socketpair",
    "ssl.wrap_socket",
    "multiprocessing.pool.Pool",
    "multiprocessing.pool.ThreadPool",
    "multiprocessing.dummy.Pool",
}
# names that are hits except as a TYPE in a signature or a declaration (ssl.SSLContext as a type is no use of it)
CALL_ONLY_QUALIFIED = {"ssl.SSLContext"}
# any name of these modules is a hit
HIT_MODULES = {"subprocess", "shutil", "fileinput", "zipfile", "tarfile", "glob", "sqlite3", "mmap", "pty", "runpy"}
HIT_PREFIXES = {
    "os": ("exec", "spawn"),  # os.execv, os.execl, os.spawnl, os.spawnvp ...
    "ctypes": ("windll", "oledll", "cdll", "pydll", "CDLL", "WinDLL", "OleDLL", "PyDLL"),  # load a library by path
    "asyncio": ("create_subprocess_", "start_unix_server", "open_unix_connection"),
    "logging": ("handlers.", "config.fileConfig"),  # every file handler; the file-based configuration
    "sys": (
        "stdin",
    ),  # sys.stdin.read / readline / buffer / iteration / sys.stdin itself: a wait on a person or a pipe
}
# method names that are hits on an object of ANY kind (the type of the object is not known to a reader of the text)
METHOD_NAMES = {
    "read_text",
    "read_bytes",
    "write_text",
    "write_bytes",
    "open",  # builtin open(), io.open(), os.open(), Path.open(), opener.open(), tarfile.open(), gzip.open() ...
    "fdopen",
    "load",  # json.load(file), pickle.load
    "system",
    "popen",
    "touch",
    "iterdir",
    "glob",
    "rglob",
    "scandir",
    "listdir",
    "walk",
    "unlink",
    "rmdir",
    "mkdir",
    "symlink_to",
    "hardlink_to",
    "chmod",
    "readlink",
    "samefile",
    "load_verify_locations",
    "load_cert_chain",
    "load_default_certs",
    "set_default_verify_paths",
    "load_dh_params",
    "create_default_context",
    "ZipFile",
    "TarFile",
    "FileInput",
    "Popen",
    "getlines",
    "LoadLibrary",
    "check_output",
    "check_call",
    "copyfile",
    "copy2",
    "copytree",
    "chdir",
    "fileConfig",
    "subprocess_exec",
    "subprocess_shell",
    "__getattribute__",
    # round 7B (M3): a pool of processes or threads made from a context, and the event loop's own socket calls
    "Pool",
    "ThreadPool",
    "sock_connect",
    "sock_recv",
    "sock_recv_into",
    "sock_sendall",
    "sock_accept",
    "getaddrinfo",
    "getnameinfo",
    "gethostbyname",
    "gethostbyname_ex",
    "gethostbyaddr",
    "create_connection",
    "create_server",
    "create_datagram_endpoint",
    "create_unix_connection",
    "create_unix_server",
    "connect_read_pipe",
    "connect_write_pipe",
    "add_reader",
    "add_writer",
    "wrap_socket",
}
CALL_ONLY_METHODS = {
    "bind",
    "listen",
    "connect_ex",
    "serve_forever",
    "start_server",
    "SSLContext",
}  # `config.bind` is a setting
ZERO_ARGUMENT_METHODS = {"read", "readlines"}  # a read with no size: `r.read()` waits for the end of the stream
ONE_ARGUMENT_METHODS = {"replace", "rename"}  # Path.replace(target); str.replace(old, new) has two
BARE_NAMES = {
    "open",
    "eval",
    "exec",
    "compile",
    "__import__",
    "__builtins__",
    "input",
    "breakpoint",
}  # also when only referred to
PATH_CLASSES = {"pathlib.Path", "pathlib.PurePath", "pathlib.PosixPath", "pathlib.WindowsPath"}
REACH_FUNCTIONS = {"getattr", "vars", "globals", "locals", "setattr", "delattr"}
REACH_MODULES = {"os", "builtins", "io", "sys", "shutil", "subprocess", "sqlite3", "importlib", "pathlib", "ssl"}
TLS_LOADER_NAMES = {"load_verify_locations", "load_cert_chain", "load_default_certs"}
TLS_PATH_KEYWORDS = {"cafile", "capath"}
LOG_FILE_CALLS = {"basicConfig"}  # logging.basicConfig(filename=...) opens a file
TLS_LOADER_FILES = {"demo_only/fake_imap.py", "demo_only/fake_smtp_tls.py"}

# -- what is allowed, and why ----------------------------------------------------------------------------------------

ALLOWED_IMPORTS = {
    ("src/lead_desk/trace.py", "sqlite3"): "the desk's own database file, opened by the desk, not a person's path",
    ("src/lead_desk/desk.py", "sqlite3"): "the desk's own database; the path was checked by book_problem first",
    ("src/lead_desk/portal_api.py", "sqlite3"): "reads the desk's own database through the desk's connection",
    ("src/lead_desk/hooks.py", "sqlite3"): "the crash hook reads the desk's own database",
    ("src/lead_desk/db.py", "sqlite3"): "the one module that opens the desk's database",
    ("src/lead_desk/db.py", "importlib"): "importlib.resources: the package's own schema.sql",
    ("src/lead_desk/loader.py", "importlib"): "imports the code of the named adapter kind from a fixed list",
    ("load_tools/check_invariants.py", "sqlite3"): "reads the book read-only after tools.pathconfine confined it",
    ("scripts/check_schema.py", "sqlite3"): "builds a throw-away database in a temp folder to test schema.sql",
    ("scripts/check_schema.py", "tempfile"): "makes that throw-away folder",
    ("scripts/run_real_check.py", "tempfile"): "a private temp folder for the self-test",
    ("scripts/run_real_check.py", "shutil"): "removes that private temp folder and finds the openssl program",
    ("scripts/run_real_check.py", "subprocess"): "starts the desk child of the self-test with a fixed command line",
    ("demo_only/fake_smtp_tls.py", "shutil"): "finds the openssl program for the made-up certificate",
    (
        "demo_only/fake_smtp_tls.py",
        "subprocess",
    ): "runs openssl with a fixed command line to make a made-up certificate",
    ("demo_only/portal_demo.py", "tempfile"): "a temp file of this process for the demo's own data",
    ("tools/hygiene.py", "subprocess"): "runs `git ls-files` (fixed command line) in the repository",
    ("tools/pathconfine.py", "tempfile"): "tempfile.gettempdir(): the name of the temp folder, nothing is opened",
}
OPENER = "an HTTP request, not a file"
ALLOWED_CALLS = {
    ("src/lead_desk/desk.py", "os.stat"): "looks at the type of the book path only (a pipe is refused); opens nothing",
    ("src/lead_desk/lockfile.py", "os.stat"): "compares the lock file's identity with the open one; opens nothing",
    (
        "src/lead_desk/live_claude.py",
        "f.read",
    ): "the last window of a regular file that was opened by regfile; the window is bounded",
    (
        "src/lead_desk/imap_count.py",
        "super().open",
    ): "the imaplib base class opens the socket to the IMAP host in the setting; the file is then a deadline reader",
    (
        "src/lead_desk/imap_count.py",
        "self.ssl_context.wrap_socket",
    ): "wraps that one connection in TLS (chain and host name checked) under the total-deadline timer; reads no file",
    ("src/lead_desk/server.py", "select.select"): "waits on the server's own accepted sockets for a short, fixed time",
    (
        "src/lead_desk/server.py",
        "select.poll",
    ): "the same wait on the server's own accepted sockets, for a file number that select cannot take",
    (
        "scripts/run_live_check.py",
        "sys.stdin.fileno",
    ): "asks whether standard input is closed or the empty device; reads nothing",
    (
        "scripts/run_live_check.py",
        "os.stat",
    ): "the identity of the empty device, compared with standard input; reads nothing",
    ("scripts/run_live_check.py", "input"): "the one yes/no question; closed input counts as no, never as yes",
    (
        "scripts/run_real_check.py",
        "os.stat",
    ): "type of the result file path (a pipe or device is refused); opens nothing",
    ("scripts/run_real_check.py", "os.path.isdir"): "type of the result file path (a folder is refused); opens nothing",
    ("scripts/run_real_check.py", "input"): "the one yes/no question; closed input counts as no, never as yes",
    ("src/lead_desk/regfile.py", "os.open"): "the one place that opens a file (both functions)",
    (
        "src/lead_desk/regfile.py",
        "os.stat",
    ): "type of an output path before a replace (a pipe, device or folder is refused); opens nothing",
    ("src/lead_desk/regfile.py", "os.fdopen"): "wraps the descriptor the line above checked",
    ("src/lead_desk/adapters.py", "_OPENER.open"): OPENER,
    ("src/lead_desk/crm_hubspot.py", "_OPENER.open"): OPENER,
    ("src/lead_desk/live_claude.py", "_OPENER.open"): OPENER,
    ("scripts/hubspot_probe.py", "_OPENER.open"): OPENER,
    ("demo_only/portal_demo.py", "_OPENER.open"): OPENER,
    (
        "scripts/http_guard.py",
        "http_only_opener(follow_redirects, use_proxy).open",
    ): "an HTTP request (http and https handlers only)",
    ("src/lead_desk/db.py", "importlib.resources.files('lead_desk').joinpath('schema.sql').read_text"): "package data",
    ("scripts/check_schema.py", "SCHEMA.read_text"): "the repository's own schema.sql",
    ("tools/hygiene.py", "path.read_text"): "term lists passed by the repository's own tests and CI",
    ("tools/hygiene.py", "(repo / f).read_text"): "tracked files found by `git ls-files`",
    ("demo_only/portal_demo.py", "os.fdopen"): "the descriptor of a temporary file this process just made (mkstemp)",
    ("src/lead_desk/tls_trust.py", "ssl.create_default_context"): "the ONE reader of a trusted-certificate file",
    ("demo_only/fake_imap.py", "ctx.load_cert_chain"): "the fake server's own certificate, made at test time",
    ("demo_only/fake_smtp_tls.py", "self._ctx.load_cert_chain"): "the fake server's own certificate, made at test time",
    (
        "src/lead_desk/regfile.py",
        "getattr(os, ...)",
    ): "reads the open-flag constants this platform has (O_BINARY is Windows only)",
    (
        "src/lead_desk/db.py",
        "sqlite3.connect",
    ): "the desk's database; the path went through book_problem and the lock first",
    ("src/lead_desk/portal_api.py", "sqlite3.connect"): "the desk's own database, read-only, by the desk's own path",
    (
        "src/lead_desk/portal_api.py",
        "root.rglob",
    ): "lists the portal's own static folder; links and non-files are skipped",
    (
        "src/lead_desk/desk.py",
        "Path(db_path).parent.mkdir",
    ): "makes the folder of the book AFTER book_problem accepted the path",
    ("src/lead_desk/hooks.py", "self.flag_path.unlink"): "removes the desk's own crash flag file",
    ("src/lead_desk/trace.py", "self.flag_path.unlink"): "removes the desk's own crash flag file",
    (
        "src/lead_desk/live_claude.py",
        "self.path.parent.mkdir",
    ): "folder of the live-call ledger, which then opens through open_output",
    (
        "src/lead_desk/loader.py",
        "importlib.import_module",
    ): "imports adapter kinds from the fixed list of kind names, never a typed name",
    (
        "src/lead_desk/run_stats.py",
        "os.replace",
    ): "swaps the desk's own statistics file in; the temp file was made by open_output",
    ("src/lead_desk/server.py", "self._slot.touch"): "the desk's own slot file name, not a typed path",
    (
        "src/lead_desk/netconnect.py",
        "socket.getaddrinfo",
    ): "looks up the host name of a mail host in the setting, in a helper thread that is waited for with a time limit",
    (
        "src/lead_desk/netconnect.py",
        "socket.socket",
    ): "makes the one socket that connects to an address of that host, with the time that is left as its time-out",
    (
        "load_tools/check_invariants.py",
        "sqlite3.connect",
    ): "opens the book read-only through readonly_sqlite_uri after confinement",
    ("load_tools/load_driver.py", "p.unlink"): "removes the part files this run just wrote and read",
    (
        "demo_only/fake_smtp_tls.py",
        "shutil.which",
    ): "looks up the openssl program on the search path; nothing is opened",
    (
        "demo_only/fake_smtp_tls.py",
        "subprocess.run",
    ): "runs openssl with a fixed command line to make a made-up certificate",
    ("demo_only/fake_smtp_tls.py", "socket.create_connection"): "the fake server's own port on this computer",
    (
        "src/lead_desk/smtp_provider.py",
        "ctx.wrap_socket",
    ): "starts TLS on the connection the sender already opened itself",
    (
        "load_tools/load_driver.py",
        "ctx.Pool",
    ): "the driver's own pool of worker processes (a fixed count, made-up requests)",
    ("demo_only/fake_imap.py", "ssl.SSLContext"): "the made-up mail server's own TLS context on this computer",
    ("demo_only/fake_imap.py", "self._ctx.wrap_socket"): "starts TLS on a connection the made-up server accepted",
    ("demo_only/fake_smtp_tls.py", "ssl.SSLContext"): "the made-up mail server's own TLS context on this computer",
    ("demo_only/fake_smtp_tls.py", "self._ctx.wrap_socket"): "starts TLS on a connection the made-up server accepted",
    ("demo_only/portal_demo.py", "os.replace"): "swaps the demo's own data file in",
    ("demo_only/portal_demo.py", "folder.glob"): "lists the demo's own temp folder",
    ("demo_only/portal_demo.py", "hooks.flag_path.unlink"): "removes the demo desk's own crash flag file",
    ("demo_only/portal_demo.py", "Path(name).unlink"): "removes the demo's own temp file",
    ("demo_only/portal_demo.py", "f.unlink"): "removes the demo's own temp file",
    ("scripts/check_schema.py", "sqlite3.connect"): "a throw-away database in a temp folder",
    ("scripts/reset_check.py", "socket.create_connection"): "tests whether the desk port on this computer answers",
    (
        "demo_only/burst.py",
        "socket.create_connection",
    ): "tests whether the address given with --url answers, before the burst starts",
    ("scripts/run_real_check.py", "shutil.rmtree"): "removes the self-test's own private temp folder",
    ("scripts/run_real_check.py", "self._private.mkdir"): "makes that private temp folder",
    ("scripts/run_real_check.py", "run_dir.glob"): "lists the self-test's own run folder",
    ("scripts/run_real_check.py", "run_dir.mkdir"): "makes the self-test's own run folder",
    ("scripts/run_real_check.py", "subprocess.Popen"): "starts the desk child with a fixed command line (no shell)",
    ("scripts/run_real_check.py", "flag.unlink"): "removes the self-test's own crash flag file",
    ("tools/hygiene.py", "subprocess.run"): "runs `git ls-files` with a fixed command line",
    (
        "tools/pathconfine.py",
        "os.scandir",
    ): "lists a folder ON the confined path to match one part, with errors turned into a refusal",
    # -- ports: every place the code listens, connects or sends (R4-08). Each reason says WHICH port or host. --------
    (
        "src/lead_desk/server.py",
        "ThreadingHTTPServer",
    ): "the desk's own web server, bound to DESK_BIND (loopback by default)",
    (
        "src/lead_desk/server.py",
        "socketserver.TCPServer",
    ): "base class of the desk's own listener (Windows exclusive bind)",
    ("src/lead_desk/server.py", "server.serve_forever"): "serves the desk's own port in the main thread",
    ("src/lead_desk/server.py", "socket.socket"): "a type name in annotations: sockets the desk's server was handed",
    (
        "src/lead_desk/smtp_outbox.py",
        "socket.socket",
    ): "connects to the mail host (an IP address) named in SmtpSettings",
    ("src/lead_desk/smtp_provider.py", "socket.socket"): "a type name in annotations; the connect is create_connection",
    (
        "src/lead_desk/imap_count.py",
        "imaplib.IMAP4_SSL",
    ): "reads only a count from the IMAP host in the setting, over TLS",
    ("load_tools/catcher.py", "asyncio.start_server"): "the catcher's own listener; --host must be a loopback address",
    ("load_tools/catcher.py", "server.serve_forever"): "serves that same loopback listener",
    (
        "demo_only/bad_request.py",
        "ThreadingHTTPServer",
    ): "the base class of QuietServer, which every fake extends; each fake's factory refuses a non-loopback host",
    ("demo_only/fake_imap.py", "socket.socket"): "the fake IMAP server's own socket (listener and type names)",
    ("demo_only/fake_imap.py", "self._srv.bind"): "binds the fake IMAP server to a loopback address",
    ("demo_only/fake_imap.py", "self._srv.listen"): "listens on that loopback socket",
    (
        "demo_only/fake_model_server.py",
        "ThreadingHTTPServer",
    ): "the fake model server; the factory refuses a non-loopback host",
    ("demo_only/fake_model_server.py", "srv.serve_forever"): "serves that loopback fake model server",
    ("demo_only/fake_smtp_tls.py", "socket.socket"): "the fake SMTP-over-TLS server's own sockets",
    ("demo_only/fake_smtp_tls.py", "self._srv.bind"): "binds the fake mail server to a loopback address",
    ("demo_only/fake_smtp_tls.py", "self._srv.listen"): "listens on that loopback socket",
    ("demo_only/fakes_server.py", "srv.serve_forever"): "serves that loopback fakes server",
    ("scripts/run_real_check.py", "socket.socket"): "asks the system for a free loopback port",
    ("scripts/run_real_check.py", "s.bind"): "binds 127.0.0.1 port 0 only to learn a free port",
}


# -- the guard -------------------------------------------------------------------------------------------------------


def _aliases(tree: ast.AST) -> tuple[dict[str, str], list[tuple[int, str]]]:
    """(local name -> the dotted name it stands for, [(line, imported top module)]). `import a.b as c` gives
    c -> a.b; `import a.b` gives a -> a; `from a import b as c` gives c -> a.b; `from . import x` is relative and
    stands for nothing known."""
    names: dict[str, str] = {}
    imports: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                imports.append((node.lineno, a.name.split(".")[0]))
                if a.asname:
                    names[a.asname] = a.name
                else:
                    names[a.name.split(".")[0]] = a.name.split(".")[0]
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            imports.append((node.lineno, node.module.split(".")[0]))
            for a in node.names:
                names[a.asname or a.name] = f"{node.module}.{a.name}"
    return names, imports


def _chain(node: ast.AST) -> list[str] | None:
    """`a.b.c` as ['a', 'b', 'c'] when it starts with a plain name, else None."""
    parts: list[str] = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
        return parts[::-1]
    return None


def _qualified(node: ast.AST, names: dict[str, str]) -> str | None:
    """The dotted name `node` stands for after the import aliases are resolved, or None for anything else."""
    chain = _chain(node)
    if not chain or chain[0] not in names:
        return None
    return ".".join([names[chain[0]], *chain[1:]])


def _is_hit_name(qual: str, called: bool, in_annotation: bool = False) -> bool:
    """A listed name is a hit; any name of a HIT_MODULES module is a hit when it is called or is a function (lower-case
    last part, `run=subprocess.run`), so that `except sqlite3.Error` or `subprocess.PIPE` is not."""
    top, last = qual.split(".")[0], qual.rsplit(".", 1)[-1]
    return (
        qual in HIT_QUALIFIED
        or (qual in CALL_ONLY_QUALIFIED and (called or not in_annotation))
        or (top in HIT_MODULES and "." in qual and (called or last[:1].islower()))
        or any(qual.startswith(f"{mod}.{p}") for mod, prefixes in HIT_PREFIXES.items() for p in prefixes)
    )


def _file_hits(source: str) -> tuple[list[tuple[int, str]], list[tuple[int, str, str]]]:
    """(imports of a denied module: [(line, module)], hits: [(line, text of the name, why)]) for one file's text."""
    tree = ast.parse(source)
    names, imports = _aliases(tree)
    denied = [(line, mod) for line, mod in imports if mod in DENIED_MODULES]
    inner = {id(n.value) for n in ast.walk(tree) if isinstance(n, ast.Attribute)}  # a.b in a.b.c: judged inside a.b.c
    calls = {id(n.func): n for n in ast.walk(tree) if isinstance(n, ast.Call)}
    hits: list[tuple[int, str, str]] = []
    annotated: set[int] = set()  # names that are only a TYPE in a signature or a declaration are no use of the name
    for a in ast.walk(tree):
        roots = [a.annotation] if isinstance(a, (ast.arg, ast.AnnAssign)) else []
        roots += [a.returns] if isinstance(a, (ast.FunctionDef, ast.AsyncFunctionDef)) else []
        annotated |= {id(n) for r in roots if r is not None for n in ast.walk(r)}
    for node in ast.walk(tree):
        text = None
        if isinstance(node, ast.ImportFrom) and any(a.name == "*" for a in node.names):
            text, why = f"from {node.module or '.'} import *", "a star import hides every name it brings in"
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id in REACH_FUNCTIONS
            and not node.args
        ):
            text, why = f"{node.func.id}()", "gives every name of this module (the open built-in too) by text"
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            qual = names.get(node.id)
            if node.id in BARE_NAMES and node.id not in names:
                text, why = node.id, "a built-in that opens a file or runs code"
            elif qual is not None and _is_hit_name(qual, id(node) in calls, id(node) in annotated):
                text, why = node.id, f"stands for {qual}"
        elif isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Load):
            qual = _qualified(node, names)
            call = calls.get(id(node))
            if (
                id(node) not in inner
                and qual is not None
                and _is_hit_name(qual, call is not None, id(node) in annotated)
            ):
                text, why = ast.unparse(node), f"is {qual}"
            elif node.attr in METHOD_NAMES:
                text, why = ast.unparse(node), f"a `.{node.attr}` call on an object that may be a path or a file"
            elif node.attr in CALL_ONLY_METHODS and call is not None:
                text, why = ast.unparse(node), f"a `.{node.attr}(...)` call: it listens or serves on a port"
            elif node.attr in ONE_ARGUMENT_METHODS and call is not None and len(call.args) == 1 and not call.keywords:
                text, why = ast.unparse(node), f"`.{node.attr}(x)` with one argument (the form of Path.{node.attr})"
            elif node.attr in ZERO_ARGUMENT_METHODS and call is not None and not call.args and not call.keywords:
                text, why = ast.unparse(node), f"`.{node.attr}()` with no size: reads until the stream ends"
            elif (
                node.attr == "__dict__"
                and isinstance(node.value, ast.Name)
                and _root(node.value, names) in REACH_MODULES
            ):
                text, why = ast.unparse(node), "reaches the names of a module without writing them"
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id in REACH_FUNCTIONS
            and node.args
            and isinstance(node.args[0], ast.Call)
            and _qualified(node.args[0].func, names) in PATH_CLASSES
        ):
            text, why = f"{node.func.id}(Path(...), ...)", "reaches a method of a path by text"
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id in REACH_FUNCTIONS
            and node.args
        ):
            if (
                _root(node.args[0], names) in REACH_MODULES
                or isinstance(node.args[0], ast.Name)
                and node.args[0].id == "__builtins__"
            ):
                text, why = f"{node.func.id}({ast.unparse(node.args[0])}, ...)", "reaches a name of a module by text"
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id in {"getattr", "setattr", "delattr", "hasattr"}
            and len(node.args) >= 2
            and isinstance(node.args[1], ast.Constant)
            and isinstance(node.args[1].value, str)
            and (node.args[1].value in METHOD_NAMES or node.args[1].value in BARE_NAMES)
        ):
            text, why = ast.unparse(node), f"reaches `{node.args[1].value}` by a literal name (the same call, hidden)"
        if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name) and node.value.id == "__builtins__":
            text, why = ast.unparse(node), "reaches a built-in by text"
        if text is not None:
            hits.append((node.lineno, text, why))
    return denied, hits


def _root(node: ast.AST, names: dict[str, str]) -> str | None:
    """The top module that a plain name stands for (`import os as o`: o -> os), else None."""
    if isinstance(node, ast.Name) and node.id in names:
        return names[node.id].split(".")[0]
    return None


def _keyword_hits(source: str) -> list[tuple[int, str]]:
    """Calls given a certificate PATH (cafile= / capath=): the path would be opened by OpenSSL itself."""
    return [
        (n.lineno, k.arg)
        for n in ast.walk(ast.parse(source))
        if isinstance(n, ast.Call)
        for k in n.keywords
        if k.arg in TLS_PATH_KEYWORDS
    ] + [
        (n.lineno, "filename")
        for n in ast.walk(ast.parse(source))
        if isinstance(n, ast.Call) and (_chain(n.func) or [""])[-1] in LOG_FILE_CALLS
        for k in n.keywords
        if k.arg == "filename"
    ]


def _problems(
    repo: Path,
    allowed_imports: dict[tuple[str, str], str] = ALLOWED_IMPORTS,
    allowed_calls: dict[tuple[str, str], str] = ALLOWED_CALLS,
) -> list[str]:
    """What the guard finds in the tree `repo`: an import or a name that is not listed, a certificate path given to
    ssl, a TLS loader outside tls_trust.py and the demo fakes, a listed entry without a reason, and a listed entry that
    no longer matches any code."""
    bad: list[str] = []
    used_imports: set[tuple[str, str]] = set()
    used_calls: set[tuple[str, str]] = set()
    for folder in GUARDED_FOLDERS:
        for py in sorted((repo / folder).rglob("*.py")):
            rel = py.relative_to(repo).as_posix()
            source = py.read_text(encoding="utf-8")
            denied, hits = _file_hits(source)
            for line, mod in denied:
                if (rel, mod) in allowed_imports:
                    used_imports.add((rel, mod))
                else:
                    bad.append(f"{rel}:{line}: imports {mod}, which needs a written reason in ALLOWED_IMPORTS")
            for line, text, why in hits:
                if text.rsplit(".", 1)[-1] in TLS_LOADER_NAMES and rel not in TLS_LOADER_FILES:
                    bad.append(f"{rel}:{line}: {text} loads certificates outside tls_trust.py and the demo fakes")
                if (rel, text) in allowed_calls:
                    used_calls.add((rel, text))
                else:
                    bad.append(f"{rel}:{line}: {text} ({why}) is not listed in ALLOWED_CALLS")
            for line, keyword in _keyword_hits(source):
                bad.append(f"{rel}:{line}: a call is given a certificate PATH, {keyword}= (use lead_desk.tls_trust)")
    for table, used, label in ((allowed_imports, used_imports, "import"), (allowed_calls, used_calls, "call")):
        for (rel, what), reason in table.items():
            if not reason.strip():
                bad.append(f"{rel}: the allowed {label} {what} has no reason")
            if (rel, what) not in used:
                bad.append(f"{rel}: the allowed {label} {what} is not in the file any more (remove it from the table)")
    return bad


def test_every_import_and_file_call_in_the_code_is_listed_with_a_reason_or_goes_through_the_one_reader() -> None:
    """Pinned over every folder of code and every shape of the lists above. A hit that is not in a table fails."""
    assert not _problems(REPO)


# -- the guard itself is tested: each shape is planted alone and must be found ---------------------------------------

ALL_ADDRESSES = ".".join(["0"] * 4)  # built from parts: the address that listens on every interface

PLANTED = {
    "builtin open": "open('x')",
    "builtin open kept in a variable": "f = open\nf('x')",
    "io.open": "import io\nio.open('x')",
    "io.open under another name": "from io import open as _o\n_o('x')",
    "module under another name": "import io as _i\n_i.open('x')",
    "os.open": "import os\nos.open('x', 0)",
    "os.open handed on as a value": "import os\nrun(opener=os.open)",
    "os.fdopen": "import os\nos.fdopen(3)",
    "Path.read_text": "from pathlib import Path\nPath('x').read_text()",
    "Path.read_bytes": "from pathlib import Path\nPath('x').read_bytes()",
    "Path.write_text": "from pathlib import Path\nPath('x').write_text('')",
    "Path.write_bytes": "from pathlib import Path\nPath('x').write_bytes(b'')",
    "Path.open": "from pathlib import Path\nPath('x').open()",
    "Path.iterdir": "from pathlib import Path\nlist(Path('x').iterdir())",
    "Path.glob": "from pathlib import Path\nlist(Path('x').glob('*'))",
    "Path.rglob": "from pathlib import Path\nlist(Path('x').rglob('*'))",
    "Path.touch": "from pathlib import Path\nPath('x').touch()",
    "Path.replace": "from pathlib import Path\nPath('x').replace('y')",
    "Path.rename": "from pathlib import Path\nPath('x').rename('y')",
    "Path.unlink": "from pathlib import Path\nPath('x').unlink()",
    "json.load": "import json\njson.load(f)",
    "os.system": "import os\nos.system('x')",
    "os.popen": "import os\nos.popen('x')",
    "os.listdir": "import os\nos.listdir('x')",
    "os.scandir": "import os\nos.scandir('x')",
    "os.walk": "import os\nlist(os.walk('x'))",
    "os.replace": "import os\nos.replace('x', 'y')",
    "os.rename": "import os\nos.rename('x', 'y')",
    "os.remove": "import os\nos.remove('x')",
    "os.execv": "import os\nos.execv('x', ['x'])",
    "os.execvp": "import os\nos.execvp('x', ['x'])",
    "os.spawnl": "import os\nos.spawnl(0, 'x')",
    "os.spawnvp": "import os\nos.spawnvp(0, 'x', ['x'])",
    "os.posix_spawn": "import os\nos.posix_spawn('x', ['x'], {})",
    "from os import listdir": "from os import listdir\nlistdir('x')",
    "sqlite3.connect": "import sqlite3\nsqlite3.connect(argv)",
    "sqlite3.connect under another name": "import sqlite3 as db\ndb.connect(argv)",
    "from sqlite3 import connect": "from sqlite3 import connect\nconnect(argv)",
    "subprocess.run": "import subprocess\nsubprocess.run(['x'])",
    "subprocess.Popen": "import subprocess\nsubprocess.Popen(['x'])",
    "subprocess.call": "import subprocess\nsubprocess.call(['x'])",
    "subprocess.check_output": "import subprocess\nsubprocess.check_output(['x'])",
    "from subprocess import run": "from subprocess import run\nrun(['x'])",
    "shutil.copyfile": "import shutil\nshutil.copyfile('x', 'y')",
    "shutil.copy": "import shutil\nshutil.copy('x', 'y')",
    "shutil.copy2": "import shutil\nshutil.copy2('x', 'y')",
    "shutil.move": "import shutil\nshutil.move('x', 'y')",
    "shutil.rmtree": "import shutil\nshutil.rmtree('x')",
    "fileinput.input": "import fileinput\nfileinput.input(['x'])",
    "zipfile.ZipFile": "import zipfile\nzipfile.ZipFile('x')",
    "from zipfile import ZipFile": "from zipfile import ZipFile\nZipFile('x')",
    "tarfile.open": "import tarfile\ntarfile.open('x')",
    "glob.glob": "import glob\nglob.glob('x*')",
    "ssl set_default_verify_paths": "import ssl\nssl.create_default_context().set_default_verify_paths()",
    "ssl load_dh_params": "import ssl\nssl.SSLContext().load_dh_params('x')",
    "ssl load_verify_locations": "import ssl\nssl.SSLContext().load_verify_locations('x')",
    "ssl load_cert_chain": "import ssl\nssl.SSLContext().load_cert_chain('x')",
    "ssl load_default_certs": "import ssl\nssl.SSLContext().load_default_certs()",
    "ssl cafile path": "import ssl\nssl.create_default_context(cafile='x')",
    "getattr on os": "import os\ngetattr(os, 'op' + 'en')('x')",
    "getattr on builtins": "import builtins\ngetattr(builtins, 'open')('x')",
    "getattr on io": "import io\ngetattr(io, 'open')('x')",
    "getattr on os under another name": "import os as _o\ngetattr(_o, 'open')('x')",
    "os.__dict__": "import os\nos.__dict__['open']('x')",
    "vars(os)": "import os\nvars(os)['open']('x')",
    "__builtins__ lookup": "__builtins__['open']('x')",
    "__import__": "__import__('os').open('x', 0)",
    "importlib.import_module": "import importlib\nimportlib.import_module('os')",
    "eval": "eval('1')",
    "exec": "exec('1')",
    "compile": "compile('1', 'x', 'exec')",
    "runpy.run_path": "import runpy\nrunpy.run_path('x')",
    "xml parse": "import xml.etree.ElementTree as ET\nET.parse('x')",
    "minidom parse": "from xml.dom import minidom\nminidom.parse('x')",
    "ConfigParser.read": "import configparser\nconfigparser.ConfigParser().read('x')",
    "argparse.FileType": "import argparse\nargparse.FileType('r')",
    "gzip.GzipFile": "import gzip\ngzip.GzipFile('x')",
    "bz2.BZ2File": "import bz2\nbz2.BZ2File('x')",
    "lzma.open": "import lzma\nlzma.open('x')",
    "urlopen of a file address": "import urllib.request\nurllib.request.urlopen('file:///x')",
    "urlretrieve": "import urllib.request\nurllib.request.urlretrieve('http://example.test', 'y')",
    "logging.FileHandler": "import logging\nlogging.FileHandler('x')",
    "linecache.getlines": "import linecache\nlinecache.getlines('x')",
    "ctypes.LoadLibrary": "import ctypes\nctypes.cdll.LoadLibrary('x')",
    "zipimporter": "import zipimport\nzipimport.zipimporter('x')",
    "pickle.Unpickler": "import pickle\npickle.Unpickler(f)",
    "methodcaller": "import operator\noperator.methodcaller('read_text')(p)",
    "getattr on a Path": "from pathlib import Path\ngetattr(Path('x'), 'read_' + 'text')()",
    "socket.socket": "import socket\nsocket.socket()",
    "socket bind": "def f(s):\n    s.bind(('" + ALL_ADDRESSES + "', 1))",
    "socket listen": "def f(s):\n    s.listen()",
    "socket connect_ex": "def f(s):\n    s.connect_ex(('x', 1))",
    "HTTPServer": "from http.server import HTTPServer\nHTTPServer(('" + ALL_ADDRESSES + "', 1), None)",
    "ThreadingHTTPServer": "import http.server\nhttp.server.ThreadingHTTPServer(('', 1), None)",
    "TCPServer": "import socketserver\nsocketserver.TCPServer(('', 1), None)",
    "serve_forever": "def f(s):\n    s.serve_forever()",
    "asyncio.start_server": "import asyncio\nasyncio.start_server(h, '', 1)",
    "asyncio.open_connection": "import asyncio\nasyncio.open_connection('x', 1)",
    "HTTPConnection": "import http.client\nhttp.client.HTTPConnection('x')",
    "smtplib.SMTP": "import smtplib\nsmtplib.SMTP('x')",
    "imaplib.IMAP4_SSL": "import imaplib\nimaplib.IMAP4_SSL('x')",
    "ftplib.FTP": "import ftplib\nftplib.FTP('x')",
}


# Round 6: shapes written to get PAST the first guard: aliased imports (`import x as y`, `from x import y as z`),
# getattr / __import__ with a literal text, path readers on a Path made in another way, wrapped openers, star imports,
# a lookup of the module's own names, and modules the first lists did not name. Each must be found.
PLANTED_R6 = {
    "pathlib alias read_text": "from pathlib import Path as P\nP('x').read_text()",
    "pathlib module alias": "import pathlib as pl\npl.Path('x').read_bytes()",
    "pathlib home joinpath": "import pathlib\npathlib.Path.ho" + "me().joinpath('x').read_text()",
    "Path.read_text as unbound": "from pathlib import Path\nPath.read_text(p)",
    "Path subclass": "from pathlib import Path\nclass Q(Path):\n    pass\nQ('x').open()",
    "from os import open as o": "from os import open as o\no('x', 0)",
    "from os import fdopen as fd": "from os import fdopen as fd\nfd(3)",
    "import os as o popen": "import os as o\no.popen('x')",
    "from subprocess import Popen as P": "from subprocess import Popen as P\nP(['x'])",
    "import subprocess as sp": "import subprocess as sp\nsp.run(['x'])",
    "from shutil import copy as c": "from shutil import copy as c\nc('x', 'y')",
    "import builtins as b": "import builtins as b\nb.open('x')",
    "from builtins import open as o": "from builtins import open as o\no('x')",
    "importlib alias": "import importlib as il\nil.import_module('os')",
    "from importlib import import_module as im": "from importlib import import_module as im\nim('os')",
    "importlib.util spec": "import importlib.util as u\nu.spec_from_file_location('a', 'x')",
    "__import__ then method": "__import__('os').listdir('x')",
    "getattr of __import__": "getattr(__import__('os'), 'open')('x')",
    "getattr os popen kept": "import os\nf = getattr(os, 'popen')",
    "getattr os split name": "import os\nf = getattr(os, 'sys' + 'tem')",
    "io.FileIO": "import io\nio.FileIO('x')",
    "from io import FileIO as F": "from io import FileIO as F\nF('x')",
    "io.open_code": "import io\nio.open_code('x')",
    "os.makedirs": "import os\nos.makedirs('x')",
    "os.chdir": "import os\nos.chdir('x')",
    "os.symlink": "import os\nos.symlink('x', 'y')",
    "os.truncate": "import os\nos.truncate('x', 0)",
    "os.utime": "import os\nos.utime('x')",
    "os.mkfifo": "import os\nos.mkfifo('x')",
    "os.removedirs": "import os\nos.removedirs('x')",
    "os.startfile": "import os\nos.startfile('x')",
    "tempfile.mkstemp": "import tempfile\ntempfile.mkstemp()",
    "codecs.open": "import codecs\ncodecs.open('x')",
    "shelve.open": "import shelve\nshelve.open('x')",
    "mmap": "import mmap\nmmap.mmap(3, 0)",
    "pty.spawn": "import pty\npty.spawn(['x'])",
    "multiprocessing.Process": "import multiprocessing\nmultiprocessing.Process(target=f)",
    "ProcessPoolExecutor": "from concurrent.futures import ProcessPoolExecutor as E\nE()",
    "runpy.run_module": "import runpy\nrunpy.run_module('x')",
    "webbrowser.open": "import webbrowser\nwebbrowser.open('x')",
    "pickle.load": "import pickle as p\np.load(f)",
    "map os.remove": "import os\nlist(map(os.remove, ['x']))",
    "urlopen alias": "from urllib.request import urlopen as uo\nuo('file:///x')",
    "urllib.request.FileHandler": "import urllib.request as u\nu.FileHandler()",
    "socket.create_server": "import socket\nsocket.create_server(('', 1))",
    "socket.create_connection": "import socket as s\ns.create_connection(('x', 1))",
    "socket.fromfd": "import socket\nsocket.fromfd(3, 2, 1)",
    "http.server alias": "import http.server as hs\nhs.HTTPServer(('', 1), None)",
    "asyncio start_server alias": "from asyncio import start_server as ss\nss(h, '', 1)",
    "asyncio.create_subprocess_exec": "import asyncio\nasyncio.create_subprocess_exec('x')",
    "asyncio.create_subprocess_shell": "import asyncio as a\na.create_subprocess_shell('x')",
    "asyncio.start_unix_server": "import asyncio\nasyncio.start_unix_server(h, 'x')",
    "loop.subprocess_exec": "def f(loop):\n    loop.subprocess_exec(p, 'x')",
    "RotatingFileHandler": "import logging.handlers\nlogging.handlers.RotatingFileHandler('x')",
    "basicConfig filename": "import logging\nlogging.basicConfig(filename='x')",
    "logging.config.fileConfig": "import logging.config\nlogging.config.fileConfig('x')",
    "star import os": "from os import *\nlistdir('x')",
    "star import subprocess": "from subprocess import *\nrun(['x'])",
    "globals lookup": "globals()['open']('x')",
    "locals lookup": "locals()['open']('x')",
    "sys.modules lookup": "import sys\nsys.modules['os'].listdir('x')",
    "__getattribute__": "import os\nos.__getattribute__('open')('x')",
    "builtins __dict__": "import builtins\nbuiltins.__dict__['open']('x')",
    "ast.literal_eval of file": "import ast\nfrom pathlib import Path\nast.literal_eval(Path('x').read_text())",
    "functools.partial open": "import functools\np = functools.partial(open, 'x')",
    "opener function": "def opener(p):\n    return open(p)",
    "ctypes CDLL": "import ctypes\nctypes.CDLL('x')",
    "ctypes alias windll": "import ctypes as c\nc.windll.kernel32",
    "sqlite3 alias from": "from sqlite3 import connect as c2\nc2(argv)",
    "dbm.open": "import dbm\ndbm.open('x')",
    "gzip.open": "import gzip\ngzip.open('x')",
    "zipfile alias": "import zipfile as z\nz.ZipFile('x')",
    "tarfile alias": "from tarfile import open as to\nto('x')",
    "glob alias": "from glob import iglob as g\ng('x*')",
    "fileinput alias": "import fileinput as fi\nfi.FileInput('x')",
    "ssl cafile alias": "import ssl as s\ns.create_default_context(cafile='x')",
    "ssl load alias": "from ssl import SSLContext as C\nC().load_verify_locations('x')",
    "ssl load_verify_locations capath": (
        "import ssl\nctx = ssl.create_default_context()\nctx.load_verify_locations(capath='x')"
    ),
    "getattr importlib": "import importlib\ngetattr(importlib, 'import_module')('os')",
    "dunder import variable": "m = __import__\nm('os')",
    "dunder import literal alias": "name = '__import__'\ngetattr(__builtins__, name)('os')",
}
PLANTED.update(PLANTED_R6)

# Round 7: the 17 shapes the round-6 review found missing. Exactly this many are planted (docs/limits.md says so).
PLANTED_R7 = {
    "stdin read": "import sys\nsys.stdin.read()",
    "stdin readline": "import sys\nsys.stdin.readline()",
    "stdin buffer": "import sys\nsys.stdin.buffer.read(1)",
    "stdin iteration": "import sys\nfor line in sys.stdin: pass",
    "os.read": "import os\nos.read(0, 1)",
    "input": "input('x')",
    "breakpoint": "breakpoint()",
    "pdb.set_trace": "import pdb\npdb.set_trace()",
    "ssl.get_server_certificate": "import ssl\nssl.get_server_certificate(('h', 1))",
    "xmlrpc ServerProxy": "import xmlrpc.client\nxmlrpc.client.ServerProxy('u')",
    "requests.get": "import requests\nrequests.get('u')",
    "signal.pause": "import signal\nsignal.pause()",
    "os.kill": "import os\nos.kill(1, 9)",
    "code.interact": "import code\ncode.interact()",
    "os.sendfile": "import os\nos.sendfile(1, 2, 0, 1)",
    "os.stat": "import os\nos.stat('x')",
    "os.path.getsize": "import os\nos.path.getsize('x')",
}
BARE_READ_SHAPE = "import urllib.request as u\nr = u.build_opener().open('http://example.test')\nr.read()"
PLANTED.update(PLANTED_R7)
PLANTED["bare read on an http reply"] = BARE_READ_SHAPE


# CONTROL (r7e, new since frozen): passes on the frozen tree, pins behaviour that must stay; no mutant run.
def test_at_least_forty_round_six_shapes_are_planted_and_all_are_found(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    """The guard test must fail when a planted shape is not found (test above); this pins that the round-6 set exists,
    is large, and holds the named kinds. WHAT THE GUARD STILL CANNOT SEE: a name built at run time from data
    (`getattr(m, name)` where `name` comes from a file, an argument or arithmetic on one), a function or class
    reached through a value handed in from another module (`def f(opener): opener('x')`), code loaded from text at
    run time (any `exec`/`eval` is refused as a call, but not what a refused call is not asked about), and a call
    made through a third-party library that opens files itself. It reads the text of the code only."""
    assert len(PLANTED_R6) >= 40
    kinds = " ".join(PLANTED_R6)
    for word in ("alias", "getattr", "__import__", "star import", "pathlib", "opener", "globals"):
        assert word in kinds, word
    missed = []
    for shape, source in PLANTED_R6.items():
        root = _plant(tmp_path_factory.mktemp("r6"), source)
        if not [p for p in _problems(root, {}, {}) if p.startswith("scripts/planted.py")]:
            missed.append(shape)
    assert not missed, f"the guard did not find: {missed}"


# CONTROL (r7e, new since frozen): passes on the frozen tree, pins behaviour that must stay; no mutant run.
def test_the_seventeen_round_seven_shapes_and_the_bare_read_are_planted_and_found(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    """The exact count is 17 (plus the one bare `.read()` shape); the docs say 17. A bare `.read()` or `.readlines()`
    with no size is a hit on an object of ANY kind: it waits for the end of the stream. `.read(n)` with a size is
    not a hit by itself (the object it is called on is what the other lists judge)."""
    assert len(PLANTED_R7) == 17
    missed = []
    for shape, source in {**PLANTED_R7, "bare read": BARE_READ_SHAPE}.items():
        root = _plant(tmp_path_factory.mktemp("r7"), source)
        if not [p for p in _problems(root, {}, {}) if p.startswith("scripts/planted.py")]:
            missed.append(shape)
    assert not missed, f"the guard did not find: {missed}"


# CONTROL (r7e, new since frozen): passes on the frozen tree, pins behaviour that must stay; no mutant run.
def test_a_read_with_a_size_is_not_a_hit_by_itself(tmp_path: Path) -> None:
    root = _plant(tmp_path, "def f(r):\n    return r.read(10)")
    assert [p for p in _problems(root, {}, {}) if p.startswith("scripts/planted.py")] == []


def _plant(tmp_path: Path, source: str, folder: str = "scripts") -> Path:
    for name in GUARDED_FOLDERS:
        (tmp_path / name).mkdir(parents=True, exist_ok=True)
    (tmp_path / folder / "planted.py").write_text(source + "\n", encoding="utf-8")
    return tmp_path


# CONTROL (r7e, new since frozen): passes on the frozen tree, pins behaviour that must stay; no mutant run.
def test_the_guard_finds_each_planted_shape_on_its_own(tmp_path_factory: pytest.TempPathFactory) -> None:
    missed = []
    for shape, source in PLANTED.items():
        root = _plant(tmp_path_factory.mktemp("shape"), source)
        found = [p for p in _problems(root, {}, {}) if p.startswith("scripts/planted.py")]
        if not found:
            missed.append(shape)
    assert not missed, f"the guard did not find: {missed}"


# CONTROL (r7e, new since frozen): passes on the frozen tree, pins behaviour that must stay; no mutant run.
def test_the_guard_leaves_alone_what_is_not_a_file_call(tmp_path: Path) -> None:
    """No false alarm on plain uses: str.replace, dict.copy, os.path.join, json.loads, asyncio.run."""
    root = _plant(
        tmp_path,
        "import asyncio, json, os\n"
        "x = 'a b'.replace(' ', '_')\nd = {}.copy()\np = os.path.join('a', 'b')\nj = json.loads('1')\n"
        "asyncio.run(main())\nn = os.environ.get('X')\nv = os.getpid()\nl = [1].copy()\n",
    )
    assert _problems(root, {}, {}) == []


# CONTROL (r7e, new since frozen): passes on the frozen tree, pins behaviour that must stay; no mutant run.
def test_an_import_of_a_denied_module_needs_a_reason_per_file(tmp_path: Path) -> None:
    for mod in sorted(DENIED_MODULES):
        root = _plant(tmp_path / mod, f"import {mod}\n")
        found = [p for p in _problems(root, {}, {}) if "needs a written reason" in p]
        assert found and mod in found[0], mod
        listed = {("scripts/planted.py", mod): "a made-up reason for the test"}
        assert [p for p in _problems(root, listed, {}) if "planted.py" in p and "not in the file" not in p] == []
        empty = {("scripts/planted.py", mod): " "}
        assert any("has no reason" in p for p in _problems(root, empty, {}))


# CONTROL (r7e, new since frozen): passes on the frozen tree, pins behaviour that must stay; no mutant run.
def test_a_listed_reason_that_matches_nothing_is_a_failure(tmp_path: Path) -> None:
    root = _plant(tmp_path, "x = 1")
    stale = {("scripts/planted.py", "open"): "a reason for code that is gone"}
    assert any("is not in the file any more" in p for p in _problems(root, {}, stale))
    assert any(
        "is not in the file any more" in p for p in _problems(root, {("scripts/planted.py", "sqlite3"): "r"}, {})
    )


# CONTROL (r7e, new since frozen): passes on the frozen tree, pins behaviour that must stay; no mutant run.
def test_a_planted_call_in_every_guarded_folder_is_found(tmp_path: Path) -> None:
    # the loop below walks GUARDED_FOLDERS itself, so a folder taken out of that tuple would be skipped by the loop: the
    # list of guarded folders is therefore written out here once more and must stay equal to it
    assert GUARDED_FOLDERS == ("src/lead_desk", "load_tools", "demo_only", "scripts", "tools")
    for folder in GUARDED_FOLDERS:
        root = _plant(tmp_path / folder.replace("/", "_"), "import os\nos.listdir('x')", folder)
        assert any(p.startswith(f"{folder}/planted.py") for p in _problems(root, {}, {})), folder


# CONTROL (r7e, new since frozen): passes on the frozen tree, pins behaviour that must stay; no mutant run.
def test_a_tls_loader_is_refused_outside_the_two_demo_fakes(tmp_path: Path) -> None:
    root = _plant(tmp_path, "import ssl\nssl.SSLContext().load_cert_chain('x')")
    assert any("loads certificates outside tls_trust.py" in p for p in _problems(root, {}, {}))


def test_the_listed_exceptions_are_each_used_once_and_have_a_reason() -> None:
    """Each table on its own (merging them could let one hide a gap in the other). A dict literal silently keeps only
    the LAST of two equal keys, so the table text is read and a repeated key is a failure. Whether each entry is still
    used is checked by the sweep test above (`_problems`)."""
    for name, table in (("ALLOWED_IMPORTS", ALLOWED_IMPORTS), ("ALLOWED_CALLS", ALLOWED_CALLS)):
        assert table, name
        for (rel, what), reason in table.items():
            assert reason.strip(), f"{name}: {rel} {what} has no reason"
            assert what.strip(), f"{name}: {rel} names nothing"
            assert (REPO / rel).is_file(), f"{name}: {rel} is not a file of this repository"
    found = set()
    for node in ast.parse(Path(__file__).read_text(encoding="utf-8")).body:
        if (
            isinstance(node, ast.Assign)
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id in {"ALLOWED_IMPORTS", "ALLOWED_CALLS"}
            and isinstance(node.value, ast.Dict)
        ):
            keys = [ast.literal_eval(k) for k in node.value.keys if k is not None]
            repeated = sorted({k for k in keys if keys.count(k) > 1})
            assert not repeated, f"{node.targets[0].id} names a key twice (the later one hides the first): {repeated}"
            found.add(node.targets[0].id)
    assert found == {"ALLOWED_IMPORTS", "ALLOWED_CALLS"}, "the two tables were not found as plain dict literals"
