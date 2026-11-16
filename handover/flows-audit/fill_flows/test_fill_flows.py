"""Self-test with made-up values only. Run: python -m unittest -v (in this folder)."""

from __future__ import annotations

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
NOT_READY = getattr(ff, "NOT_READY_NAME", "NOT-READY-DO-NOT-IMPORT.txt")
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


def stat_is(st, kind):
    import stat as _s

    return (_s.S_ISREG if kind == "reg" else _s.S_ISDIR)(st.st_mode)


def rtext(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def jload(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def jdump(obj, path):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh)


def wtext_read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def wtext(path, text, mode="w"):
    with open(path, mode, encoding="utf-8") as fh:
        fh.write(text)


def run_cli(*args):
    """Run the CLI as a subprocess; returns (code, stdout, stderr)."""
    p = subprocess.run(  # noqa: S603
        [sys.executable, "-I", os.path.join(HERE, "fill_flows.py"), *args],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    return p.returncode, p.stdout, p.stderr


WRITTEN: list[str] = []  # every value written by write_values; no output may show one


def write_values(path, vals):
    WRITTEN.extend(v for v in vals.values() if len(v) >= 4)
    with open(path, "w") as fh:
        fh.write("# made-up\n" + "".join(f"{k}={v}\n" for k, v in vals.items()))
    os.chmod(path, 0o600)


def write_raw(path, text, values=(), mode="w"):
    """Write a hand-made values file (odd bytes, no line-end change) and register every value in
    it, so the screen-output check also looks for it. Every raw write in this file goes here."""
    WRITTEN.extend(v for v in values if len(v) >= 4)
    with open(path, mode, newline="" if mode == "w" else None) as fh:
        fh.write(text)


def raw_values_text(**kv):
    """KEY=VALUE lines for the six made-up flow keys, with `kv` replacing some values."""
    return "".join(f"{k}={kv.get(k, v)}\n" for k, v in VALS.items())


def forms(v):
    """A value as it could show up on screen: plain, escaped as JSON (with and without
    \\uXXXX for non-ASCII), or as a Python literal."""
    return {
        v,
        json.dumps(v)[1:-1],
        json.dumps(v, ensure_ascii=False)[1:-1],
        ascii(v)[1:-1],
        repr(v)[1:-1],
    }


def tree_hash(d):
    out = {}
    for n in sorted(os.listdir(d)):
        if n == ff.MARKER_NAME:  # holds the folder name, so it differs between folders
            continue
        with open(os.path.join(d, n), "rb") as fh:
            out[n] = hashlib.sha256(fh.read()).hexdigest()
    return out


def all_strings(folder):
    found = set()
    for n in os.listdir(folder):
        if n in (ff.MARKER_NAME, NOT_READY):
            continue
        found.update(ff.iter_strings(jload(os.path.join(folder, n))))
    return found


class Base(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.mkdtemp(prefix="ff13-", dir=os.environ.get("FF_TEST_BASE"))
        self.addCleanup(shutil.rmtree, self.t, True)
        WRITTEN.clear()
        self.vf = os.path.join(self.t, "flow-values.env")
        write_values(self.vf, VALS)
        self.nflow = 0

    def leak_check(self, so, se):
        for v in (*VALS.values(), *PH_VALS.values(), *WRITTEN):
            for f in forms(v):
                self.assertNotIn(f, so, "a value reached stdout")
                self.assertNotIn(f, se, "a value reached stderr")

    strict = False  # True: the fill runs as a person types it (no --allow-placeholders added)

    def _lenient(self, args):
        """Most tests exercise the NOT READY copy, so `fill` gets --allow-placeholders unless the
        test sets `strict`."""
        if args and args[0] == "fill" and not self.strict and "--allow-placeholders" not in args:
            return (*args, "--allow-placeholders")
        return args

    def cli(self, *args):
        """Run the CLI; fail the test if ANY made-up value shows in stdout or stderr."""
        code, so, se = run_cli(*self._lenient(args))
        self.leak_check(so, se)
        return code, so, se

    def inproc(self, *args):
        """Same as cli, but in this process (so a test can patch the module)."""
        bo, be = io.StringIO(), io.StringIO()
        with redirect_stdout(bo), redirect_stderr(be):
            code = ff.main(list(self._lenient(args)))
        self.leak_check(bo.getvalue(), be.getvalue())
        return code, bo.getvalue(), be.getvalue()

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
            self.assertEqual(code, 3, se)  # written, but placeholders are left
            self.assertEqual(
                sorted(os.listdir(out)), sorted([*os.listdir(src), ff.MARKER_NAME, NOT_READY])
            )
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
            self.assertIn("NOT READY TO IMPORT: ", se)
            self.assertNotIn("NOT READY", so)
            # source untouched
            self.assertIn("$env", rtext(os.path.join(src, "mf-sub-crm-mail.json")))

    def test_real_expressions(self):
        src = self.copy_flows("real")
        out = self.out()
        self.assertEqual(self.fill(src=src, out=out)[0], 3)
        found = all_strings(out)
        self.assertIn("={{ " + json.dumps(URL) + " }}/qualify", found)
        self.assertIn('={{ Number("2500" || 10000) }}', found)
        self.assertIn("={{ " + json.dumps(VALS["DESK_ALERT_TO"]) + " }}", found)

    def test_film_expressions(self):
        src = self.copy_flows("film")
        out = self.out()
        self.assertEqual(self.fill(src=src, out=out)[0], 3)
        found = all_strings(out)
        self.assertIn('={{ "http://127.0.0.1:9/stage" }}/qualify', found)
        self.assertIn('={{ Number("3000" || 10000) }}', found)
        self.assertIn('={{ "http://127.0.0.1:9/crm" }}/upsert', found)

    def test_token_in_every_location(self):
        # expressions are filled anywhere; a plain text only in the listed address fields
        top = {
            "pinData": {
                "n1": [{"json": {"u": "={{ $env.DESK_URL }}", "toEmail": "x $env.DESK_ALERT_TO"}}]
            },
        }
        params = {
            "url": "plain $env.DESK_URL",
            "lst": ["={{ $env.DESK_URL }}", ["={{ $env.DESK_URL }}"]],
            "fromEmail": ["a $env.DESK_ALERT_TO"],
            "ccEmail": "b $env.DESK_TIMEOUT_MS",
        }
        src = self.flow_dir(params, top)
        self.assertEqual(self.cli("check", src, "--tokens-only")[0], 1)
        out = self.out()
        code, _, se = self.fill(src=src, out=out)
        self.assertEqual(code, 0, se)
        found = all_strings(out)
        self.assertFalse([t for t in found if "$env" in t])
        for want in (
            "plain " + URL,
            "={{ " + json.dumps(URL) + " }}",
            "x " + VALS["DESK_ALERT_TO"],
            "a " + VALS["DESK_ALERT_TO"],
            "b 2500",
        ):
            self.assertIn(want, found)
        self.assertEqual(self.cli("check", out, "--tokens-only")[0], 0)

    def test_plain_token_outside_the_address_fields_is_refused(self):
        # F10: n8n does not evaluate a plain text, so a token there is only meaningful in a
        # literal address field. The real v5 flows hold none in a plain text (see PLAIN_KEYS).
        for params in (
            {"u": "x $env.DESK_URL"},
            {"name": "$env.DESK_URL"},
            {"credentials": {"c": {"id": "1", "name": "cred $env.DESK_ALERT_TO"}}},
            {"lst": ["plain $env.DESK_TIMEOUT_MS"]},
            {"k $env.DESK_URL": 1},
            {"jsonBody": '{"a": "$env.DESK_URL"}'},
        ):
            se = self.refuse(params, "plain text")
            self.assertNotIn(CANARY, se)
        se = self.refuse({"u": "x $env.DESK_URL"}, "field u")
        self.assertIn("key name", self.refuse({"k $env.DESK_URL": 1}, "key name"))
        self.assertNotIn("PATH", se)

    def test_real_flows_hold_no_plain_token(self):
        # the reason the list of plain fields may be this short: count them in the real flows
        for flavor in ("real", "film"):
            src = self.copy_flows(flavor)
            for n in os.listdir(src):
                for t in ff.iter_strings(jload(os.path.join(src, n))):
                    if "$env" in t:
                        self.assertTrue(t.startswith("="), (n, "plain token in a real flow"))

    def test_idempotent_same_bytes(self):
        src = self.copy_flows("film")
        o1, o2 = self.out("a"), self.out("b")
        self.assertEqual(self.fill(src=src, out=o1)[0], 3)
        self.assertEqual(self.fill(src=src, out=o2)[0], 3)
        self.assertEqual(tree_hash(o1), tree_hash(o2))
        m1, m2 = jload(o1 + ".manifest.json"), jload(o2 + ".manifest.json")
        m1["files"].pop(ff.MARKER_NAME)  # the marker holds the folder name
        m2["files"].pop(ff.MARKER_NAME)
        self.assertEqual(m1, m2)

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
        code, _, se = self.fill(src=src, out=out1)
        self.assertEqual(code, 3)
        self.assertIn(f"NOT READY TO IMPORT: {left} placeholders left", se)
        write_values(self.vf, {**VALS, **PH_VALS})
        out2 = self.out("two")
        code, so, se = self.fill(src=src, out=out2)
        self.assertEqual(code, 0, se)
        self.assertNotIn("NOT READY", so + se)
        found = all_strings(out2)
        self.assertFalse([t for t in found if t in ff.PLACEHOLDERS])
        self.assertIn("phv-pg-1", found)
        self.assertIn(PH_VALS["FROM_ADDRESS_PLACEHOLDER"], found)
        self.assertEqual(self.cli("check", out2)[0], 0)
        self.assertEqual(self.cli("check", out1)[0], 1)

    def test_check_mode(self):
        src = self.copy_flows("real")
        code, so, _ = self.cli("check", src)
        self.assertEqual(code, 1)
        for w in ("DESK_URL", "DESK_ALERT_TO", "SUB_WORKFLOW_ID", "PG_CREDENTIAL_ID"):
            self.assertIn(w, so)
        out = self.out()
        self.fill(src=src, out=out)
        code, so, _ = self.cli("check", out, "--tokens-only")
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
        code, so, _ = self.cli("check", d)
        self.assertEqual(code, 1)
        self.assertIn("token $env DESK_URL", so)
        self.assertIn("token $env DESK_TIMEOUT_MS", so)
        self.assertIn("1 other $env use", so)
        self.assertIn("3 problem(s)", so)

    def test_check_bad_json_and_nan(self):
        d = self.flow_dir({})
        wtext(os.path.join(d, "bad.json"), "{nope")
        wtext(os.path.join(d, "nan.json"), '{"nodes": [], "x": NaN}')
        code, so, _ = self.cli("check", d)
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
        self.assertEqual(code, 3)
        self.assertIn("MF_UNUSED_KEY", se)
        self.assertNotIn("abc", se.replace("MF_UNUSED_KEY", ""))

    def test_other_name_refused_even_with_value(self):
        # a clean flow, so the refusal can only come from the name rule
        self.refuse({"url": "$env.PATH"}, "PATH", vals={**VALS, "PATH": "/opt/pathv-q9k"})

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

    def test_nested_template_refused(self):
        # F1: a template inside ${ } makes the backtick toggle see the token as "outside"; the
        # token is really inside a template string. Any token in a part with ` or ${ is refused.
        for expr in (
            "={{ `${ `a $env.DESK_URL` }` }}",
            "={{ `${ `a` }` + $env.DESK_URL }}",
            "={{ `${ `${ `$env.DESK_URL` }` }` }}",
            "={{ $env.DESK_URL + '${' }}",
            '={{ $env.DESK_URL + "`" }}',
        ):
            self.refuse({"u": expr}, "not filled")
        s = ff.Subst({"DESK_URL": "x"})
        self.assertEqual(s.string("={{ `t` + 1 }}"), "={{ `t` + 1 }}")  # no token: untouched

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
        self.assertEqual(self.fill(src=src, out=o)[0], 3)
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
            write_raw(self.vf, raw_values_text(DESK_URL=bad), [bad])
            code, so, se = self.fill()
            self.assertEqual(code, 1, repr(bad))
            self.assertIn(msg, se, repr(bad))
            self.assertIn("DESK_URL" if "line 2" not in msg else "values file", se)
            self.assertFalse(os.path.exists(self.out()))
            self.assertNotIn(bad.strip(), (so + se).replace("DESK_URL", ""), repr(bad))

    def test_quote_and_backslash_in_middle_are_escaped(self):
        for bad in ('has"quote', "back\\slash", "it's"):
            write_raw(self.vf, raw_values_text(DESK_URL=bad), [bad])
            code = self.fill()[0]
            self.assertEqual(code, 3, bad)
            self.assertIn("={{ " + json.dumps(bad) + " }}/qualify", all_strings(self.out()))
            shutil.rmtree(self.out())
            os.unlink(self.out() + ".manifest.json")

    def test_inline_comment_marker_warns(self):
        write_values(self.vf, {**VALS, "MF_CRM_URL": "http://127.0.0.1:9/crm #old"})
        code, _, se = self.fill()
        self.assertEqual(code, 3)
        self.assertIn("value of MF_CRM_URL contains ' #'", se)

    def test_bom_refused(self):
        write_raw(self.vf, b"\xef\xbb\xbf" + b"DESK_URL=x\n", mode="wb")
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
        write_raw(self.vf, "DESK_URL=a\nDESK_URL=b\n")
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

        def flaky(path, data, dir_fd, *rest):
            calls.append(os.path.basename(path))
            if len(calls) == 3:
                # F2: the text of the error holds a made-up value; it must never be printed
                raise OSError("disk full (test) " + CANARY)
            return real(path, data, dir_fd, *rest)

        WRITTEN.append(CANARY)
        out = self.out()
        with mock.patch.object(ff, "_write_new", flaky):
            code, _, se = self.inproc(
                "fill", "--in", self.copy_flows("real"), "--values", self.vf, "--out", out
            )
        self.assertEqual(code, 1)
        self.assertIn("failed: OSError", se)
        self.assertNotIn("disk full", se)  # the error text is never printed
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
        # F5: a second delete (or a typo) is not an error; it says plainly that nothing is there
        code, so, _ = self.cli("delete", "--out", self.out("none"))
        self.assertEqual((code, "nothing to delete" in so), (0, True), so)
        out = self.made()
        self.assertEqual(self.cli("delete", "--out", out)[0], 0)
        code, so, _ = self.cli("delete", "--out", out)  # the same command again
        self.assertEqual((code, "nothing to delete" in so), (0, True), so)


class Unit(Base):
    def test_token_forms(self):
        s = ff.Subst({"DESK_URL": 'a"b\\c', "MF_CRM_URL": "x"})
        self.assertEqual(s.string("$env.DESK_URL", None, "url"), 'a"b\\c')  # plain field: raw text
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
        self.assertEqual(s.string("plain $env.DESK_URL", "other", "url"), "plain x")
        with self.assertRaises(ff.Refused):
            s.string("plain $env.DESK_URL", "other", "name")

    def test_exit_codes_are_literal(self):
        self.assertEqual(self.cli()[0], 2)  # command-line mistake
        self.assertEqual(self.cli("fill", "--in", self.t)[0], 2)
        self.assertEqual(ff.EXIT_OK, 0)
        self.assertEqual(ff.EXIT_REFUSED, 1)
        self.assertEqual(ff.EXIT_INCOMPLETE, 3)
        self.assertEqual(ff.EXIT_NOTHING, 4)

    def test_values_never_in_messages_in_process(self):
        write_raw(self.vf, "DESK_URL=" + CANARY + "\r\n", [CANARY])
        code, so, se = self.inproc(
            "fill", "--in", self.copy_flows("real"), "--values", self.vf, "--out", self.out()
        )
        self.assertEqual(code, 1)
        self.assertNotIn(CANARY, so + se)

    def test_property_roundtrip_random_values(self):
        alphabet = "ab\"\\{}$'`/:.%\u00e9\u4e2d "
        for seed in range(5):  # five fixed seeds, not one
            rnd = random.Random(seed)  # noqa: S311 - test data only
            for _ in range(200):
                v = "".join(rnd.choice(alphabet) for _ in range(rnd.randint(1, 12)))
                if "$env" in v:
                    continue
                lit = ff._js_literal(v)
                self.assertNotIn("}}", lit)
                back = json.loads(lit.replace("\\u007b", "{").replace("\\u007d", "}"))
                self.assertEqual(back, v)


class Hardening(Base):
    """Review round 2: exit code 3, the no-manifest signature, cleanup of a stub, and more."""

    def made(self):
        out = self.out()
        self.fill(src=self.copy_flows("film"), out=out)
        return out

    def raw_values(self, **kv):
        write_raw(self.vf, raw_values_text(**kv), list(kv.values()))

    # ---- M2: written but incomplete
    def test_placeholder_inside_longer_string_counts(self):
        d = self.flow_dir({"to": "Name <FROM_ADDRESS_PLACEHOLDER>", "url": "$env.DESK_URL"})
        out = self.out()
        code, so, se = self.fill(src=d, out=out)
        self.assertEqual(code, 3)
        self.assertIn("NOT READY TO IMPORT: 1 placeholders left", se)
        self.assertNotIn("NOT READY", so)
        self.assertTrue(os.path.isdir(out))  # the copy is written; it is just not ready
        code, so, _ = self.cli("check", out)
        self.assertEqual(code, 1)
        self.assertIn("placeholder FROM_ADDRESS_PLACEHOLDER x1", so)

    def test_exit_0_only_when_nothing_is_left(self):
        d = self.flow_dir({"url": "$env.DESK_URL"})
        self.assertEqual(self.fill(src=d)[0], 0)

    # ---- M4: platform
    def test_platform_check_refuses_plainly(self):
        d = self.flow_dir({"u": "$env.DESK_URL"})
        with mock.patch.object(ff, "HAS_NOFOLLOW", False):
            code, so, se = self.inproc("check", d)
        self.assertEqual(code, 1)
        self.assertIn("Linux, macOS or WSL", se)
        self.assertEqual(so, "")

    # ---- M1 / F3: --no-manifest needs the tool's signature
    def test_no_manifest_refuses_a_plain_input_folder(self):
        src = self.copy_flows("real")  # modes 0755 / 0644, still holds $env text
        before = tree_hash(src)
        code, _, se = self.cli("delete", "--out", src, "--no-manifest")
        self.assertEqual(code, 1)
        self.assertIn("not marked as this tool's output", se)
        self.assertEqual(tree_hash(src), before)

    def test_no_manifest_refuses_wrong_file_mode_folder_mode_and_owner(self):
        out = self.made()
        os.unlink(out + ".manifest.json")
        p = os.path.join(out, "mf-form.json")
        os.chmod(p, 0o644)
        code, _, se = self.cli("delete", "--out", out, "--no-manifest")
        self.assertEqual((code, "mf-form.json" in se), (1, True))
        os.chmod(p, 0o600)
        os.chmod(out, 0o500)
        code, _, se = self.cli("delete", "--out", out, "--no-manifest")
        self.assertEqual(
            (code, "mode 0700 and yours" in se), (1, True), se
        )  # the check, not EACCES
        os.chmod(out, 0o700)
        with mock.patch.object(ff.os, "getuid", return_value=os.getuid() + 1):
            code, _, se = self.inproc("delete", "--out", out, "--no-manifest")
        self.assertEqual((code, "mode 0700 and yours" in se), (1, True), se)
        self.assertEqual(len(os.listdir(out)), 6)
        self.assertEqual(self.cli("delete", "--out", out, "--no-manifest")[0], 0)

    def test_no_manifest_refuses_non_json_and_env_text(self):
        out = self.made()
        os.unlink(out + ".manifest.json")
        p = os.path.join(out, "mf-form.json")
        wtext(p, "{cut short")
        code, _, se = self.cli("delete", "--out", out, "--no-manifest")
        self.assertEqual((code, "does not parse as JSON" in se), (1, True))
        self.assertTrue(os.path.exists(p))
        wtext(p, '{"nodes": [], "u": "$env.DESK_URL"}')
        code, _, se = self.cli("delete", "--out", out, "--no-manifest")
        self.assertEqual((code, "holds $env text" in se), (1, True))
        wtext(p, "{cut short")  # a killed run leaves a cut file: --force-hash allows it
        self.assertEqual(self.cli("delete", "--out", out, "--no-manifest", "--force-hash")[0], 0)
        self.assertFalse(os.path.exists(out))

    def test_symlinked_out_dir_with_no_manifest_and_with_copied_manifest(self):
        out = self.made()
        link = self.out("link")
        os.symlink(out, link)
        code, _, se = self.cli("delete", "--out", link, "--no-manifest")
        self.assertEqual((code, "symlink" in se), (1, True))
        shutil.copy(out + ".manifest.json", link + ".manifest.json")
        self.assertEqual(self.cli("delete", "--out", link)[0], 1)
        self.assertEqual(len(os.listdir(out)), 6)
        self.assertTrue(os.path.exists(out + ".manifest.json"))

    def test_delete_of_a_half_filled_folder(self):
        out = self.made()
        os.unlink(os.path.join(out, "mf-form.json"))
        code, so, _ = self.cli("delete", "--out", out)
        self.assertEqual((code, "deleted 3 files" in so), (0, True))
        self.assertFalse(os.path.exists(out + ".manifest.json"))

    # ---- F1: a cut file made by this run is removed
    def test_write_cut_in_the_middle_leaves_nothing_and_rerun_works(self):
        real_fdopen = os.fdopen
        count = {"n": 0}

        class Half:
            def __init__(self, fh):
                self.fh = fh

            def __enter__(self):
                return self

            def __exit__(self, *_a):
                self.fh.close()
                return False

            def write(self, data):
                self.fh.write(data[:10])
                self.fh.flush()
                raise OSError("disk full (test)")

        def fake(fd, mode="r", *a, **k):
            fh = real_fdopen(fd, mode, *a, **k)
            if mode == "wb":
                count["n"] += 1
                if count["n"] == 3:  # manifest, first file, then a file cut in the middle
                    return Half(fh)
            return fh

        out, src = self.out(), self.copy_flows("real")
        args = ("fill", "--in", src, "--values", self.vf, "--out", out)
        with mock.patch.object(ff.os, "fdopen", fake):
            code, _, se = self.inproc(*args)
        self.assertEqual((code, "failed: OSError" in se), (1, True))
        self.assertFalse(os.path.exists(out))
        self.assertFalse(os.path.exists(out + ".manifest.json"))
        self.assertEqual(self.inproc(*args)[0], 3)  # the re-run is not blocked
        self.assertEqual(len(os.listdir(out)), 6)

    # ---- F5: forms and values
    def test_odd_spellings(self):
        self.refuse({"u": "={{ $env . DESK_URL }}"}, "$env token is left")
        self.refuse({"u": "={{ /* c */ $env.DESK_URL }}"}, "comment")
        self.refuse({"u": "={{ // c\n$env.DESK_URL }}"}, "comment")
        s = ff.Subst({"DESK_URL": "x"})
        self.assertEqual(s.string('={{ "$" + "env.DESK_URL" }}'), '={{ "$" + "env.DESK_URL" }}')

    def test_more_bad_values(self):
        for bad, msg in {
            "nel\x85x": "control or line-break",
            "=1+1": "starts with '='",
        }.items():
            self.raw_values(DESK_URL=bad)
            code, so, se = self.fill()
            self.assertEqual(code, 1, repr(bad))
            self.assertIn(msg, se)
            self.assertNotIn(bad, so + se)

    def test_values_file_mode_0604_refused(self):
        os.chmod(self.vf, 0o604)
        code, _, se = self.fill()
        self.assertEqual((code, "chmod 600" in se), (1, True))

    # ---- F7, F8
    def test_check_on_empty_folder_fails(self):
        d = os.path.join(self.t, "empty")
        os.mkdir(d)
        code, _, se = self.cli("check", d)
        self.assertEqual((code, "no .json files" in se), (1, True))

    def test_output_inside_input_refused(self):
        src = self.copy_flows("real")
        for sub in ("o", os.path.join("a", "o")):
            os.makedirs(os.path.join(src, os.path.dirname(sub)), exist_ok=True)
            code, _, se = self.fill(src=src, out=os.path.join(src, sub))
            self.assertEqual((code, "inside it" in se), (1, True))
            self.assertFalse(os.path.exists(os.path.join(src, sub)))
        self.assertEqual(self.fill(src=src, out=src)[0], 1)

    # ---- F10: a regex or division next to a token
    def test_slash_outside_a_string_refused(self):
        self.refuse({"u": "={{ /x/.test($env.DESK_URL) }}"}, "'/' outside a string")
        self.refuse({"u": "={{ /'/.test('a') + $env.DESK_URL }}"})  # mis-lexed quote: refused
        self.refuse({"u": "={{ $env.DESK_TIMEOUT_MS / 2 }}"}, "'/' outside a string")

    # ---- N2: a code key higher up still counts
    def test_code_key_carried_down(self):
        self.refuse({"jsCode": {"a": {"b": "return $env.DESK_URL"}}}, "jsCode")
        self.refuse({"pythonCode": [{"b": ["x $env.DESK_URL"]}]}, "pythonCode")

    # ---- N4: digits only, trailing slash
    def test_ms_keys_digits_only(self):
        for bad in ("25s", "-5", "2500.5", "\uff12\uff15", "1e3", "0x10"):
            self.raw_values(DESK_TIMEOUT_MS=bad)
            code, _, se = self.fill()
            self.assertEqual((code, "digits only" in se), (1, True), repr(bad))
            self.assertFalse(os.path.exists(self.out()))

    def test_trailing_slash_in_url_warns(self):
        self.raw_values(DESK_URL="http://127.0.0.1:9/")
        code, _, se = self.fill()
        self.assertEqual(code, 3)
        self.assertIn("value of DESK_URL ends with '/'", se)

    # ---- round 3: tests for the four surviving hand mutants and the symlinked parent
    def test_no_manifest_force_hash_refuses_a_folder_named_like_a_json_file(self):
        # kills "S_ISREG removed": a folder x.json (mode 0600) passes the mode check and, with
        # --force-hash, the read check; without the plain-file check unlink would fail half way.
        out = self.made()
        os.unlink(out + ".manifest.json")
        os.mkdir(os.path.join(out, "zz.json"), 0o600)
        for extra in ((), ("--force-hash",)):
            code, _, se = self.cli("delete", "--out", out, "--no-manifest", *extra)
            self.assertEqual((code, "not a plain .json file" in se), (1, True), se)
            self.assertEqual(len(os.listdir(out)), 7)  # nothing was deleted

    def test_no_manifest_refuses_a_fifo_without_hanging(self):
        out = self.made()
        os.unlink(out + ".manifest.json")
        os.mkfifo(os.path.join(out, "zz.json"), 0o600)
        code, _, se = self.cli("delete", "--out", out, "--no-manifest", "--force-hash")
        self.assertEqual((code, "not a plain .json file" in se), (1, True), se)
        self.assertEqual(len(os.listdir(out)), 7)

    def test_fill_names_a_leftover_manifest_plainly(self):
        # kills "manifest-exists refusal removed": without it the O_EXCL write fails with an
        # unhelpful "failed: FileExistsError"
        out = self.out()
        man = out + ".manifest.json"
        wtext(man, "keep me")
        code, _, se = self.fill(out=out)
        self.assertEqual((code, "already exists" in se, "failed" in se), (1, True, False), se)
        self.assertEqual(rtext(man), "keep me")
        self.assertFalse(os.path.exists(out))

    def test_fill_into_a_symlink_that_points_into_git_names_the_real_cause(self):
        # the link itself is the refusal (it exists); no folder is made in the git folder
        repo = os.path.join(self.t, "repo")
        os.makedirs(os.path.join(repo, ".git"))
        link = self.out("lnk")
        os.symlink(repo, link)
        code, _, se = self.fill(out=link)
        self.assertEqual((code, "already exists" in se), (1, True), se)
        self.assertEqual(os.listdir(repo), [".git"])

    def test_delete_no_manifest_refuses_a_symlink_or_folder_in_the_manifest_place(self):
        # kills "manifest-is-symlink check removed" on delete
        for kind in ("link", "dir"):
            out = self.made()
            os.unlink(out + ".manifest.json")
            victim = os.path.join(self.t, "victim-" + kind)
            wtext(victim, "precious")
            if kind == "link":
                os.symlink(victim, out + ".manifest.json")
            else:
                os.mkdir(out + ".manifest.json")
            for extra in ((), ("--force-hash",)):
                code, _, se = self.cli("delete", "--out", out, "--no-manifest", *extra)
                self.assertEqual((code, "manifest is a symlink or not a file" in se), (1, True))
                self.assertEqual(len(os.listdir(out)), 6)  # nothing deleted
            self.assertEqual(rtext(victim), "precious")
            if kind == "link":
                os.unlink(out + ".manifest.json")
            else:
                os.rmdir(out + ".manifest.json")
            shutil.rmtree(out)

    # ---- round 3: a symlinked output parent
    def test_symlinked_parent_of_my_own_is_accepted_and_works_end_to_end(self):
        real = os.path.join(self.t, "real-parent")
        os.mkdir(real, 0o700)
        link = os.path.join(self.t, "link-parent")
        os.symlink(real, link)
        out = os.path.join(link, "sub")
        self.assertEqual(self.fill(out=out)[0], 3)
        self.assertEqual(sorted(os.listdir(real)), ["sub", "sub.manifest.json"])
        self.assertEqual(self.cli("delete", "--out", out)[0], 0)
        self.assertEqual(os.listdir(real), [])

    def test_symlinked_parent_made_by_another_user_is_refused(self):
        real = os.path.join(self.t, "real-parent")
        os.mkdir(real, 0o700)
        link = os.path.join(self.t, "link-parent")
        os.symlink(real, link)
        out = os.path.join(link, "sub")
        real_lstat = os.lstat

        def other_owner(path, *a, **k):
            st = real_lstat(path, *a, **k)
            if os.fspath(path) == link:
                return os.stat_result((st.st_mode,) + tuple(st)[1:4] + (4242,) + tuple(st)[5:])
            return st

        with mock.patch.object(ff.os, "lstat", other_owner):
            code, _, se = self.inproc(
                "fill", "--in", self.copy_flows("real"), "--values", self.vf, "--out", out
            )
            self.assertEqual((code, "symlink made by another user" in se), (1, True), se)
            self.assertEqual(os.listdir(real), [])
            self.assertEqual(self.inproc("delete", "--out", out)[0], 1)

    # ---- round 4: tests for three more surviving mutants
    def test_values_file_must_be_a_regular_file(self):
        d = os.path.join(self.t, "vdir")
        os.mkdir(d, 0o700)
        code, _, se = self.fill(vf=d)
        self.assertEqual((code, "not a regular file" in se), (1, True), se)
        self.assertFalse(os.path.exists(self.out()))

    def test_delete_refuses_a_parent_link_made_by_another_user(self):
        real = os.path.join(self.t, "real-parent")
        os.mkdir(real, 0o700)
        link = os.path.join(self.t, "link-parent")
        os.symlink(real, link)
        self.assertEqual(self.fill(out=os.path.join(real, "sub"))[0], 3)
        real_lstat = os.lstat

        def other_owner(path, *a, **k):
            st = real_lstat(path, *a, **k)
            if os.fspath(path) == link:
                return os.stat_result((st.st_mode,) + tuple(st)[1:4] + (4242,) + tuple(st)[5:])
            return st

        with mock.patch.object(ff.os, "lstat", other_owner):
            code, _, se = self.inproc("delete", "--out", os.path.join(link, "sub"))
        self.assertEqual((code, "symlink made by another user" in se), (1, True), se)
        self.assertEqual(sorted(os.listdir(real)), ["sub", "sub.manifest.json"])
        self.assertEqual(len(os.listdir(os.path.join(real, "sub"))), 6)

    def test_check_reports_every_one_of_the_six_placeholder_names(self):
        for name in ff.PLACEHOLDERS:
            d = self.flow_dir({"a": name})
            code, so, _ = self.cli("check", d)
            self.assertEqual((code, f"placeholder {name} x1" in so), (1, True), name)

    # ---- round 4: values file must be a regular file (a pipe must not hang the tool)
    def test_values_file_pipe_is_refused_without_hanging(self):
        fifo = os.path.join(self.t, "vpipe")
        os.mkfifo(fifo, 0o600)
        code, _, se = self.fill(vf=fifo)
        self.assertEqual((code, "not a regular file" in se), (1, True), se)
        self.assertFalse(os.path.exists(self.out()))

    # ---- security review M1: modes are checked on the written file and folder
    def _fake_modes(self, kind):
        real = os.fstat

        def fake(fd):
            st = real(fd)
            if kind == "file" and stat_is(st, "reg") and st.st_size == 0:
                return os.stat_result((st.st_mode | 0o077,) + tuple(st)[1:])
            if kind == "dir" and stat_is(st, "dir"):
                return os.stat_result((st.st_mode | 0o077,) + tuple(st)[1:])
            return st

        return fake

    def test_modes_that_do_not_hold_on_the_disk_refuse_and_leave_nothing(self):
        for kind in ("file", "dir"):
            out = self.out(kind)
            with mock.patch.object(ff.os, "fstat", self._fake_modes(kind)):
                code, _, se = self.inproc(
                    "fill", "--in", self.copy_flows("real"), "--values", self.vf, "--out", out
                )
            self.assertEqual((code, "modes do not hold" in se), (1, True), (kind, se))
            self.assertFalse(os.path.exists(out), kind)
            self.assertFalse(os.path.exists(out + ".manifest.json"), kind)

    # ---- security review M2: the folder is opened once; swapping the path later changes nothing
    def test_fill_folder_swapped_for_a_link_after_mkdir_writes_nothing_there(self):
        victim = os.path.join(self.t, "victim")
        os.mkdir(victim)
        out = self.out()
        real_mkdir = os.mkdir

        def swap(path, mode=0o777, *, dir_fd=None):
            real_mkdir(path, mode, dir_fd=dir_fd)
            if os.path.basename(str(path)) == "out":
                os.rmdir(os.path.join(self.t, "out"))
                os.symlink(victim, os.path.join(self.t, "out"))

        with mock.patch.object(ff.os, "mkdir", swap):
            code, _, _ = self.inproc(
                "fill", "--in", self.copy_flows("real"), "--values", self.vf, "--out", out
            )
        self.assertEqual(code, 1)
        self.assertEqual(os.listdir(victim), [])

    def test_delete_path_swapped_for_a_link_after_opening_leaves_the_decoy_alone(self):
        out = self.made()
        decoy = os.path.join(self.t, "decoy")
        shutil.copytree(out, decoy)
        before = tree_hash(decoy)
        real_listdir = os.listdir

        def swap(arg):
            res = real_listdir(arg)
            if isinstance(arg, int):  # the folder was opened once; now swap the path
                os.rename(out, out + ".moved")
                os.symlink(decoy, out)
            return res

        with mock.patch.object(ff.os, "listdir", swap):
            self.inproc("delete", "--out", out)
        self.assertEqual(tree_hash(decoy), before)

    # ---- security review M3: --no-manifest needs the marker file
    def test_no_manifest_needs_the_marker_file(self):
        out = self.made()
        os.unlink(out + ".manifest.json")
        marker = os.path.join(out, ff.MARKER_NAME)
        os.unlink(marker)
        code, _, se = self.cli("delete", "--out", out, "--no-manifest", "--force-hash")
        self.assertEqual((code, "no marker file" in se), (1, True), se)
        self.assertEqual(len(os.listdir(out)), 5)

    def test_no_manifest_refuses_a_marker_for_another_folder_or_format(self):
        out = self.made()
        os.unlink(out + ".manifest.json")
        marker = os.path.join(out, ff.MARKER_NAME)
        for text in (
            ff.MARKER_FORMAT + "\nother-name\n",
            "wrong-format\n" + os.path.basename(out) + "\n",
        ):
            os.unlink(marker)
            fd = os.open(marker, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            os.write(fd, text.encode())
            os.close(fd)
            code, _, se = self.cli("delete", "--out", out, "--no-manifest", "--force-hash")
            self.assertEqual((code, "marker file is not" in se), (1, True), se)
            self.assertEqual(len(os.listdir(out)), 6)

    def test_hand_made_folder_of_json_files_is_not_deleted_without_manifest(self):
        d = os.path.join(self.t, "mine")
        os.mkdir(d, 0o700)
        fd = os.open(os.path.join(d, "a.json"), os.O_WRONLY | os.O_CREAT, 0o600)
        os.write(fd, b"{}")
        os.close(fd)
        code, _, _ = self.cli("delete", "--out", d, "--no-manifest", "--force-hash")
        self.assertEqual(code, 1)
        self.assertTrue(os.path.exists(os.path.join(d, "a.json")))

    # ---- security review nits
    def test_names_from_disk_are_printed_safely(self):
        d = os.path.join(self.t, "esc")
        os.mkdir(d)
        name = "mf-\x1b[31mred.json"
        jdump(
            {"nodes": [{"name": "n", "parameters": {"a": "PG_CREDENTIAL_ID"}}]},
            os.path.join(d, name),
        )
        code, so, se = self.cli("check", d)
        self.assertEqual(code, 1)
        self.assertNotIn("\x1b", so + se)
        self.assertIn("\\x1b[31mred.json", so)

    def test_two_keys_that_become_one_are_refused(self):
        write_values(self.vf, {**VALS, "PG_CREDENTIAL_ID": "phv-pg-1"})
        self.refuse({"phv-pg-1": 1, "PG_CREDENTIAL_ID": 2}, "same key")

    def test_placeholder_name_inside_a_code_field_is_refused(self):
        write_values(self.vf, {**VALS, "SMTP_CREDENTIAL_ID": "phv-smtp-2"})
        self.refuse({"jsCode": "SMTP_CREDENTIAL_ID"}, "jsCode")
        se = self.refuse({"jsCode": "return $env.DESK_URL"}, "jsCode")
        self.assertIn("sits in a jsCode field", se)

    def test_no_manifest_with_no_folder_still_validates_the_manifest(self):
        out = self.out()
        wtext(out + ".manifest.json", "not json")
        os.chmod(out + ".manifest.json", 0o600)
        code, _, se = self.cli("delete", "--out", out, "--no-manifest")
        self.assertEqual((code, "not a valid fill_flows manifest" in se), (1, True), se)
        self.assertTrue(os.path.exists(out + ".manifest.json"))

    def test_manifest_delete_refuses_a_folder_that_is_not_yours(self):
        out = self.made()
        real = os.fstat

        def other_dir_owner(fd):
            st = real(fd)
            if stat_is(st, "dir"):
                return os.stat_result(
                    (st.st_mode, *tuple(st)[1:4], os.getuid() + 1, *tuple(st)[5:])
                )
            return st

        with mock.patch.object(ff.os, "fstat", other_dir_owner):
            code, _, se = self.inproc("delete", "--out", out)
        self.assertEqual((code, "folder is not owned by you" in se), (1, True), se)
        self.assertEqual(len(os.listdir(out)), 6)
        with mock.patch.object(ff.os, "getuid", return_value=os.getuid() + 1):
            code, _, se = self.inproc("delete", "--out", out)
        self.assertEqual((code, "not owned by you" in se), (1, True), se)
        self.assertEqual(len(os.listdir(out)), 6)

    # ---- round 6: tests that kill the mutants that survived evidence round 5
    def test_check_refuses_a_not_ready_note_even_with_no_placeholders(self):
        d = os.path.join(self.t, "clean")
        os.mkdir(d)
        jdump({"name": "t", "nodes": [{"name": "n1", "parameters": {}}]}, os.path.join(d, "a.json"))
        self.assertEqual(self.cli("check", d)[0], 0)
        wtext(os.path.join(d, NOT_READY), "not ready")
        code, so, _ = self.cli("check", d)
        self.assertEqual(code, 1, so)
        self.assertIn(f"{NOT_READY} is in the folder", so)
        self.assertIn("1 problem(s)", so)

    def test_delete_never_closes_a_handle_it_did_not_open(self):
        out = self.made()
        os.unlink(out + ".manifest.json")  # refused before the folder is opened
        closed = []
        real_close = os.close

        def spy(fd):
            closed.append(fd)
            if fd > 2:
                real_close(fd)

        with mock.patch.object(ff.os, "close", spy):
            code, _, se = self.inproc("delete", "--out", out)
        self.assertEqual((code, "manifest is missing" in se), (1, True), se)
        self.assertTrue(closed)
        self.assertTrue(all(fd > 2 for fd in closed), closed)

    def _other_owner_files(self):
        real = ff._lstat_or_none

        def other(name, fd):
            st = real(name, fd)
            if st is not None and stat_is(st, "reg"):
                return os.stat_result(
                    (st.st_mode, *tuple(st)[1:4], os.getuid() + 1, *tuple(st)[5:])
                )
            return st

        return mock.patch.object(ff, "_lstat_or_none", other)

    def test_delete_names_a_file_and_a_manifest_that_are_not_yours(self):
        out = self.made()
        with self._other_owner_files():
            code, _, se = self.inproc("delete", "--out", out)
            self.assertEqual((code, ": not owned by you; nothing deleted" in se), (1, True), se)
            code, _, se = self.inproc("delete", "--out", out, "--no-manifest", "--force-hash")
            self.assertEqual((code, "manifest is not owned by you" in se), (1, True), se)
        self.assertEqual(len(os.listdir(out)), 6)

    def test_fill_refuses_a_disk_that_ignores_file_modes_in_plain_words(self):
        real = os.fchmod

        def loosen_folders(fd, mode):
            real(fd, 0o755 if mode == 0o700 else mode)

        with mock.patch.object(ff.os, "fchmod", loosen_folders):
            code, _, se = self.inproc(
                "fill", "--in", self.copy_flows("film"), "--values", self.vf, "--out", self.out()
            )
        self.assertEqual(code, 1, se)
        self.assertIn("file modes do not hold on this disk (the new folder is not private)", se)
        self.assertIn("a normal Linux or macOS disk", se)
        self.assertFalse(os.path.exists(self.out()))

    def test_fd_path_reads_the_macos_place_of_an_open_handle(self):
        class FakeFcntl:
            F_GETPATH = 50

            def __init__(self, reply):
                self.reply = reply

            def fcntl(self, fd, op, buf):
                assert op == self.F_GETPATH
                return self.reply

        def no_proc(_):
            raise OSError

        for reply, want in ((b"/real/place\0junk\0more", "/real/place"), (b"relative\0", "fb")):
            with (
                mock.patch.object(ff.os, "readlink", no_proc),
                mock.patch.dict(sys.modules, {"fcntl": FakeFcntl(reply)}),
            ):
                self.assertEqual(ff._fd_path(3, "fb"), want)

    # ---- security review r3 (findings 1 to 7)
    def full_vals(self):
        write_values(self.vf, {**VALS, **PH_VALS})

    def two_flows(self):
        d = self.flow_dir({"u": "={{ $env.DESK_URL }}"})
        shutil.copy(os.path.join(d, "mf-x.json"), os.path.join(d, "mf-y.json"))
        return d

    def killed_fill(self, sig, kill_at=4):
        """Run a fill in a child process that sends itself `sig` after `kill_at` file writes."""
        driver = (
            "import os, sys, signal\n"
            "sys.path.insert(0, sys.argv[1])\n"
            "import fill_flows as ff\n"
            "real, n = ff._write_new, [0]\n"
            "def w(name, data, fd, created=None):\n"
            "    real(name, data, fd, created)\n"
            "    n[0] += 1\n"
            "    if n[0] == int(sys.argv[2]):\n"
            "        os.kill(os.getpid(), getattr(signal, sys.argv[3]))\n"
            "ff._write_new = w\n"
            "sys.exit(ff.main(['fill', '--in', sys.argv[4], '--values', sys.argv[5],"
            " '--out', sys.argv[6]]))\n"
        )
        out = self.out()
        p = subprocess.run(  # noqa: S603
            [
                sys.executable,
                "-I",
                "-c",
                driver,
                HERE,
                str(kill_at),
                sig,
                self.two_flows(),
                self.vf,
                out,
            ],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        self.leak_check(p.stdout, p.stderr)
        return out, p

    def test_terminate_and_hangup_signals_clean_up_the_copy(self):
        self.full_vals()
        for sig in ("SIGTERM", "SIGHUP"):
            out, p = self.killed_fill(sig)
            self.assertEqual(p.returncode, 1, (sig, p.returncode, p.stderr))
            self.assertFalse(os.path.exists(out), sig)
            self.assertFalse(os.path.exists(out + ".manifest.json"), sig)

    def test_a_kill_that_cannot_be_caught_leaves_a_copy_that_check_refuses(self):
        self.full_vals()
        out, p = self.killed_fill("SIGKILL")
        self.assertEqual(p.returncode, -9)
        self.assertTrue(os.path.isdir(out))
        code, so, _ = self.cli("check", out)
        self.assertEqual(code, 1, so)
        self.assertIn(f"{NOT_READY} is in the folder", so)
        self.assertEqual(self.cli("delete", "--out", out)[0], 0)  # and delete still clears it
        self.assertFalse(os.path.exists(out))

    def test_the_not_ready_note_goes_in_first_and_out_last(self):
        self.full_vals()
        order = []
        real = ff._write_new

        def spy(name, data, fd, created=None):
            order.append(name)
            return real(name, data, fd, created)

        out = self.out()
        with mock.patch.object(ff, "_write_new", spy):
            self.assertEqual(
                self.inproc("fill", "--in", self.two_flows(), "--values", self.vf, "--out", out)[0],
                0,
            )
        self.assertEqual(order[1:3], [NOT_READY, ff.MARKER_NAME])  # manifest, note, marker, files
        self.assertNotIn(NOT_READY, os.listdir(out))  # a complete copy has no note
        self.assertEqual(self.cli("check", out)[0], 0)

    def test_check_compares_the_folder_with_its_manifest(self):
        self.full_vals()
        for damage in ("missing", "extra", "changed", "non-json"):
            out = self.out(damage)
            self.assertEqual(self.fill(src=self.two_flows(), out=out)[0], 0)
            self.assertEqual(self.cli("check", out)[0], 0)
            if damage == "missing":
                os.unlink(os.path.join(out, "mf-y.json"))
            elif damage == "extra":
                jdump({"nodes": []}, os.path.join(out, "z.json"))
            elif damage == "non-json":
                wtext(os.path.join(out, "notes.txt"), "x")
            else:
                with open(os.path.join(out, "mf-y.json"), "ab") as fh:
                    fh.write(b" ")
            code, so, _ = self.cli("check", out)
            self.assertEqual(code, 1, (damage, so))
            self.assertIn("manifest", so, damage)

    def test_fill_refuses_by_default_when_a_placeholder_value_is_missing(self):
        self.strict = True
        out = self.out()
        code, _, se = self.fill(src=self.copy_flows("real"), out=out)
        self.assertEqual(code, 1, se)
        self.assertIn("--allow-placeholders", se)
        self.assertFalse(os.path.exists(out))
        self.assertFalse(os.path.exists(out + ".manifest.json"))
        self.strict = False
        self.assertEqual(self.fill(src=self.copy_flows("real"), out=out)[0], 3)

    def test_delete_no_manifest_keeps_a_file_the_manifest_does_not_list(self):
        self.full_vals()
        out = self.out()
        self.assertEqual(self.fill(src=self.two_flows(), out=out)[0], 0)
        extra = os.path.join(out, "mine.json")
        jdump({"keep": 1}, extra)
        os.chmod(extra, 0o600)
        for flags in (("--no-manifest",), ("--no-manifest", "--force-hash")):
            code, _, se = self.cli("delete", "--out", out, *flags)
            self.assertEqual((code, "not in the manifest" in se), (1, True), se)
            self.assertTrue(os.path.exists(extra))
        code, _, se = self.cli("delete", "--out", out, "--no-manifest-typo")
        self.assertEqual(code, 2)
        os.unlink(os.path.join(out + ".manifest.json"))
        code, _, se = self.cli("delete", "--out", out)
        self.assertEqual(code, 1)
        self.assertIn("only the marker, the not-ready note and .json files", se)
        self.assertNotIn("removes only the files this tool writes", se)

    def test_values_file_must_be_yours(self):
        with mock.patch.object(ff.os, "getuid", return_value=os.getuid() + 1):
            code, _, se = self.inproc(
                "fill", "--in", self.copy_flows("film"), "--values", self.vf, "--out", self.out()
            )
        self.assertEqual((code, "values file is not owned by you" in se), (1, True), se)
        self.assertFalse(os.path.exists(self.out()))

    def _made_real(self):
        out = self.out()
        self.fill(src=self.copy_flows("real"), out=out)
        return out

    def test_delete_takes_the_note_and_the_marker_last(self):
        out = self._made_real()
        order = []
        real = os.unlink

        def spy(name, *a, **k):
            order.append(name)
            return real(name, *a, **k)

        with mock.patch.object(ff.os, "unlink", spy):
            self.assertEqual(self.inproc("delete", "--out", out)[0], 0)
        folder_files = [n for n in order if not n.endswith(".manifest.json")]
        self.assertEqual(folder_files[-2:], [NOT_READY, ff.MARKER_NAME])
        self.assertTrue(order[-1].endswith(".manifest.json"))

    def test_delete_stopped_half_way_leaves_a_marked_folder(self):
        out = self._made_real()
        real, count = os.unlink, [0]

        def stop(name, *a, **k):
            count[0] += 1
            if count[0] == 2:
                raise KeyboardInterrupt
            return real(name, *a, **k)

        with mock.patch.object(ff.os, "unlink", stop):
            with self.assertRaises(KeyboardInterrupt):
                self.inproc("delete", "--out", out)
        self.assertIn(ff.MARKER_NAME, os.listdir(out))  # still marked: a re-run finds it
        self.assertEqual(self.cli("delete", "--out", out)[0], 0)
        self.assertFalse(os.path.exists(out))

    def test_escaped_spellings_of_the_env_name_are_refused(self):
        for esc in (
            "\\u0024env.DESK_URL",
            "$\\u0065nv.DESK_URL",
            "\\x24env.DESK_URL",
            "\\u{24}env.DESK_URL",
        ):
            se = self.refuse({"u": "={{ " + esc + " }}"}, "escape")
            self.assertIn("written with an escape", se)
        self.refuse({"jsCode": "return \\u0024env.DESK_URL"}, "escape")
        d = os.path.join(self.t, "chk")
        os.mkdir(d)
        jdump(
            {"nodes": [{"name": "n", "parameters": {"u": "={{ \\u0024env.DESK_URL }}"}}]},
            os.path.join(d, "a.json"),
        )
        self.assertEqual(self.cli("check", d, "--tokens-only")[0], 1)

    # ---- security review minor 4: the expression lexer against a real JavaScript engine
    @unittest.skipUnless(shutil.which("node"), "node (a JavaScript engine) is not installed")
    def test_lexer_agrees_with_a_real_js_engine(self):
        state = [20261116]

        def pick(items):  # tiny fixed-seed generator: the same cases on every run
            state[0] = (state[0] * 1103515245 + 12345) % 2**31
            return items[(state[0] >> 8) % len(items)]

        frags = [
            "1",
            "+",
            "-",
            "* 2",
            '"a"',
            "'b'",
            "`t`",
            '"\\""',
            "'\\''",
            "/* c */",
            "// c\n",
            "/r/",
            " / 2",
            "(",
            ")",
            "[",
            "]",
            "{",
            "}",
            ",",
            "?",
            ":",
            "0",
            "x",
            '"',
            "'",
            "`",
            "\\",
            "${",
            "/*",
            "//",
        ]
        value = "v\"'`\\${}/*//x"
        cases = [
            "`${ `a $env.MF_STAGE_URL` }`",  # F1: the token is inside a nested template string
            "`${ `a` }` + $env.MF_STAGE_URL + `x`",
        ]
        for _ in range(600):
            a = " ".join(pick(frags) for _ in range(pick(range(6))))
            b = " ".join(pick(frags) for _ in range(pick(range(6))))
            cases.append(a + " $env.MF_STAGE_URL " + b)
        accepted = []
        for part in cases:
            sub = ff.Subst({"MF_STAGE_URL": value})
            try:
                out = sub._expr_part(part)
            except ff.Refused:
                continue
            accepted.append((part.replace("$env.MF_STAGE_URL", "__T"), out))
        for bad in cases[:2]:  # the nested forms must be refused, whatever node says
            self.assertNotIn(bad.replace("$env.MF_STAGE_URL", "__T"), [a for a, _ in accepted])
        self.assertGreater(len(accepted), 20)
        self.assertLess(len(accepted), len(cases) - 20)
        script = (
            "const c=JSON.parse(require('fs').readFileSync(0,'utf8'));const v=c.v;"
            "const run=(src,args)=>{try{return JSON.stringify(new Function('__T','return ('+src+')')(args))}"
            "catch(e){return 'ERR:'+e.name}};"
            "console.log(JSON.stringify(c.p.map(([o,n])=>[run(o,v),run(n,v)])))"
        )
        p = subprocess.run(  # noqa: S603
            ["node", "-e", script],  # noqa: S607
            input=json.dumps({"v": value, "p": accepted}),
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        self.assertEqual(p.returncode, 0, p.stderr[:300])
        results = json.loads(p.stdout)
        compared = 0
        self.assertEqual(len(results), len(accepted))
        for i, (orig, out) in enumerate(accepted):
            r_orig, r_out = results[i]
            if r_orig.startswith("ERR:SyntaxError"):
                continue  # the unfilled text was not valid JavaScript; nothing to compare
            compared += 1
            self.assertEqual(r_orig, r_out, (orig, out))
        self.assertGreater(compared, 10)


class Round5(Base):
    """Security review round 2 (fix round 5): one test or more per finding."""

    def made(self, flavor="film"):
        out = self.out()
        self.fill(src=self.copy_flows(flavor), out=out)
        return out

    def swap_on_open(self, match, action):
        """A replacement for os.open that runs `action` once, at the first open whose path
        equals `match`: right before (when=before) the real call."""
        real_open = os.open
        state = {"n": 0}

        def hook(path, flags, mode=0o777, *, dir_fd=None):
            if os.fspath(path) == match and state["n"] == 0:
                state["n"] = 1
                action()
            return real_open(path, flags, mode, dir_fd=dir_fd)

        return hook

    # ---- 2: error text and escaped forms
    def test_leak_check_sees_escaped_forms(self):
        v = "ab" + '"' + "cd\\ef"  # a value with a quote and a backslash
        WRITTEN.append(v)
        for shown in (v, json.dumps(v)[1:-1], ascii(v)[1:-1], repr(v)[1:-1]):
            with self.assertRaises(AssertionError):
                self.leak_check(shown, "")
            with self.assertRaises(AssertionError):
                self.leak_check("", "x " + shown)

    def test_exception_text_is_never_printed(self):
        WRITTEN.append(CANARY)
        for name, exc in (
            ("do_check", ValueError("bad " + CANARY)),
            ("do_delete", KeyError(CANARY)),
            ("do_fill", RuntimeError(CANARY)),
        ):
            with mock.patch.object(ff, name, side_effect=exc):
                args = {
                    "do_check": ("check", self.t),
                    "do_delete": ("delete", "--out", self.out()),
                    "do_fill": ("fill", "--in", self.t, "--values", self.vf, "--out", self.out()),
                }[name]
                code, _so, se = self.inproc(*args)
            self.assertEqual((code, se), (1, "failed: " + type(exc).__name__ + "\n"), name)

    # ---- 3: a swap AFTER the open
    def test_fill_folder_swapped_for_a_link_after_the_open_writes_nothing_there(self):
        victim = os.path.join(self.t, "victim")
        os.mkdir(victim)
        out = self.out()
        real_open = os.open
        state = {"done": False}

        def hook(path, flags, mode=0o777, *, dir_fd=None):
            fd = real_open(path, flags, mode, dir_fd=dir_fd)
            opened_out = dir_fd is not None and path == "out" and flags & os.O_DIRECTORY
            if opened_out and not state["done"]:  # the folder was just opened: swap its name
                state["done"] = True
                os.rename(out, out + ".moved")
                os.symlink(victim, out)
            return fd

        with mock.patch.object(ff.os, "open", hook):
            code, _, _ = self.inproc(
                "fill", "--in", self.copy_flows("real"), "--values", self.vf, "--out", out
            )
        self.assertTrue(state["done"])
        self.assertEqual(os.listdir(victim), [])
        self.assertEqual(code, 3)
        self.assertEqual(len(os.listdir(out + ".moved")), 6)  # all written through the open folder

    # ---- 4: a cut manifest with no folder
    def test_delete_force_hash_removes_an_empty_or_cut_manifest_when_no_folder(self):
        out = self.out()
        man = out + ".manifest.json"
        for text in ("", '{"format": "fill_flows-manifest-1", "fil'):
            write_raw(man, text)
            os.chmod(man, 0o600)
            code, _, se = self.cli("delete", "--out", out)  # without the flag: still refused
            self.assertEqual((code, "not a valid fill_flows manifest" in se), (1, True), se)
            self.assertTrue(os.path.exists(man))
            code, so, _ = self.cli("delete", "--out", out, "--force-hash")
            self.assertEqual((code, "deleted the manifest" in so), (0, True), so)
            self.assertFalse(os.path.exists(man))
            self.assertEqual(self.fill(out=out)[0], 3)  # and a new fill works again
            self.cli("delete", "--out", out)

    def test_fill_refusal_names_the_way_out_of_a_cut_manifest(self):
        out = self.out()
        write_raw(out + ".manifest.json", "")
        code, _, se = self.fill(out=out)
        self.assertEqual((code, "delete --out" in se, "--force-hash" in se), (1, True, True), se)

    def test_force_hash_does_not_remove_a_manifest_that_is_a_link(self):
        out = self.out()
        victim = os.path.join(self.t, "victim")
        write_raw(victim, "precious")
        os.symlink(victim, out + ".manifest.json")
        code, _, se = self.cli("delete", "--out", out, "--force-hash")
        self.assertEqual((code, "symlink or not a file" in se), (1, True), se)
        self.assertEqual(rtext(victim), "precious")

    # ---- 6: checks on the place the open handle really is in
    def test_values_file_swapped_into_git_after_the_name_check_is_refused(self):
        clean = os.path.join(self.t, "clean")
        os.mkdir(clean, 0o700)
        repo = os.path.join(self.t, "repo2")
        os.makedirs(os.path.join(repo, ".git"))
        write_values(os.path.join(clean, "v.env"), VALS)
        write_values(os.path.join(repo, "v.env"), VALS)
        link = os.path.join(self.t, "vlink")
        os.symlink(clean, link)
        vf = os.path.join(link, "v.env")

        def swap():
            os.unlink(link)
            os.symlink(repo, link)

        out = self.out()
        with mock.patch.object(ff.os, "open", self.swap_on_open(vf, swap)):
            code, _, se = self.inproc(
                "fill", "--in", self.copy_flows("real"), "--values", vf, "--out", out
            )
        self.assertEqual((code, "git repository" in se), (1, True), se)
        self.assertFalse(os.path.exists(out))

    def test_output_parent_swapped_into_git_after_the_name_check_writes_nothing(self):
        clean = os.path.join(self.t, "clean-parent")
        os.mkdir(clean, 0o700)
        repo = os.path.join(self.t, "repo3")
        os.makedirs(os.path.join(repo, ".git"))
        link = os.path.join(self.t, "plink")
        os.symlink(clean, link)

        def swap():
            os.unlink(link)
            os.symlink(repo, link)

        with mock.patch.object(ff.os, "open", self.swap_on_open(link, swap)):
            code, _, se = self.inproc(
                "fill",
                "--in",
                self.copy_flows("real"),
                "--values",
                self.vf,
                "--out",
                os.path.join(link, "sub"),
            )
        self.assertEqual((code, "git repository" in se), (1, True), se)
        self.assertEqual(os.listdir(repo), [".git"])
        self.assertEqual(os.listdir(clean), [])

    def test_fd_path_follows_the_handle_not_the_name(self):
        a = os.path.join(self.t, "a")
        os.mkdir(a)
        fd = os.open(a, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.rename(a, a + "2")
            self.assertTrue(ff._fd_path(fd, "fallback").endswith("/a2"))
        finally:
            os.close(fd)
        self.assertEqual(ff._fd_path(10**6, "fallback"), "fallback")  # no such handle: fallback

    # ---- 7: --no-manifest and the sibling manifest
    def test_no_manifest_does_not_remove_an_invalid_sibling_manifest(self):
        out = self.made()
        man = out + ".manifest.json"
        write_raw(man + ".new", "{broken")
        os.replace(man + ".new", man)
        os.chmod(man, 0o600)
        code, _, se = self.cli("delete", "--out", out, "--no-manifest")
        self.assertEqual((code, "not a valid fill_flows manifest" in se), (1, True), se)
        self.assertTrue(os.path.exists(man))
        self.assertEqual(len(os.listdir(out)), 6)  # nothing deleted
        code, _, _ = self.cli("delete", "--out", out, "--no-manifest", "--force-hash")
        self.assertEqual(code, 0)  # the person said so: folder and the cut manifest go
        self.assertFalse(os.path.exists(out))
        self.assertFalse(os.path.exists(man))

    def test_no_manifest_removes_a_valid_sibling_manifest(self):
        out = self.made()
        self.assertEqual(self.cli("delete", "--out", out, "--no-manifest")[0], 0)
        self.assertFalse(os.path.exists(out + ".manifest.json"))

    # ---- 8: bad file names at fill time
    def test_input_names_with_a_backslash_or_control_character_are_refused(self):
        for bad in ("a\\b.json", "x\x01y.json", "x\x1b[31m.json", "x\u202ey.json"):
            d = self.flow_dir({"url": "$env.DESK_URL"})
            os.rename(os.path.join(d, "mf-x.json"), os.path.join(d, bad))
            out = self.out()
            code, _, se = self.fill(src=d, out=out)
            self.assertEqual((code, "path or control character" in se), (1, True), (bad, se))
            self.assertNotIn("\x1b", se)
            self.assertFalse(os.path.exists(out))
            self.assertFalse(os.path.exists(out + ".manifest.json"))

    def test_output_folder_name_with_a_backslash_is_refused(self):
        out = os.path.join(self.t, "o\\x")
        code, _, se = self.fill(out=out)
        self.assertEqual((code, "plain name" in se), (1, True), se)
        self.assertFalse(os.path.exists(out))

    # ---- 9: infinity
    def test_a_number_that_reads_as_infinity_is_refused(self):
        d = self.flow_dir({"url": "$env.DESK_URL", "big": 0})
        p = os.path.join(d, "mf-x.json")
        wtext(p, wtext_read(p).replace('"big": 0', '"big": 1e999'))
        code, _, se = self.fill(src=d)
        self.assertEqual((code, "mf-x.json" in se, "not valid JSON" in se), (1, True, True), se)
        self.assertFalse(os.path.exists(self.out()))
        with self.assertRaises(ValueError):
            ff.dump({"a": float("inf")})
        with self.assertRaises(ValueError):
            ff.dump({"a": float("nan")})

    # ---- 11: Ctrl-C between the creation of a file and its entry in the clean-up list
    def test_interrupt_right_after_a_file_is_written_leaves_nothing(self):
        real = ff._write_new
        n = {"n": 0}

        def wrapped(*a, **k):
            real(*a, **k)
            n["n"] += 1
            if n["n"] == 3:  # manifest, marker, then the first file: interrupt just after it
                raise KeyboardInterrupt

        out = self.out()
        with mock.patch.object(ff, "_write_new", wrapped), self.assertRaises(KeyboardInterrupt):
            self.inproc("fill", "--in", self.copy_flows("real"), "--values", self.vf, "--out", out)
        self.assertFalse(os.path.exists(out))
        self.assertFalse(os.path.exists(out + ".manifest.json"))

    def test_a_real_ctrl_c_during_creation_leaves_nothing(self):
        import signal

        real_open = os.open
        n = {"n": 0}

        def hook(path, flags, mode=0o777, *, dir_fd=None):
            fd = real_open(path, flags, mode, dir_fd=dir_fd)
            if flags & os.O_EXCL and dir_fd is not None:
                n["n"] += 1
                if n["n"] == 4:  # the file is made; the signal comes before the list entry
                    signal.raise_signal(signal.SIGINT)
            return fd

        out = self.out()
        with mock.patch.object(ff.os, "open", hook), self.assertRaises(KeyboardInterrupt):
            self.inproc("fill", "--in", self.copy_flows("real"), "--values", self.vf, "--out", out)
        self.assertGreaterEqual(n["n"], 4)
        self.assertFalse(os.path.exists(out))
        self.assertFalse(os.path.exists(out + ".manifest.json"))

    # ---- 12: a copy that still holds placeholders is loud and marked
    def test_incomplete_copy_is_marked_not_ready(self):
        out = self.made("real")
        self.assertIn(NOT_READY, os.listdir(out))
        self.assertIn("NOT READY TO IMPORT", rtext(os.path.join(out, NOT_READY)))
        self.assertEqual(oct(os.stat(os.path.join(out, NOT_READY)).st_mode & 0o777), "0o600")
        self.assertIn(NOT_READY, jload(out + ".manifest.json")["files"])
        code, so, _ = self.cli("check", out)
        self.assertEqual((code, NOT_READY in so), (1, True), so)
        # a complete copy carries no such file
        write_values(self.vf, {**VALS, **PH_VALS})
        done = self.out("done")
        self.assertEqual(self.fill(src=self.copy_flows("real"), out=done)[0], 0)
        self.assertNotIn(NOT_READY, os.listdir(done))
        self.assertEqual(self.cli("check", done)[0], 0)

    def test_fill_then_import_stops_when_placeholders_are_left(self):
        # README: `fill && import`. The shell must not reach the second command.
        cmd = [
            "sh",
            "-c",
            'python3 -I "$0" fill --in "$1" --values "$2" --out "$3" && echo IMPORTED',
        ]
        out = self.out()
        args = [os.path.join(HERE, "fill_flows.py"), self.copy_flows("real"), self.vf, out]
        p = subprocess.run(cmd + args, capture_output=True, text=True, timeout=60, check=False)  # noqa: S603
        self.leak_check(p.stdout, p.stderr)
        self.assertNotIn("IMPORTED", p.stdout)
        self.assertNotEqual(p.returncode, 0)
        # by default a missing placeholder value is a refusal and nothing is written
        self.assertIn("--allow-placeholders", p.stderr)
        self.assertFalse(os.path.exists(out))
        # the credential walk-through asks for the NOT READY copy on purpose
        cmd2 = [*cmd[:2], cmd[2].replace("--out", "--allow-placeholders --out")]
        p = subprocess.run(cmd2 + args, capture_output=True, text=True, timeout=60, check=False)  # noqa: S603
        self.assertNotIn("IMPORTED", p.stdout)
        self.assertEqual(p.returncode, 3)
        self.assertIn("NOT READY TO IMPORT", p.stderr)

    def test_delete_handles_the_not_ready_note(self):
        out = self.made("real")
        self.assertEqual(self.cli("delete", "--out", out)[0], 0)
        self.assertFalse(os.path.exists(out))
        out = self.made("real")
        os.unlink(out + ".manifest.json")
        note = os.path.join(out, NOT_READY)
        os.unlink(note)
        write_raw(note, "someone else's note")
        os.chmod(note, 0o600)
        code, _, se = self.cli("delete", "--out", out, "--no-manifest")
        self.assertEqual((code, "not-ready note is not" in se), (1, True), se)
        os.unlink(note)
        self.assertEqual(self.cli("delete", "--out", out, "--no-manifest")[0], 0)
        self.assertFalse(os.path.exists(out))


if __name__ == "__main__":
    unittest.main()
