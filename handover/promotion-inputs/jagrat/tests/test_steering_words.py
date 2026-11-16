from importlib import resources

import pytest

from jagrat import quarantine

EIGHTEEN = [
    "restart_pods",
    "scale_up",
    "scale_down",
    "rollback_deploy",
    "failover_replica",
    "clear_cache",
    "terminate_connections",
    "revert_config",
    "pause_flow",
    "resume_flow",
    "shift_traffic",
    "redrive_messages",
    "cancel_query",
    "raise_limit",
    "freeze_changes",
    "revert_change",
    "no_action",
    "escalate_to_human",
]


def test_the_data_file_holds_exactly_the_eighteen_reference_values():
    text = (resources.files("jagrat") / "data" / "steering_action_words.txt").read_text(
        encoding="utf-8"
    )
    assert text.splitlines() == EIGHTEEN


@pytest.mark.parametrize("word", EIGHTEEN)
def test_steering_check_matches_each_squashed_value(word):
    assert quarantine._ACTION_WORDS.search(word.replace("_", ""))


@pytest.mark.parametrize("word", ["scaledown", "failoverreplica", "clearcache"])
def test_retired_words_are_still_refused_as_measurements(word):
    assert quarantine._plain(word, 40) is False


def test_plain_words_still_pass():
    assert quarantine._plain("checkout", 40) is True
