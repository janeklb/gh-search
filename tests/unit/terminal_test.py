from unittest.mock import call, patch

import pytest

from ghsearch.terminal import ProgressPrinter


@pytest.mark.parametrize(
    "overwrite, isatty, force, expected_calls",
    [
        # overwrite = True, isatty = True, force = False
        (
            True,
            True,
            False,
            [
                call("\r\033[?25lHello!", nl=False),
                call("\r\033[?25l      ", nl=False),
                call("\r\033[?25h", nl=False),
            ],
        ),
        # overwrite = True, isatty = True, force = True
        (
            True,
            True,
            True,
            [
                call("\nHello!"),
                call("\r\033[?25l", nl=False),
                call("\r\033[?25h", nl=False),
            ],
        ),
        # overwrite = False, isatty = True, force = False
        (False, True, False, [call("Hello!")]),
        # overwrite = False, isatty = True, force = True
        (False, True, True, [call("Hello!")]),
        # overwrite = True, isatty = False, force = False
        (True, False, False, []),
        # overwrite = True, isatty = False, force = True
        (True, False, True, []),
        # overwrite = False, isatty = False, force = False
        (False, False, False, [call("Hello!")]),
        # overwrite = False, isatty = False, force = True
        (False, False, True, [call("Hello!")]),
    ],
)
def test_progress_printer(assert_click_echo_calls, overwrite, isatty, force, expected_calls):
    with patch("ghsearch.terminal.sys") as mock_sys:
        mock_sys.stdout.isatty.return_value = isatty

        with ProgressPrinter(overwrite=overwrite) as printer:
            printer("Hello!", force=force)

    assert_click_echo_calls(*expected_calls)
