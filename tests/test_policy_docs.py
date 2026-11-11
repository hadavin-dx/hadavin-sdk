"""Checks of the texts around the declared permissions that live outside the page: the CHANGELOG entry, the
README link and the CI workflow (ticket Q8c, PR 1, fix batch 1). Kept apart from tests/test_policy_guard.py
because the mutant runner copies only `src`, `tests`, `tools` and `docs` into its temp tree.
"""

from __future__ import annotations

import yaml as _yaml
from tools import policy_page as pp

from tests.test_policy_guard import ROOT, _policies


def test_m1_no_text_states_the_vault_refusals_as_fact_while_no_run_is_on_record():
    assert pp.ENGINE_RUN is None, "a run is on record: change this test together with ENGINE_RUN"
    page = pp.page(ROOT)
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    entry = changelog[changelog.index("**Declared permissions for three backend kinds**") :][:4000]
    for name, text in (("page", page), ("CHANGELOG", entry)):
        flat = " ".join(text.split())
        assert "refused by a real Vault server" not in flat, name
        assert "have not run yet" in flat, name
    assert page.count("These tests have not run yet: no run of them is on record.") == 3


def test_the_page_title_notes_and_engine_image_are_true():
    text = pp.page(ROOT)
    assert text.startswith("# Declared permissions per backend kind\n")
    assert pp.PAGE == "docs/declared-permissions.md"
    for path in ("README.md", "CHANGELOG.md", "docs/declared-permissions.md"):
        body = (ROOT / path).read_text(encoding="utf-8").lower()
        assert "least-privilege polic" not in body, path
    assert "builder's memory" not in text and "No ticket removes this yet" not in text
    jobs = _yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8"))["jobs"]
    images = {
        job["services"]["vault"]["image"]
        for job in jobs.values()
        if "vault" in (job.get("services") or {})
    }
    assert len(images) == 1 and images.pop().startswith(pp.ENGINE_IMAGE + "@sha256:")
    for words in (
        f"one server image only: `{pp.ENGINE_IMAGE}`, licence: Business Source License 1.1",
        "The open alternative OpenBao (licence MPL-2.0)",
        "it has not yet been",
        "identity groups of the signed-in entity",
        "the wildcard verb `*`",
        "`create` on the self-review resources",
        "the namespaced Role on this page cannot grant it",
        "without it, so that longer form is not allowed by this policy",
    ):
        assert words in " ".join(text.split()), words
    never = {(k, n.name) for k, p in _policies().items() for n in p.never}
    for entry in (
        ("secrets/vault", "{mount}/delete/*"),
        ("secrets/vault", "{mount}/undelete/*"),
        ("secrets/vault", "{mount}/subkeys/*"),
        ("signer/vault_transit", "{transit_mount}/byok-export/*"),
        ("signer/vault_transit", "{transit_mount}/keys/{key_name}/rotate"),
        ("signer/vault_transit", "{transit_mount}/keys/{key_name}/trim"),
        ("signer/vault_transit", "{transit_mount}/restore"),
        ("signer/vault_transit", "{transit_mount}/restore/*"),
    ):
        assert entry in never, entry
    data = next(n for n in _policies()["secrets/vault"].never if n.name == "{mount}/data/*")
    assert "patch" in data.capabilities


def test_m14_ci_runs_the_policy_mutants_next_to_the_stage_mutants():
    steps = _yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8"))[
        "jobs"
    ]["check"]["steps"]
    runs = [s.get("run", "") for s in steps]
    assert "python tests/stage_mutants.py" in runs and "python tests/policy_mutants.py" in runs
    assert (
        runs.index("python tests/policy_mutants.py")
        == runs.index("python tests/stage_mutants.py") + 1
    )
