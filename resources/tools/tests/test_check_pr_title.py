from check_pr_title import MARKER, main


def run(tmp_path, title, files):
    files_file = tmp_path / "files.txt"
    files_file.write_text("\n".join(files) + "\n")
    comment = tmp_path / "comment.md"
    code = main(
        [
            "--title",
            title,
            "--files-from",
            str(files_file),
            "--comment-out",
            str(comment),
        ]
    )
    return code, comment.read_text()


def test_valid_title(tmp_path):
    code, comment = run(tmp_path, "fix(data): x", ["crypto_db.bib"])
    assert code == 0
    assert comment.startswith(MARKER)
    assert "follows the format" in comment


def test_invalid_title(tmp_path):
    code, comment = run(tmp_path, "Fixed my own last name", ["crypto_db.bib"])
    assert code == 1
    assert comment.startswith(MARKER)
    assert "The title must have the form type(scope): description" in comment
    assert "````\nfix(data): my own last name\n````" in comment
    for example in (
        "add(data): FC 2025, FCW 2025, ICISC 2025",
        "fix(data): title of EC:CFSY96",
        "fix(data)!: rename keys of entries with more than six authors",
        "ci: cache the bibtex8 binary",
    ):
        assert example in comment


def test_data_file_without_scope(tmp_path):
    code, comment = run(tmp_path, "chore: x", ["crypto_db.bib", "README.md"])
    assert code == 1
    assert "crypto_db.bib" in comment


def test_title_is_data_not_code(tmp_path):
    title = '`rm -rf /` $(id) "x"; fix'
    code, comment = run(tmp_path, title, ["README.md"])
    assert code == 1
    assert f"````\nchore: {title}\n````" in comment


def test_backticks_in_title_cannot_close_the_block(tmp_path):
    code, comment = run(tmp_path, "Fix a ```` b.", ["README.md"])
    assert code == 1
    assert "`````\nchore: a ```` b\n`````" in comment


def test_missing_files_argument():
    assert main(["--title", "fix: x"]) == 2


def test_title_starting_with_a_dash(tmp_path):
    files_file = tmp_path / "files.txt"
    files_file.write_text("README.md\n")
    comment = tmp_path / "comment.md"
    argv = [
        "--title=-fix stuff",
        "--files-from",
        str(files_file),
        "--comment-out",
        str(comment),
    ]
    assert main(argv) == 1
    assert "````\nchore: -fix stuff\n````" in comment.read_text()
