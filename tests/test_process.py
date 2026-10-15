"""The streaming runner passes each line on as it arrives, and reads progress from adb's output."""

import sys

from adb_toolkit.core.process import percent_of, stream


def test_each_line_is_passed_on_and_a_carriage_return_ends_a_line_too():
    code = "import sys; sys.stdout.write('[ 10%] a.txt\\r[ 55%] a.txt\\r'); sys.stdout.write('done\\n')"
    seen: list[str] = []

    result = stream([sys.executable, "-c", code], seen.append)

    assert seen == ["[ 10%] a.txt", "[ 55%] a.txt", "done"]
    assert result.ok
    assert result.stdout == "[ 10%] a.txt\n[ 55%] a.txt\ndone"


def test_a_failing_command_reports_its_exit_code():
    result = stream([sys.executable, "-c", "import sys; sys.exit(3)"], lambda line: None)

    assert result.returncode == 3
    assert not result.ok


def test_stdin_is_closed_so_a_question_gets_no_answer_and_does_not_hang():
    code = "import sys; sys.stdout.write(sys.stdin.read() or 'no input')"

    result = stream([sys.executable, "-c", code], lambda line: None)

    assert result.stdout == "no input"


def test_a_missing_program_reports_127_instead_of_raising():
    result = stream(["adb-toolkit-no-such-program"], lambda line: None)

    assert result.returncode == 127


def test_a_command_past_its_timeout_is_stopped_and_reports_124():
    result = stream([sys.executable, "-c", "import time; time.sleep(30)"], lambda line: None, timeout=0.5)

    assert result.returncode == 124


def test_percent_is_read_from_push_pull_and_sideload_lines():
    assert percent_of("[ 45%] /sdcard/a.txt") == 45
    assert percent_of("[100%] /sdcard/a.txt") == 100
    assert percent_of("serving: 'rom.zip'  (~12%)") == 12
    assert percent_of("Success") is None
