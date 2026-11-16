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
import fill_flows as ff

DEMO = os.environ.get("FF_DEMO_DIR") or os.path.normpath(os.path.join(HERE, "..", "..", "demo"))
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
PH_VALS = {  # made-up values for the six placeholder names
    "PG_CREDENTIAL_ID": "phv-pg-1",
    "SMTP_CREDENTIAL_ID": "phv-smtp-2",
    "SUB_WORKFLOW_ID": "phv-sub-3",
    "HS_CRED_PLACEHOLDER": "phv-hs-4",
    "FROM_ADDRESS_PLACEHOLDER": "from" + "@" + "example.invalid",
    "INTAKE_ADDRESS_PLACEHOLDER": "intake" + "@" + "example.invalid",
}


def rtext(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def jload(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def jdump(obj, path):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh)


def wtext(path, text, mode="w"):
    with open(path, mode, encoding="utf-8") as fh:
        fh.write(text)


def run(*args):
    """Run the CLI as a subprocess; returns (code, stdout, stderr)."""
    p = subprocess.run(  # noqa: S603
        [sys.executable, "-I", os.path.join(HERE, "fill_flows.py"), *args],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    return p.returncode, p.stdout, p.stderr


def write_values(path, vals):
    with open(path, "w") as fh:
        fh.write("# made-up\n" + "".join(f"{k}={v}\n" for k, v in vals.items()))
    os.chmod(path, 0o600)


def tree_hash(d):
    out = {}
    for n in sorted(os.listdir(d)):
        with open(os.path.join(d, n), "rb") as fh:
            out[n] = hashlib.sha256(fh.read()).hexdigest()
    return out


def all_strings(folder):
    found = set()
    for n in os.listdir(folder):
        found.update(ff.iter_strings(jload(os.path.join(folder, n))))
    return found


class Base(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.mkdtemp(prefix="ff13-", dir=os.environ.get("FF_TEST_BASE"))
        self.addCleanup(shutil.rmtree, self.t, True)
        self.vf = os.path.join(self.t, "flow-values.env")
        write_values(self.vf, VALS)
        self.nflow = 0

    def run(self, *args):  # noqa: A003 - shadows TestCase.run on purpose? no: see below
        raise NotImplementedError

    def copy_flows(self, flavor):
        dst = os.path.join(self.t, "in-" + flavor)
        shutil.copytree(
            os.path.join(DEMO, f"n8n-flows-{flavor}-v5"),
            dst,
            ignore=shutil.ignore_patterns("*.md", "*.txt"),
            dirs_exist_ok=True,
        )
        return dst

    def flow_dir(self, params, top=None):
        """A folder with one tiny flow file whose single node carries `params`."""
        self.nflow += 1
        d = os.path.join(self.t, f"flow-{self.nflow}")
        os.mkdir(d)
        obj = {"name": "t", "nodes": [{"name": "n1", "parameters": params}], "connections": {}}
        obj.update(top or {})
        jdump(obj, os.path.join(d, "mf-x.json"))
        return d

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
                a = jload(os.path.join(src, n))
                b = jload(os.path.join(out, n))
                self.assertEqual(len(a["nodes"]), len(b["nodes"]))
                self.assertEqual(a["connections"], b["connections"])
                self.assertNotIn("$env", rtext(os.path.join(out, n)))
            self.assertEqual(oct(os.stat(out).st_mode & 0o777), "0o700")
            for n in os.listdir(out):
                self.assertEqual(oct(os.stat(os.path.join(out, n)).st_mode & 0o777), "0o600")
            # the unused keys of the other flavor produce only a key-name warning
            self.assertIn("warning: key", se)
            # source untouched
            self.assertIn("$env", rtext(os.path.join(src, "mf-sub-crm-mail.json")))

    def test_expression_forms_are_correct(self):
        src = self.copy_flows("real")
        out = self.out()
        self.assertEqual(run("fill", "--in", src, "--values", self.vf, "--out", out)[0], 0)
        o = jload(os.path.join(out, "mf-sub-crm-mail.json"))
        q = next(n for n in o["nodes"] if "qualify" in str(n["parameters"].get("url", "")))
        self.assertEqual(q["parameters"]["url"], '={{ "' + URL.replace("{", "") + '" }}/qualify')
        self.assertEqual(q["parameters"]["options"]["timeout"], '={{ Number("2500" || 10000) }}')
        al = jload(os.path.join(out, "mf-recovery.json"))
        self.assertIn('={{ "' + VALS["DESK_ALERT_TO"] + '" }}', json.dumps(al).replace('\\"', '"'))

    def test_idempotent_same_bytes(self):
        src = self.copy_flows("film")
        o1, o2 = self.out("a"), self.out("b")
        self.assertEqual(run("fill", "--in", src, "--values", self.vf, "--out", o1)[0], 0)
        self.assertEqual(run("fill", "--in", src, "--values", self.vf, "--out", o2)[0], 0)
        self.assertEqual(tree_hash(o1), tree_hash(o2))
        self.assertEqual(rtext(o1 + ".manifest.json"), rtext(o2 + ".manifest.json"))

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
        return run(
            "fill",
            "--in",
            src or self.copy_flows("real"),
            "--values",
            vf or self.vf,
            "--out",
            out or self.out(),
        )

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
        o = jload(p)
        o["nodes"][0]["parameters"]["extra"] = "={{ $env.DESK_OTHER_THING }}"
        o["nodes"][1]["parameters"]["dyn"] = "={{ $env[name] }}"
        jdump(o, p)
        code, _, se = self.fill(src=src)
        self.assertEqual(code, 1)
        self.assertIn("DESK_OTHER_THING", se)
        self.assertFalse(os.path.exists(self.out()))
        # a non-DESK/MF name is refused even when a value exists for it
        write_values(self.vf, {**VALS, "PATH": "x"})
        o["nodes"][0]["parameters"]["extra"] = "$env.PATH"
        jdump(o, p)
        self.assertEqual(self.fill(src=src)[0], 1)

    def test_dynamic_env_use_refused(self):
        src = self.copy_flows("real")
        p = os.path.join(src, "mf-form.json")
        o = jload(p)
        o["nodes"][1]["parameters"]["dyn"] = "={{ $env[name] }}"
        jdump(o, p)
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
        code, _, _ = self.fill()
        self.assertEqual(code, 1)
        self.assertEqual(os.listdir(self.out()), [])
        src = self.copy_flows("real")
        o = self.out("second")
        self.assertEqual(self.fill(src=src, out=o)[0], 0)
        self.assertEqual(self.fill(src=src, out=o)[0], 1)  # second run refuses, no overwrite

    def test_bad_values(self):
        for bad in ('has"quote', "back\\slash", "new\nline", "tab\there", "cr\rx", "u\u2028x"):
            with open(self.vf, "w", newline="") as fh:
                fh.writelines(f"{k}={bad if k == 'DESK_URL' else v}\n" for k, v in VALS.items())
            code, so, se = self.fill()
            if bad in ('has"quote', "back\\slash"):
                # quotes and backslashes are legal; they must be escaped, not refused
                self.assertEqual(code, 0, bad)
                o = jload(os.path.join(self.out(), "mf-sub-crm-mail.json"))
                url = next(
                    n for n in o["nodes"] if "/qualify" in str(n["parameters"].get("url", ""))
                )
                lit = url["parameters"]["url"][len("={{ ") : -len(" }}/qualify")]
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
        t = rtext(os.path.join(self.out(), "mf-sub-crm-mail.json"))
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
        wtext(os.path.join(src, "mf-form.json"), "{not json")
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
        m = rtext(out + ".manifest.json")
        self.assertNotIn(CANARY, m)
        self.assertEqual(oct(os.stat(out + ".manifest.json").st_mode & 0o777), "0o600")

    def test_refuses_extra_file(self):
        out = self.made()
        wtext(os.path.join(out, "mine.txt"), "keep")
        code, _, se = run("delete", "--out", out)
        self.assertEqual(code, 1)
        self.assertIn("mine.txt", se)
        self.assertTrue(os.path.exists(os.path.join(out, "mf-form.json")))

    def test_hash_change(self):
        out = self.made()
        p = os.path.join(out, "mf-form.json")
        wtext(p, " ", "a")
        code, _, _ = run("delete", "--out", out)
        self.assertEqual(code, 1)
        self.assertTrue(os.path.exists(p))  # nothing deleted
        self.assertEqual(run("delete", "--out", out, "--force-hash")[0], 0)
        self.assertFalse(os.path.exists(out))

    def test_symlink_in_folder(self):
        out = self.made()
        victim = os.path.join(self.t, "victim.txt")
        wtext(victim, "precious")
        p = os.path.join(out, "mf-form.json")
        os.unlink(p)
        os.symlink(victim, p)
        for extra in ((), ("--force-hash",)):
            code, _, _ = run("delete", "--out", out, *extra)
            self.assertEqual(code, 1)
            self.assertEqual(rtext(victim), "precious")

    def test_symlinked_out_dir_and_manifest_names(self):
        out = self.made()
        link = self.out("link")
        os.symlink(out, link)
        self.assertEqual(run("delete", "--out", link)[0], 1)
        self.assertTrue(os.path.isdir(out))
        # a manifest naming a path outside the folder is refused
        man = jload(out + ".manifest.json")
        man["files"]["../victim.txt"] = "0" * 64
        jdump(man, out + ".manifest.json")
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
        self.assertEqual(
            s.string("={{ $env[ 'MF_CRM_URL' ] + $env.MF_CRM_URL }}"), '={{ "x" + "x" }}'
        )
        self.assertEqual(
            s.string("=http://$env.MF_CRM_URL/{{ $env.MF_CRM_URL }}"), '=http://x/{{ "x" }}'
        )
        self.assertEqual(s.string("={{ $env.DESK_URL }}"), '={{ "a\\"b\\\\c" }}')
        self.assertEqual(s.bad, set())
        s.string("={{ $env.DESK_NOPE }}")
        self.assertEqual(s.bad, {"DESK_NOPE"})

    def test_values_never_in_messages_in_process(self):
        with open(self.vf, "w", newline="") as fh:
            fh.write("DESK_URL=" + CANARY + "\r\n")
        buf = io.StringIO()
        with redirect_stdout(buf), redirect_stderr(buf):
            code = ff.main(
                ["fill", "--in", self.copy_flows("real"), "--values", self.vf, "--out", self.out()]
            )
        self.assertEqual(code, 1)
        self.assertNotIn(CANARY, buf.getvalue())

    def test_property_roundtrip_random_values(self):
        import random

        rnd = random.Random(7)  # noqa: S311 - test data only
        alphabet = "ab\"\\{}$'`/:.%\u00e9\u4e2d "
        for _ in range(200):
            v = "".join(rnd.choice(alphabet) for _ in range(rnd.randint(1, 12)))
            if "$env" in v or v.strip() == "" and not v:
                continue
            lit = ff._js_literal(v)
            self.assertNotIn("}}", lit)
            self.assertEqual(json.loads(lit.replace("\\u007b", "{").replace("\\u007d", "}")), v)


if __name__ == "__main__":
    unittest.main()
