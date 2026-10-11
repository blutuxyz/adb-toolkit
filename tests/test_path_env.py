from adb_toolkit.core.path_env import merge_path_entries


def test_appends_a_new_directory():
    assert merge_path_entries("C:\\Tools;C:\\Bin", "C:\\New", separator=";") == "C:\\Tools;C:\\Bin;C:\\New"


def test_returns_none_when_the_directory_is_already_listed():
    assert merge_path_entries("/usr/bin:/tools", "/tools/", separator=":") is None


def test_ignores_empty_entries_and_quotes():
    assert merge_path_entries("", "/tools", separator=":") == "/tools"
    assert merge_path_entries(":/usr/bin:", "/tools", separator=":") == "/usr/bin:/tools"
    assert merge_path_entries('"/tools"', "/tools", separator=":") is None
