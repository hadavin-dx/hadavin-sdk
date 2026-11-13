Every runner and builder brief sets PYTHONPATH=<worktree>/src and prints hadavin_sdk.__file__ before any run, because shared venvs hold an editable install that may point at another worktree.
