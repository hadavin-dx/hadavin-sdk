"""The copyleft pattern of tools/licence_check.py, spelling by spelling, and the ways the check itself must fail."""

import pytest
from tools import licence_check as lc

COPYLEFT = [
    "GPL-3.0-or-later",
    "GPLv3",
    "GPLv2+",
    "GPL-2.0-only WITH Classpath-exception-2.0",
    "LGPL-2.1+",
    "LGPLv3+",
    "LGPL-3.0-only",
    "AGPLv3",
    "AGPL-3.0-or-later",
    "GNU Affero General Public License v3",
    "Affero General Public License",
    "GNU Lesser General Public License v2.1 (LGPLv2.1)",
    "Lesser General Public License",
    "GNU General Public License v3 (GPLv3)",
    "License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)",
    "SSPL-1.0",
    "Server Side Public License",
    "EUPL-1.2",
    "European Union Public Licence 1.2",
    "gpl-3.0",
    "Some prose\nthat is long and ends with: licensed under the GNU GPL version 3",
]
PERMISSIVE = [
    "MIT",
    "MIT License",
    "Apache-2.0",
    "Apache Software License",
    "BSD-3-Clause",
    "BSD 2-Clause License",
    "ISC",
    "Mozilla Public License 2.0 (MPL 2.0)",
    "MPL-2.0",
    "PSF-2.0",
    "Python Software Foundation License",
    "Unlicense",
    "0BSD",
]


@pytest.mark.parametrize("text", COPYLEFT)
def test_copyleft_spellings_are_caught(text):
    assert lc.is_copyleft([text])


@pytest.mark.parametrize("text", PERMISSIVE)
def test_permissive_spellings_pass(text):
    assert not lc.is_copyleft([text])


def _run(tmp_path, export, exceptions=""):
    e = tmp_path / "export.txt"
    e.write_text(export, encoding="utf-8")
    x = tmp_path / "exc.txt"
    x.write_text(exceptions, encoding="utf-8")
    return lc.main(["licence_check", str(e), str(x)])


def test_a_package_that_is_not_installed_fails(tmp_path):
    assert _run(tmp_path, "no-such-package-zz==1.0\n") == 1


def test_a_missing_package_must_be_listed_as_unchecked(tmp_path):
    line = "no-such-package-zz==1.0 ; sys_platform == 'nonexistent-os'\n"
    assert _run(tmp_path, line) == 1
    assert _run(tmp_path, line, "unchecked no-such-package-zz==1.0  # by hand\n") == 0


def test_a_stale_exception_fails(tmp_path):
    assert _run(tmp_path, "", "allow no-such-package-zz==1.0  # gone\n") == 1
