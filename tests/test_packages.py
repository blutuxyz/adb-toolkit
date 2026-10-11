from adb_toolkit.core.packages import (
    SYSTEM,
    USER,
    AppEntry,
    build_entries,
    parse_package_list,
    restore_succeeded,
    uninstall_succeeded,
)


def test_parses_package_lines_and_skips_anything_else():
    output = "package:com.android.chrome\npackage:com.example.app\n\nWARNING: something\n"

    assert parse_package_list(output) == {"com.android.chrome", "com.example.app"}


def test_build_entries_marks_user_system_and_removed_apps():
    installed = {"com.example.app", "com.android.chrome"}
    system = {"com.android.chrome", "com.android.bloat"}

    entries = build_entries(installed, system)

    assert entries == [
        AppEntry("com.android.bloat", SYSTEM, installed=False),
        AppEntry("com.android.chrome", SYSTEM, installed=True),
        AppEntry("com.example.app", USER, installed=True),
    ]
    assert entries[0].removed is True
    assert entries[1].removed is False
    assert entries[2].removed is False


def test_tags_describe_each_kind_of_app():
    assert AppEntry("a", SYSTEM, installed=True).tag == "System app"
    assert AppEntry("b", USER, installed=True).tag == "User app"
    assert AppEntry("c", SYSTEM, installed=False).tag == "Removed system app"


def test_uninstall_success_is_read_from_pm_output():
    assert uninstall_succeeded("Success\n") is True
    assert uninstall_succeeded("Failure [DELETE_FAILED_INTERNAL_ERROR]\n") is False


def test_restore_success_is_read_from_cmd_package_output():
    assert restore_succeeded("Package com.android.bloat installed for user: 0\n") is True
    assert restore_succeeded("Package com.android.bloat is already installed\n") is True
    assert restore_succeeded("Error: unknown package\n") is False
