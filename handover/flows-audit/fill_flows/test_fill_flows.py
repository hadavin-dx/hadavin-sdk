"""Self-test with made-up values only. Run: python -m unittest -v (in this folder)."""

import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fill_flows as ff  # noqa: E402

DEMO = os.path.normpath(os.path.join(HERE, "..", "..", "demo"))
BASE = "/tmp/ff13"
CANARY = "CANARY" + "-" + "q7x" + "-" + "zz"  # made-up, built from parts
URL = "http://127.0.0.1:9/" + CANARY
VALS = {
    "DESK_URL": URL,
    "DESK_TIMEOUT_MS": "2500",
    "DESK_ALERT_TO": "desk" + "@" + "example.invalid",
    "MF_STAGE_URL": "http://127.0.0.1:9/stage",
    "MF_STAGE_TIMEOUT_MS": "3000",
    "MF_CRM_URL": "http://127.0.0.1:9/crm",
}


def run(*args):
    """Run the CLI as a subprocess; returns (code, stdout, stderr)."""
    p = subprocess.run(
        [sys.executable, "-I", os.path.join(HERE, "fill_flows.py"), *args],
        capture_output=True, text=True, timeout=60,
    )
    return p.returncode, p.stdout, p.stderr


def write_values(path, vals):
    with open(path, "w") as fh:
        fh.write("# made-up\n" + "".join(f"{k}={v}\n" for k, v in vals.items()))


def tree_hash(d):
    return {n: hashlib.sha256(open(os.path.join(d, n), "rb").read()).hexdigest()
            for n in sorted(os.listdir(d))}


class Base(unittest.TestCase):
    def setUp(self):
        os.makedirs(BASE, exist_ok=True)
        self.t = tempfile.mkdtemp(dir=BASE)
        self.addCleanup(shutil.rmtree, self.t, True)
        self.vf = os.path.join(self.t, "flow-values.env")
        write_values(self.vf, VALS)

    def copy_flows(self, flavor):
        dst = os.path.join(self.t, "in-" + flavor)
        shutil.copytree(os.path.join(DEMO, f"n8n-flows-{flavor}-v5"), dst,
                        ignore=shutil.ignore_patterns("*.md", "*.txt"))
        return dst

    def out(self, name="out"):
        return os.path.join(self.t, name)


class Positive(Base):
    def test_real_and_film(self):
        for flavor in ("real", "film"):
            src = self.copy_flows(flavor)
            out = self.out("o-" + flavor)
            code, so, se = run("fill", "--in", src, "--values", self.vf, "--out", out)
            self.assertEqual(code, 0, se)
            for stream in (so, se):
                self.assertNotIn(CANARY, stream)
                self.assertNotIn(VALS["DESK_ALERT_TO"], stream)
            self.assertEqual(sorted(os.listdir(out)), sorted(os.listdir(src)))
            for n in os.listdir(src):
                a = json.load(open(os.path.join(src, n)))
                b = json.load(open(os.path.join(out, n)))
                self.assertEqual(len(a["nodes"]), len(b["nodes"]))
                self.assertEqual(a["connections"], b["connections"])
                self.assertNotIn("$env", open(os.path.join(out, n)).read())
            self.assertEqual(oct(os.stat(out).st_mode & 0o777), "0o700")
            for n in os.listdir(out):
                self.assertEqual(oct(os.stat(os.path.join(out, n)).st_mode & 0o777), "0o600")
            # the unused keys of the other flavor produce only a key-name warning
            self.assertIn("warning: key", se)
            # source untouched
            self.assertIn("$env", open(os.path.join(src, "mf-sub-crm-mail.json")).read())

    def test_expression_forms_are_correct(self):
        b = json.load(open(os.path.join(self.out("o-x") or "", "x"))) if False else None
        del b
        src = self.copy_flows("real")
        out = self.out()
        self.assertEqual(run("fill", "--in", src, "--values", self.vf, "--out", out)[0], 0)
        o = json.load(open(os.path.join(out, "mf-sub-crm-mail.json")))
        q = next(n for n in o["nodes"] if "qualify" in str(n["parameters"].get("url", "")))
        self.assertEqual(q["parameters"]["url"], '={{ "' + URL.replace("{", "") + '" }}/qualify')
        self.assertEqual(q["parameters"]["options"]["timeout"],
                         '={{ Number("2500" || 10000) }}')
        al = json.load(open(os.path.join(out, "mf-recovery.json")))
        self.assertIn('={{ "' + VALS["DESK_ALERT_TO"] + '" }}',
                      json.dumps(al).replace('\\"', '"'))

    def test_idempotent_same_bytes(self):
        src = self.copy_flows("film")
        o1, o2 = self.out("a"), self.out("b")
        self.assertEqual(run("fill", "--in", src, "--values", self.vf, "--out", o1)[0], 0)
        self.assertEqual(run("fill", "--in", src, "--values", self.vf, "--out", o2)[0], 0)
        self.assertEqual(tree_hash(o1), tree_hash(o2))
        self.assertEqual(open(o1 + ".manifest.json").read(), open(o2 + ".manifest.json").read())

    def test_already_filled_input_exit_4(self):
        src = self.copy_flows("film")
        o1, o2 = self.out("a"), self.out("b")
        run("fill", "--in", src, "--values", self.vf, "--out", o1)
        code, _, se = run("fill", "--in", o1, "--values", self.vf, "--out", o2)
        self.assertEqual(code, ff.EXIT_NOTHING)
        self.assertIn("nothing to fill", se)
        self.assertFalse(os.path.exists(o2))

    def test_check_mode(self):
        src = self.copy_flows("real")
        code, so, _ = run("check", src)
        self.assertEqual(code, 1)
        for w in ("DESK_URL", "DESK_ALERT_TO", "SUB_WORKFLOW_ID", "PG_CREDENTIAL_ID"):
            self.assertIn(w, so)
        out = self.out()
        run("fill", "--in", src, "--values", self.vf, "--out", out)
        code, so, _ = run("check", out, "--tokens-only")
        self.assertEqual((code, "token" in so), (0, False))
        self.assertEqual(run("check", out)[0], 1)  # placeholders remain (filled later)
        self.assertNotIn(CANARY, run("check", out)[1])
        self.assertFalse(os.path.exists(out + "x"))


class Negative(Base):
    def fill(self, src=None, vf=None, out=None):
        return run("fill", "--in", src or self.copy_flows("real"),
                   "--values", vf or self.vf, "--out", out or self.out())

    def test_missing_key(self):
        v = {k: x for k, x in VALS.items() if k != "DESK_URL"}
        write_values(self.vf, v)
        code, _, se = self.fill()
        self.assertEqual(code, 1)
        self.assertIn("DESK_URL", se)
        self.assertFalse(os.path.exists(self.out()))

    def test_empty_value(self):
        write_values(self.vf, {**VALS, "DESK_URL": ""})
        code, _, se = self.fill()
        self.assertEqual(code, 1)
        self.assertIn("DESK_URL", se)
        self.assertFalse(os.path.exists(self.out()))

    def test_extra_unknown_key_warns_only(self):
        write_values(self.vf, {**VALS, "MF_UNUSED_KEY": "abc"})
        code, _, se = self.fill()
        self.assertEqual(code, 0)
        self.assertIn("MF_UNUSED_KEY", se)
        self.assertNotIn("abc", se.replace("MF_UNUSED_KEY", ""))

    def test_leftover_token_in_added_node(self):
        src = self.copy_flows("real")
        p = os.path.join(src, "mf-form.json")
        o = json.load(open(p))
        o["nodes"][0]["parameters"]["extra"] = "={{ $env.DESK_OTHER_THING }}"
        o["nodes"][1]["parameters"]["dyn"] = "={{ $env[name] }}"
        json.dump(o, open(p, "w"))
        code, _, se = self.fill(src=src)
        self.assertEqual(code, 1)
        self.assertIn("DESK_OTHER_THING", se)
        self.assertFalse(os.path.exists(self.out()))
        # a non-DESK/MF name is refused even when a value exists for it
        write_values(self.vf, {**VALS, "PATH": "x"})
        o["nodes"][0]["parameters"]["extra"] = "$env.PATH"
        json.dump(o, open(p, "w"))
        self.assertEqual(self.fill(src=src)[0], 1)

    def test_dynamic_env_use_refused(self):
        src = self.copy_flows("real")
        p = os.path.join(src, "mf-form.json")
        o = json.load(open(p))
        o["nodes"][1]["parameters"]["dyn"] = "={{ $env[name] }}"
        json.dump(o, open(p, "w"))
        code, _, se = self.fill(src=src)
        self.assertEqual(code, 1)
        self.assertIn("mf-form.json", se)

    def test_output_inside_repo(self):
        repo = os.path.join(self.t, "repo")
        os.makedirs(os.path.join(repo, ".git"))
        code, _, se = self.fill(out=os.path.join(repo, "sub", "o"))
        self.assertEqual(code, 1)
        self.assertIn("git", se)
        code, _, se = self.fill(out=os.path.join(repo, "o"))
        self.assertEqual(code, 1)
        self.assertFalse(os.path.exists(os.path.join(repo, "o")))

    def test_output_exists(self):
        os.mkdir(self.out())
        code, _, se = self.fill()
        self.assertEqual(code, 1)
        self.assertEqual(os.listdir(self.out()), [])
        src = self.copy_flows("real")
        o = self.out("second")
        self.assertEqual(self.fill(src=src, out=o)[0], 0)
        self.assertEqual(self.fill(src=src, out=o)[0], 1)  # second run refuses, no overwrite

    def test_bad_values(self):
        for bad in ('has"quote', "back\\slash", "new\nline", "tab\there", "cr\rx", "u\u2028x"):
            with open(self.vf, "w", newline="") as fh:
                for k, v in VALS.items():
                    fh.write(f"{k}={bad if k == 'DESK_URL' else v}\n")
            code, so, se = self.fill()
            if bad in ('has"quote', "back\\slash"):
                # quotes and backslashes are legal; they must be escaped, not refused
                self.assertEqual(code, 0, bad)
                o = json.load(open(os.path.join(self.out(), "mf-sub-crm-mail.json")))
                url = next(n for n in o["nodes"]
                           if "/qualify" in str(n["parameters"].get("url", "")))
                lit = url["parameters"]["url"][len("={{ "):-len(" }}/qualify")]
                self.assertEqual(json.loads(lit), bad)  # the literal reads back exactly
                shutil.rmtree(self.out())
                os.unlink(self.out() + ".manifest.json")
            else:
                self.assertEqual(code, 1, repr(bad))
                self.assertFalse(os.path.exists(self.out()))
            self.assertNotIn(bad, so + se)

    def test_braces_cannot_close_expression(self):
        write_values(self.vf, {**VALS, "DESK_URL": "http://127.0.0.1:9/a}}b{{c"})
        self.assertEqual(self.fill()[0], 0)
        t = open(os.path.join(self.out(), "mf-sub-crm-mail.json")).read()
        self.assertNotIn("a}}b", t)
        self.assertIn("\\\\u007d\\\\u007d", t)

    def test_value_with_env_and_duplicate_key(self):
        write_values(self.vf, {**VALS, "DESK_URL": "x$env.y"})
        self.assertEqual(self.fill()[0], 1)
        with open(self.vf, "w") as fh:
            fh.write("DESK_URL=a\nDESK_URL=b\n")
        code, _, se = self.fill()
        self.assertEqual(code, 1)
        self.assertNotIn("=b", se)

    def test_symlink_input_refused(self):
        src = self.copy_flows("real")
        os.symlink(os.path.join(src, "mf-form.json"), os.path.join(src, "link.json"))
        self.assertEqual(self.fill(src=src)[0], 1)

    def test_invalid_json_input(self):
        src = self.copy_flows("real")
        open(os.path.join(src, "mf-form.json"), "w").write("{not json")
        code, _, se = self.fill(src=src)
        self.assertEqual(code, 1)
        self.assertIn("mf-form.json", se)
        self.assertFalse(os.path.exists(self.out()))


class Delete(Base):
    def made(self):
        out = self.out()
        run("fill", "--in", self.copy_flows("film"), "--values", self.vf, "--out", out)
        return out

    def test_delete_ok(self):
        out = self.made()
        code, _, _ = run("delete", "--out", out)
        self.assertEqual(code, 0)
        self.assertFalse(os.path.exists(out))
        self.assertFalse(os.path.exists(out + ".manifest.json"))

    def test_manifest_has_no_values(self):
        out = self.made()
        m = open(out + ".manifest.json").read()
        self.assertNotIn(CANARY, m)
        self.assertEqual(oct(os.stat(out + ".manifest.json").st_mode & 0o777), "0o600")

    def test_refuses_extra_file(self):
        out = self.made()
        open(os.path.join(out, "mine.txt"), "w").write("keep")
        code, _, se = run("delete", "--out", out)
        self.assertEqual(code, 1)
        self.assertIn("mine.txt", se)
        self.assertTrue(os.path.exists(os.path.join(out, "mf-form.json")))

    def test_hash_change(self):
        out = self.made()
        p = os.path.join(out, "mf-form.json")
        open(p, "a").write(" ")
        code, _, se = run("delete", "--out", out)
        self.assertEqual(code, 1)
        self.assertTrue(os.path.exists(p))  # nothing deleted
        self.assertEqual(run("delete", "--out", out, "--force-hash")[0], 0)
        self.assertFalse(os.path.exists(out))

    def test_symlink_in_folder(self):
        out = self.made()
        victim = os.path.join(self.t, "victim.txt")
        open(victim, "w").write("precious")
        p = os.path.join(out, "mf-form.json")
        os.unlink(p)
        os.symlink(victim, p)
        for extra in ((), ("--force-hash",)):
            code, _, _ = run("delete", "--out", out, *extra)
            self.assertEqual(code, 1)
            self.assertEqual(open(victim).read(), "precious")

    def test_symlinked_out_dir_and_manifest_names(self):
        out = self.made()
        link = self.out("link")
        os.symlink(out, link)
        self.assertEqual(run("delete", "--out", link)[0], 1)
        self.assertTrue(os.path.isdir(out))
        # a manifest naming a path outside the folder is refused
        man = json.load(open(out + ".manifest.json"))
        man["files"]["../victim.txt"] = "0" * 64
        json.dump(man, open(out + ".manifest.json", "w"))
        self.assertEqual(run("delete", "--out", out)[0], 1)
        self.assertTrue(os.path.exists(os.path.join(out, "mf-form.json")))

    def test_no_manifest(self):
        out = self.made()
        os.unlink(out + ".manifest.json")
        self.assertEqual(run("delete", "--out", out)[0], 1)
        self.assertTrue(os.path.isdir(out))


class Unit(Base):
    def test_token_forms(self):
        s = ff.Subst({"DESK_URL": 'a"b\\c', "MF_CRM_URL": "x"})
        self.assertEqual(s.string("$env.DESK_URL"), 'a"b\\c')  # plain field: raw text
        self.assertEqual(s.string("={{$env.MF_CRM_URL}}"), '={{"x"}}')
        self.assertEqual(s.string("={{ $env['MF_CRM_URL'] }}"), '={{ "x" }}')
        self.assertEqual(s.string('={{ $env["MF_CRM_URL"] }}'), '={{ "x" }}')
        self.assertEqual(s.string("={{ $env[ 'MF_CRM_URL' ] + $env.MF_CRM_URL }}"),
                         '={{ "x" + "x" }}')
        self.assertEqual(s.string("=http://$env.MF_CRM_URL/{{ $env.MF_CRM_URL }}"),
                         '=http://x/{{ "x" }}')
        self.assertEqual(s.string("={{ $env.DESK_URL }}"), '={{ "a\\"b\\\\c" }}')
        self.assertEqual(s.bad, set())
        s.string("={{ $env.DESK_NOPE }}")
        self.assertEqual(s.bad, {"DESK_NOPE"})

    def test_values_never_in_messages_in_process(self):
        write_values(self.vf, {**VALS, "DESK_URL": CANARY + "\n"})
        buf = io.StringIO()
        with redirect_stdout(buf), redirect_stderr(buf):
            code = ff.main(["fill", "--in", self.copy_flows("real"),
                            "--values", self.vf, "--out", self.out()])
        self.assertEqual(code, 1)
        self.assertNotIn(CANARY, buf.getvalue())

    def test_property_roundtrip_random_values(self):
        import random

        rnd = random.Random(7)
        alphabet = 'ab"\\{}$\'`/:.%\u00e9\u4e2d '
        for _ in range(200):
            v = "".join(rnd.choice(alphabet) for _ in range(rnd.randint(1, 12)))
            if "$env" in v or v.strip() == "" and not v:
                continue
            lit = ff._js_literal(v)
            self.assertNotIn("}}", lit)
            self.assertEqual(json.loads(lit.replace("\\u007b", "{").replace("\\u007d", "}")), v)


if __name__ == "__main__":
    unittest.main()
