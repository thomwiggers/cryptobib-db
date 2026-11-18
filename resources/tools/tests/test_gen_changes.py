import os
import subprocess

import gen_changes
import pytest
from gen_changes import HistoryError, generate, main

ARCHIVE = b"* 2026-06-23\nFC 2025\n\n"


@pytest.fixture
def git_env(tmp_path):
    """Environment that isolates git from the user's and the system's configuration."""
    xdg = tmp_path / "xdg"
    xdg.mkdir()
    env = {
        k: v
        for k, v in os.environ.items()
        if not k.startswith("GIT_") or k in ("GIT_EXEC_PATH",)
    }
    env.update(
        GIT_CONFIG_GLOBAL=os.devnull,
        GIT_CONFIG_NOSYSTEM="1",
        GIT_ATTR_NOSYSTEM="1",
        XDG_CONFIG_HOME=str(xdg),
        LC_ALL="C",
    )
    return env


class Repo:
    def __init__(self, path, env):
        self.path = path
        self.env = env

    def git(self, *args, date=None):
        env = dict(self.env)
        if date is not None:
            env.update(GIT_AUTHOR_DATE=date, GIT_COMMITTER_DATE=date)
        return subprocess.run(
            ["git", *args],
            cwd=self.path,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        ).stdout

    def commit(self, subject, files, date, body=""):
        for name in files:
            path = self.path / name
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a") as f:
                f.write(f"{subject}\n")
        self.git("add", "--", *files)
        message = ["-m", subject] + (["-m", body] if body else [])
        self.git("commit", "-q", *message, date=date)


def make_repo(path, env):
    path.mkdir()
    repo = Repo(path, env)
    repo.git("init", "-q", "-b", "master")
    repo.git("config", "user.name", "Test")
    repo.git("config", "user.email", "test@example.org")
    repo.git("config", "commit.gpgsign", "false")
    return repo


@pytest.fixture
def git_repo(tmp_path, git_env):
    repo = make_repo(tmp_path / "repo", git_env)
    date = "2026-06-23T12:00:00+00:00"
    repo.commit("initial", ["crypto_db.bib"], date)
    (repo.path / "changes.txt").write_bytes(ARCHIVE)
    repo.git("add", "changes.txt")
    repo.git("commit", "-q", "-m", "changes", date=date)
    repo.git("mv", "changes.txt", "changes-archive.txt")
    repo.git("commit", "-q", "-m", "chore: archive the changelog", date=date)
    return repo


@pytest.fixture
def repo(git_repo):
    return git_repo.path


NOON = "2026-12-03T12:00:00+00:00"


def test_no_commits_after_cutoff(repo):
    assert generate(repo) == (repo / "changes-archive.txt").read_bytes()


def test_block_format(git_repo, repo):
    git_repo.commit("fix(data): title of EC:CFSY96 (#346)", ["crypto_db.bib"], NOON)
    git_repo.commit("add(data): FC 2025, FCW 2025 (#348)", ["crypto_db.bib"], NOON)
    git_repo.commit("fix(data)!: rename keys (#350)", ["crypto_db.bib"], NOON)
    git_repo.commit("Misc fixes", ["crypto_db.bib"], NOON)
    git_repo.commit(
        "ci: cache the bibtex8 binary (#351)", [".github/workflows/ci.yaml"], NOON
    )
    git_repo.commit("add(data): IEEE S&P 2026 (#349)", ["crypto_db.bib"], NOON)
    assert generate(repo) == (
        b"* 2026-12-03\n"
        b"Breaking: rename keys (#350)\n"
        b"Added: FC 2025, FCW 2025 (#348); IEEE S&P 2026 (#349)\n"
        b"Fixed: title of EC:CFSY96 (#346)\n"
        b"Other: Misc fixes\n"
        b"\n"
        b"* 2026-06-23\nFC 2025\n\n"
    )


def test_newest_date_first_and_utc(git_repo, repo):
    git_repo.commit("fix(data): a", ["crypto_db.bib"], "2026-12-03T23:30:00-05:00")
    git_repo.commit("fix(data): b", ["crypto_db.bib"], "2026-12-03T10:00:00+00:00")
    assert generate(repo).startswith(
        b"* 2026-12-04\nFixed: a\n\n* 2026-12-03\nFixed: b\n\n"
    )


def test_pr_merge_commit_title_from_body(git_repo, repo):
    git_repo.git("switch", "-q", "-c", "tapei-typo")
    git_repo.commit("typo", ["crypto_db.bib"], NOON)
    git_repo.git("switch", "-q", "master")
    git_repo.git(
        "merge",
        "-q",
        "--no-ff",
        "tapei-typo",
        "-m",
        "Merge pull request #341 from flogriesser/tapei-typo\n\nfix(data): Tapei -> Taipei",
        date="2026-12-04T12:00:00+00:00",
    )
    assert (
        generate(repo) == b"* 2026-12-04\nFixed: Tapei -> Taipei (#341)\n\n" + ARCHIVE
    )


def test_plain_merge_is_unpacked(git_repo, repo):
    git_repo.git("switch", "-q", "-c", "side")
    git_repo.commit("fix(data): a (#1)", ["crypto_db.bib"], NOON)
    git_repo.commit("Misc", ["crypto_db.bib"], NOON)
    git_repo.git("switch", "-q", "master")
    git_repo.commit("fix(data): b (#2)", ["config.py"], NOON)
    git_repo.git(
        "merge",
        "-q",
        "--no-ff",
        "side",
        "-m",
        "Merge branch 'master' of github.com:cryptobib/db",
        date="2026-12-05T12:00:00+00:00",
    )
    output = generate(repo)
    assert output == (
        b"* 2026-12-05\n"
        b"Fixed: a (#1)\n"
        b"Other: Misc\n"
        b"\n"
        b"* 2026-12-03\n"
        b"Fixed: b (#2)\n"
        b"\n" + ARCHIVE
    )
    assert b"Merge branch" not in output


def test_nested_plain_merge_lists_each_commit_once(git_repo, repo):
    git_repo.git("branch", "side")
    git_repo.commit("fix(data): m1", ["config.py"], "2026-12-01T12:00:00+00:00")
    git_repo.git("switch", "-q", "side")
    git_repo.commit("fix(data): s1", ["crypto_db.bib"], "2026-12-02T12:00:00+00:00")
    git_repo.git(
        "merge",
        "-q",
        "--no-ff",
        "master",
        "-m",
        "Merge branch 'master' into side",
        date="2026-12-03T12:00:00+00:00",
    )
    git_repo.git("switch", "-q", "master")
    git_repo.git(
        "merge",
        "-q",
        "--no-ff",
        "side",
        "-m",
        "Merge branch 'side'",
        date="2026-12-05T12:00:00+00:00",
    )
    assert generate(repo) == (
        b"* 2026-12-05\nFixed: s1\n\n* 2026-12-01\nFixed: m1\n\n" + ARCHIVE
    )


def test_octopus_merge_lists_every_branch(git_repo, repo):
    git_repo.git("switch", "-q", "-c", "x")
    git_repo.commit("fix(data): x", ["crypto_db.bib"], NOON)
    git_repo.git("switch", "-q", "-c", "y", "master")
    git_repo.commit("fix(data): y", ["config.py"], NOON)
    git_repo.git("switch", "-q", "master")
    git_repo.git(
        "merge",
        "-q",
        "--no-ff",
        "x",
        "y",
        "-m",
        "Merge branches 'x' and 'y'",
        date="2026-12-05T12:00:00+00:00",
    )
    assert generate(repo) == b"* 2026-12-05\nFixed: x; y\n\n" + ARCHIVE


def test_pr_merge_without_body_is_unpacked(git_repo, repo):
    git_repo.git("switch", "-q", "-c", "p")
    git_repo.commit("typo", ["crypto_db.bib"], NOON)
    git_repo.git("switch", "-q", "master")
    git_repo.git(
        "merge",
        "-q",
        "--no-ff",
        "p",
        "-m",
        "Merge pull request #7 from a/p",
        date="2026-12-04T12:00:00+00:00",
    )
    assert generate(repo) == b"* 2026-12-04\nOther: typo\n\n" + ARCHIVE


def test_pr_merge_body_title_loses_pr_suffix(git_repo, repo):
    git_repo.git("switch", "-q", "-c", "tapei-typo")
    git_repo.commit("typo", ["crypto_db.bib"], NOON)
    git_repo.git("switch", "-q", "master")
    git_repo.git(
        "merge",
        "-q",
        "--no-ff",
        "tapei-typo",
        "-m",
        "Merge pull request #341 from flogriesser/tapei-typo\n\n"
        "fix(data): Tapei -> Taipei (#341)",
        date="2026-12-04T12:00:00+00:00",
    )
    assert (
        generate(repo) == b"* 2026-12-04\nFixed: Tapei -> Taipei (#341)\n\n" + ARCHIVE
    )


def test_revert_touching_data_is_other(git_repo, repo):
    git_repo.commit('Revert "add(data): FC 2025 (#348)"', ["crypto_db.bib"], NOON)
    assert generate(repo).startswith(
        b'* 2026-12-03\nOther: Revert "add(data): FC 2025 (#348)"\n\n'
    )


def test_only_trailing_pr_number_is_stripped(git_repo, repo):
    git_repo.commit("fix(data): entries (#12) and more (#345)", ["crypto_db.bib"], NOON)
    assert generate(repo).startswith(
        b"* 2026-12-03\nFixed: entries (#12) and more (#345)\n\n"
    )


def test_data_title_without_data_file_is_listed(git_repo, repo):
    git_repo.commit("fix(data): venue name of ACNS (#7)", ["config.py"], NOON)
    assert generate(repo).startswith(
        b"* 2026-12-03\nFixed: venue name of ACNS (#7)\n\n"
    )


def test_non_data_commit_is_omitted(git_repo, repo):
    git_repo.commit("docs: describe the title format (#9)", ["README.md"], NOON)
    assert generate(repo) == (repo / "changes-archive.txt").read_bytes()


def test_shallow_clone(git_repo, repo, tmp_path, monkeypatch):
    clone = tmp_path / "clone"
    git_repo.git("clone", "-q", "--depth", "1", f"file://{repo}", str(clone))
    with pytest.raises(HistoryError, match="shallow"):
        generate(clone)
    monkeypatch.setattr(gen_changes, "ROOT", clone)
    assert main([]) == 1
    assert not (clone / "changes.txt").exists()


def test_no_archive(tmp_path, git_env):
    repo = make_repo(tmp_path / "repo", git_env)
    repo.commit("initial", ["crypto_db.bib"], NOON)
    with pytest.raises(HistoryError):
        generate(repo.path)
