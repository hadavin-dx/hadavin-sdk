"""Self-test with made-up values only. Run: python -m unittest -v (in this folder)."""

import hashlib
import io
import json
import os
import random
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock

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

    def cli(self, *args):
        """Run the CLI; fail the test if ANY made-up value shows in stdout or stderr."""
        code, so, se = run(*args)
        for v in (*VALS.values(), *PH_VALS.values()):
            self.assertNotIn(v, so, "a value reached stdout")
            self.assertNotIn(v, se, "a value reached stderr")
        return code, so, se

    def fill(self, src=None, vf=None, out=None):
        return self.cli(
            "fill",
            "--in",
            src or self.copy_flows("real"),
            "--values",
            vf or self.vf,
            "--out",
            out or self.out(),
        )

    def refuse(self, params, *needles, top=None, vals=None):
        """A one-node flow with `params` must be refused: exit 1, needles named, nothing written."""
        if vals is not None:
            write_values(self.vf, vals)
        code, _, se = self.fill(src=self.flow_dir(params, top))
        self.assertEqual(code, 1, se)
        self.assertIn("mf-x.json", se)
        for w in needles:
            self.assertIn(w, se)
        self.assertFalse(os.path.exists(self.out()))
        self.assertFalse(os.path.exists(self.out() + ".manifest.json"))
        return se

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
            code, so, se = self.fill(src=src, out=out)
            self.assertEqual(code, 0, se)
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
            # six placeholders are still in the files and the values file has no key for them
            self.assertIn("NOT READY TO IMPORT: ", so)
            # source untouched
            self.assertIn("$env", rtext(os.path.join(src, "mf-sub-crm-mail.json")))

    def test_real_expressions(self):
        src = self.copy_flows("real")
        out = self.out()
        self.assertEqual(self.fill(src=src, out=out)[0], 0)
        found = all_strings(out)
        self.assertIn("={{ " + json.dumps(URL) + " }}/qualify", found)
        self.assertIn('={{ Number("2500" || 10000) }}', found)
        self.assertIn("={{ " + json.dumps(VALS["DESK_ALERT_TO"]) + " }}", found)

    def test_film_expressions(self):
        src = self.copy_flows("film")
        out = self.out()
        self.assertEqual(self.fill(src=src, out=out)[0], 0)
        found = all_strings(out)
        self.assertIn('={{ "http://127.0.0.1:9/stage" }}/qualify', found)
        self.assertIn('={{ Number("3000" || 10000) }}', found)
        self.assertIn('={{ "http://127.0.0.1:9/crm" }}/upsert', found)

    def test_token_in_every_location(self):
        top = {
            "pinData": {
                "n1": [{"json": {"u": "={{ $env.DESK_URL }}", "p": "x $env.DESK_ALERT_TO"}}]
            },
        }
        params = {
            "k $env.DESK_URL": 1,
            "lst": ["={{ $env.DESK_URL }}", "plain $env.DESK_TIMEOUT_MS", ["={{ $env.DESK_URL }}"]],
            "credentials": {"c": {"id": "1", "name": "cred $env.DESK_ALERT_TO"}},
        }
        src = self.flow_dir(params, top)
        p = os.path.join(src, "mf-x.json")
        o = jload(p)
        o["nodes"][0]["name"] = "node $env.DESK_ALERT_TO"
        jdump(o, p)
        self.assertEqual(run("check", src, "--tokens-only")[0], 1)
        out = self.out()
        code, _, se = self.fill(src=src, out=out)
        self.assertEqual(code, 0, se)
        found = all_strings(out)
        self.assertFalse([t for t in found if "$env" in t])
        for want in (
            "k " + URL,
            "={{ " + json.dumps(URL) + " }}",
            "plain 2500",
            "cred " + VALS["DESK_ALERT_TO"],
            "node " + VALS["DESK_ALERT_TO"],
            "x " + VALS["DESK_ALERT_TO"],
        ):
            self.assertIn(want, found)
        self.assertEqual(run("check", out, "--tokens-only")[0], 0)

    def test_idempotent_same_bytes(self):
        src = self.copy_flows("film")
        o1, o2 = self.out("a"), self.out("b")
        self.assertEqual(self.fill(src=src, out=o1)[0], 0)
        self.assertEqual(self.fill(src=src, out=o2)[0], 0)
        self.assertEqual(tree_hash(o1), tree_hash(o2))
        self.assertEqual(rtext(o1 + ".manifest.json"), rtext(o2 + ".manifest.json"))

    def test_already_filled_input_exit_4(self):
        src = self.copy_flows("film")
        o1, o2 = self.out("a"), self.out("b")
        self.fill(src=src, out=o1)
        code, _, se = self.fill(src=o1, out=o2)
        self.assertEqual(code, 4)
        self.assertIn("nothing to fill", se)
        self.assertFalse(os.path.exists(o2))

    def test_placeholders_filled_when_keys_given(self):
        src = self.copy_flows("real")
        left = sum(
            1
            for n in os.listdir(src)
            for t in ff.iter_strings(jload(os.path.join(src, n)))
            if t in ff.PLACEHOLDERS
        )
        self.assertGreater(left, 0)
        out1 = self.out("one")
        code, so, _ = self.fill(src=src, out=out1)
        self.assertEqual(code, 0)
        self.assertIn(f"NOT READY TO IMPORT: {left} placeholders left", so)
        write_values(self.vf, {**VALS, **PH_VALS})
        out2 = self.out("two")
        code, so, se = self.fill(src=src, out=out2)
        self.assertEqual(code, 0, se)
        self.assertNotIn("NOT READY", so)
        found = all_strings(out2)
        self.assertFalse([t for t in found if t in ff.PLACEHOLDERS])
        self.assertIn("phv-pg-1", found)
        self.assertIn(PH_VALS["FROM_ADDRESS_PLACEHOLDER"], found)
        self.assertEqual(run("check", out2)[0], 0)
        self.assertEqual(run("check", out1)[0], 1)

    def test_check_mode(self):
        src = self.copy_flows("real")
        code, so, _ = run("check", src)
        self.assertEqual(code, 1)
        for w in ("DESK_URL", "DESK_ALERT_TO", "SUB_WORKFLOW_ID", "PG_CREDENTIAL_ID"):
            self.assertIn(w, so)
        out = self.out()
        self.fill(src=src, out=out)
        code, so, _ = run("check", out, "--tokens-only")
        self.assertEqual((code, "token" in so), (0, False))
        code, so, _ = self.cli("check", out)
        self.assertEqual(code, 1)  # placeholders remain
        self.assertIn("placeholder", so)

    def test_check_reads_parsed_json_forms(self):
        d = self.flow_dir(
            {
                "a": "$env.DESK_URL",  # plain string
                "b": '={{ $env["DESK_TIMEOUT_MS"] }}',  # bracket form with quotes (escaped in JSON)
                "c": "={{ $env[name] }}",  # dynamic form
            }
        )
        code, so, _ = run("check", d)
        self.assertEqual(code, 1)
        self.assertIn("token $env DESK_URL", so)
        self.assertIn("token $env DESK_TIMEOUT_MS", so)
        self.assertIn("1 other $env use", so)
        self.assertIn("3 problem(s)", so)

    def test_check_bad_json_and_nan(self):
        d = self.flow_dir({})
        wtext(os.path.join(d, "bad.json"), "{nope")
        wtext(os.path.join(d, "nan.json"), '{"nodes": [], "x": NaN}')
        code, so, _ = run("check", d)
        self.assertEqual(code, 1)
        self.assertIn("bad.json", so)
        self.assertIn("nan.json", so)
        self.assertEqual(so.count("not valid JSON"), 2)


class Negative(Base):
    def test_missing_key(self):
        v = {k: x for k, x in VALS.items() if k != "DESK_URL"}
        write_values(self.vf, v)
        code, _, se = self.fill()
        self.assertEqual(code, 1)
        self.assertIn("missing or empty", se)
        self.assertIn("DESK_URL", se)
        self.assertFalse(os.path.exists(self.out()))

    def test_empty_value(self):
        write_values(self.vf, {**VALS, "DESK_URL": ""})
        code, _, se = self.fill()
        self.assertEqual(code, 1)
        self.assertIn("missing or empty", se)
        self.assertIn("DESK_URL", se)
        self.assertFalse(os.path.exists(self.out()))

    def test_extra_unknown_key_warns_only(self):
        write_values(self.vf, {**VALS, "MF_UNUSED_KEY": "abc"})
        code, _, se = self.fill()
        self.assertEqual(code, 0)
        self.assertIn("MF_UNUSED_KEY", se)
        self.assertNotIn("abc", se.replace("MF_UNUSED_KEY", ""))

    def test_other_name_refused_even_with_value(self):
        # a clean flow, so the refusal can only come from the name rule
        self.refuse({"x": "$env.PATH"}, "PATH", vals={**VALS, "PATH": "xyz"})

    def test_leftover_token_unknown_name(self):
        self.refuse({"x": "={{ $env.DESK_OTHER_THING }}"}, "DESK_OTHER_THING")

    def test_dynamic_env_use_refused(self):
        self.refuse({"dyn": "={{ $env[name] }}"}, "$env token is left")

    def test_token_outside_braces_refused(self):
        self.refuse({"u": "=http://$env.DESK_URL/x"}, "outside a clean {{ }}")
        self.refuse({"u": "={{ 1 }} $env.DESK_URL"}, "outside a clean {{ }}")

    def test_token_in_quoted_js_string_refused(self):
        self.refuse({"u": '={{ "a $env.DESK_URL" }}'}, "quoted JS string")
        self.refuse({"u": "={{ 'a' + '$env.DESK_URL' }}"}, "quoted JS string")
        self.refuse({"u": "={{ `x${$env.DESK_URL}` }}"}, "quoted JS string")

    def test_token_in_code_fields_refused(self):
        for key in ("jsCode", "functionCode", "pythonCode"):
            self.refuse({key: "return $env.DESK_URL"}, key)
            self.refuse({key: "={{ $env.DESK_URL }}"}, key)

    def test_broken_or_nested_braces_refused(self):
        self.refuse({"u": "={{ $env.DESK_URL }} }}"}, "outside a clean {{ }}")
        self.refuse({"u": "={{ {{ $env.DESK_URL }}"}, "outside a clean {{ }}")
        self.refuse({"u": "={{ $env.DESK_URL "}, "outside a clean {{ }}")

    def test_comment_in_expression_refused(self):
        self.refuse({"u": "={{ $env.DESK_URL // note }}"}, "comment")

    def test_output_inside_repo(self):
        repo = os.path.join(self.t, "repo")
        os.makedirs(os.path.join(repo, ".git"))
        code, _, se = self.fill(out=os.path.join(repo, "sub", "o"))
        self.assertEqual(code, 1)
        self.assertIn("git", se)
        code, _, se = self.fill(out=os.path.join(repo, "o"))
        self.assertEqual(code, 1)
        self.assertFalse(os.path.exists(os.path.join(repo, "o")))

    def test_output_under_mnt_refused(self):
        code, _, se = self.fill(out="/mnt/ff13-never-created")
        self.assertEqual(code, 1)
        self.assertIn("/mnt", se)
        self.assertFalse(os.path.exists("/mnt/ff13-never-created"))

    def test_output_exists(self):
        os.mkdir(self.out())
        code, _, se = self.fill()
        self.assertEqual(code, 1)
        self.assertIn("already exists", se)
        self.assertEqual(os.listdir(self.out()), [])
        src = self.copy_flows("real")
        o = self.out("second")
        self.assertEqual(self.fill(src=src, out=o)[0], 0)
        self.assertEqual(self.fill(src=src, out=o)[0], 1)  # second run refuses, no overwrite

    def test_bad_values(self):
        cases = {
            "new\nline": "line 2: no '='",
            "tab\there": "control or line-break",
            "cr\rx": "control or line-break",
            "u\u2028x": "control or line-break",
            "x{{y": "contains '{{' or '}}'",
            "x}}y": "contains '{{' or '}}'",
            "x$env.y": "contains '$env'",
            ' "quoted"': "space at its start or end",
            '"quoted"': "quote mark",
            "'quoted'": "quote mark",
            "trail ": "space at its start or end",
            "lead\x7fx": "control or line-break",
        }
        for bad, msg in cases.items():
            with open(self.vf, "w", newline="") as fh:
                fh.writelines(f"{k}={bad if k == 'DESK_URL' else v}\n" for k, v in VALS.items())
            code, so, se = self.fill()
            self.assertEqual(code, 1, repr(bad))
            self.assertIn(msg, se, repr(bad))
            self.assertIn("DESK_URL" if "line 2" not in msg else "values file", se)
            self.assertFalse(os.path.exists(self.out()))
            self.assertNotIn(bad.strip(), (so + se).replace("DESK_URL", ""), repr(bad))

    def test_quote_and_backslash_in_middle_are_escaped(self):
        for bad in ('has"quote', "back\\slash", "it's"):
            with open(self.vf, "w", newline="") as fh:
                fh.writelines(f"{k}={bad if k == 'DESK_URL' else v}\n" for k, v in VALS.items())
            code = self.fill()[0]
            self.assertEqual(code, 0, bad)
            self.assertIn("={{ " + json.dumps(bad) + " }}/qualify", all_strings(self.out()))
            shutil.rmtree(self.out())
            os.unlink(self.out() + ".manifest.json")

    def test_inline_comment_marker_warns(self):
        write_values(self.vf, {**VALS, "MF_CRM_URL": "http://127.0.0.1:9/crm #old"})
        code, _, se = self.fill()
        self.assertEqual(code, 0)
        self.assertIn("value of MF_CRM_URL contains ' #'", se)

    def test_bom_refused(self):
        with open(self.vf, "wb") as fh:
            fh.write(b"\xef\xbb\xbf" + b"DESK_URL=x\n")
        code, _, se = self.fill()
        self.assertEqual(code, 1)
        self.assertIn("BOM", se)

    def test_values_file_modes_and_places(self):
        os.chmod(self.vf, 0o644)
        code, _, se = self.fill()
        self.assertEqual((code, "chmod 600" in se), (1, True))
        os.chmod(self.vf, 0o640)
        self.assertEqual(self.fill()[0], 1)
        os.chmod(self.vf, 0o600)
        # inside a git repository
        repo = os.path.join(self.t, "repo")
        os.makedirs(os.path.join(repo, ".git"))
        inside = os.path.join(repo, "v.env")
        write_values(inside, VALS)
        code, _, se = self.fill(vf=inside)
        self.assertEqual((code, "git repository" in se), (1, True))
        # a symlink to a good file
        link = os.path.join(self.t, "link.env")
        os.symlink(self.vf, link)
        code, _, se = self.fill(vf=link)
        self.assertEqual((code, "symlink" in se), (1, True))
        self.assertFalse(os.path.exists(self.out()))

    def test_values_file_under_mnt_refused(self):
        with self.assertRaises(ff.Refused) as cm:
            ff.read_values("/mnt/ff13-never/values.env")
        self.assertIn("/mnt", str(cm.exception))
        self.assertTrue(ff.under_mnt("/mnt/x"))
        self.assertFalse(ff.under_mnt("/mntx/y"))

    def test_duplicate_key(self):
        with open(self.vf, "w") as fh:
            fh.write("DESK_URL=a\nDESK_URL=b\n")
        code, _, se = self.fill()
        self.assertEqual(code, 1)
        self.assertIn("appears twice", se)
        self.assertNotIn("=b", se)

    def test_symlink_input_refused(self):
        src = self.copy_flows("real")
        os.symlink(os.path.join(src, "mf-form.json"), os.path.join(src, "link.json"))
        code, _, se = self.fill(src=src)
        self.assertEqual(code, 1)
        self.assertIn("link.json", se)

    def test_upper_case_json_refused(self):
        src = self.copy_flows("real")
        shutil.copy(os.path.join(src, "mf-form.json"), os.path.join(src, "OTHER.JSON"))
        code, _, se = self.fill(src=src)
        self.assertEqual(code, 1)
        self.assertIn("OTHER.JSON", se)

    def test_invalid_json_input(self):
        src = self.copy_flows("real")
        wtext(os.path.join(src, "mf-form.json"), "{not json")
        code, _, se = self.fill(src=src)
        self.assertEqual(code, 1)
        self.assertIn("mf-form.json", se)
        self.assertFalse(os.path.exists(self.out()))
        wtext(os.path.join(src, "mf-form.json"), '{"nodes": [], "connections": {}, "x": NaN}')
        self.assertEqual(self.fill(src=src)[0], 1)

    def test_failed_write_removes_everything_and_manifest_goes_first(self):
        calls = []
        real = ff._write_new

        def flaky(path, data):
            calls.append(os.path.basename(path))
            if len(calls) == 3:
                raise OSError("disk full (test)")
            return real(path, data)

        out = self.out()
        buf = io.StringIO()
        with mock.patch.object(ff, "_write_new", flaky), redirect_stderr(buf):
            code = ff.main(
                ["fill", "--in", self.copy_flows("real"), "--values", self.vf, "--out", out]
            )
        self.assertEqual(code, 1)
        self.assertIn("failed: OSError", buf.getvalue())
        self.assertEqual(len(calls), 3)
        self.assertTrue(calls[0].endswith(".manifest.json"))
        self.assertFalse(os.path.exists(out))
        self.assertFalse(os.path.exists(out + ".manifest.json"))


class Delete(Base):
    def made(self):
        out = self.out()
        self.fill(src=self.copy_flows("film"), out=out)
        return out

    def test_delete_ok(self):
        out = self.made()
        code, _, _ = self.cli("delete", "--out", out)
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
        code, _, se = self.cli("delete", "--out", out)
        self.assertEqual(code, 1)
        self.assertIn("mine.txt", se)
        self.assertTrue(os.path.exists(os.path.join(out, "mf-form.json")))

    def test_hash_change(self):
        out = self.made()
        p = os.path.join(out, "mf-form.json")
        wtext(p, " ", "a")
        code, _, se = self.cli("delete", "--out", out)
        self.assertEqual(code, 1)
        self.assertIn("content changed", se)
        self.assertTrue(os.path.exists(p))  # nothing deleted
        self.assertEqual(self.cli("delete", "--out", out, "--force-hash")[0], 0)
        self.assertFalse(os.path.exists(out))

    def test_symlink_in_folder(self):
        out = self.made()
        victim = os.path.join(self.t, "victim.txt")
        wtext(victim, "precious")
        p = os.path.join(out, "mf-form.json")
        os.unlink(p)
        os.symlink(victim, p)
        for extra in ((), ("--force-hash",), ("--no-manifest",)):
            code, _, se = self.cli("delete", "--out", out, *extra)
            self.assertEqual(code, 1)
            self.assertIn("mf-form.json", se)
            self.assertEqual(rtext(victim), "precious")

    def test_symlinked_out_dir_and_manifest_names(self):
        out = self.made()
        link = self.out("link")
        os.symlink(out, link)
        self.assertEqual(self.cli("delete", "--out", link)[0], 1)
        self.assertTrue(os.path.isdir(out))
        # a manifest naming a path outside the folder is refused
        man = jload(out + ".manifest.json")
        man["files"]["../victim.txt"] = "0" * 64
        jdump(man, out + ".manifest.json")
        code, _, se = self.cli("delete", "--out", out)
        self.assertEqual(code, 1)
        self.assertIn("plain file name", se)
        self.assertTrue(os.path.exists(os.path.join(out, "mf-form.json")))

    def test_no_manifest_needs_the_flag(self):
        out = self.made()
        os.unlink(out + ".manifest.json")
        code, _, se = self.cli("delete", "--out", out)
        self.assertEqual(code, 1)
        self.assertIn("--no-manifest", se)
        self.assertTrue(os.path.isdir(out))
        code, _, _ = self.cli("delete", "--out", out, "--no-manifest")
        self.assertEqual(code, 0)
        self.assertFalse(os.path.exists(out))

    def test_no_manifest_refuses_foreign_files(self):
        out = self.made()
        os.unlink(out + ".manifest.json")
        wtext(os.path.join(out, "mine.txt"), "keep")
        code, _, se = self.cli("delete", "--out", out, "--no-manifest")
        self.assertEqual(code, 1)
        self.assertIn("mine.txt", se)
        self.assertTrue(os.path.exists(os.path.join(out, "mf-form.json")))

    def test_manifest_left_without_folder(self):
        out = self.made()
        shutil.rmtree(out)  # as if a fill had stopped between the manifest and the folder
        code, _, _ = self.cli("delete", "--out", out)
        self.assertEqual(code, 0)
        self.assertFalse(os.path.exists(out + ".manifest.json"))

    def test_nothing_there(self):
        self.assertEqual(self.cli("delete", "--out", self.out("none"))[0], 1)


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
        self.assertEqual(s.string("={{ 'k' + $env.MF_CRM_URL }}/p"), "={{ 'k' + \"x\" }}/p")
        self.assertEqual(s.string("={{ $env.DESK_URL }}"), '={{ "a\\"b\\\\c" }}')
        self.assertEqual(
            s.string('={{ "it\'s" }} {{ $env.MF_CRM_URL }}'), '={{ "it\'s" }} {{ "x" }}'
        )
        self.assertEqual(s.bad, set())
        s.string("={{ $env.DESK_NOPE }}")
        self.assertEqual(s.bad, {"DESK_NOPE"})

    def test_token_refusals_in_process(self):
        s = ff.Subst({"DESK_URL": "x"})
        for bad in ("=a $env.DESK_URL", '={{ "$env.DESK_URL" }}', "={{ {{ $env.DESK_URL }}"):
            with self.assertRaises(ff.Refused):
                s.string(bad)
        with self.assertRaises(ff.Refused):
            s.string("return $env.DESK_URL", "jsCode")
        self.assertEqual(s.string("plain $env.DESK_URL", "other"), "plain x")

    def test_exit_codes_are_literal(self):
        self.assertEqual(run()[0], 2)  # command-line mistake
        self.assertEqual(run("fill", "--in", self.t)[0], 2)
        self.assertEqual(ff.EXIT_OK, 0)
        self.assertEqual(ff.EXIT_REFUSED, 1)
        self.assertEqual(ff.EXIT_NOTHING, 4)

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
        rnd = random.Random(7)  # noqa: S311 - test data only
        alphabet = "ab\"\\{}$'`/:.%\u00e9\u4e2d "
        for _ in range(200):
            v = "".join(rnd.choice(alphabet) for _ in range(rnd.randint(1, 12)))
            if "$env" in v:
                continue
            lit = ff._js_literal(v)
            self.assertNotIn("}}", lit)
            self.assertEqual(json.loads(lit.replace("\\u007b", "{").replace("\\u007d", "}")), v)


if __name__ == "__main__":
    unittest.main()
