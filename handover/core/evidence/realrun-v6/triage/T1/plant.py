import sys, hashlib, shutil, subprocess, pathlib, json
# usage: plant.py NAME LOG pytest-args... ; plants mutant NAME, runs, restores, compares hashes
T = pathlib.Path('/home/user/build/rr6/tree-T1')
MUT = {
 'R20': ('scripts/run_real_check.py', 'print("refused: --config: the config file cannot be read")', 'print("refused: FileNotFoundError")'),
 'SIMPREP3': ('scripts/run_real_check.py', '    config = confine_anywhere(path, what="--config")', '    config = path'),
 'N20': ('scripts/run_real_check.py', '    if out.is_dir():\n        return "REAL_RESULT_FILE", "the result path is a folder', '    if False:\n        return "REAL_RESULT_FILE", "the result path is a folder'),
}
name, log, *args = sys.argv[1:]
p = T / 'scripts/run_real_check.py'
orig = p.read_bytes(); h = hashlib.sha256(orig).hexdigest()
bak = pathlib.Path('/home/user/build/rr6/tmp-T1/orig-' + name); bak.write_bytes(orig)
s = orig.decode()
for n in name.split('+'):
    f, old, new = MUT[n]; assert s.count(old) == 1, n; s = s.replace(old, new, 1)
try:
    p.write_text(s)
    subprocess.run(['/home/user/build/rr6/out/T1/run.sh', log, *args])
finally:
    p.write_bytes(orig)
print(name, 'restored', hashlib.sha256(p.read_bytes()).hexdigest() == h)
