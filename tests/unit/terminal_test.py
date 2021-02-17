from unittest.mock import call, patch

import pytest

from ghsearch.terminal import ProgressPrinter


@pytest.mark.parametrize(
    "overwrite, isatty, expected_calls",
    [
        # overwrite = True, isatty = True
        (
            True,
            True,
            [
                call("\r\033[?25lHello!", nl=False),
                call("\r\033[?25l      ", nl=False),
                call("\r\033[?25h", nl=False),
            ],
        ),
        # overwrite = False, isatty = True
        (False, True, [call("Hello!")]),
        # overwrite = True, isatty = False
        (True, False, []),
        # overwrite = False, isatty = False
        (False, False, [call("Hello!")]),
    ],
)
def test_progress_printer(assert_click_echo_calls, overwrite, isatty, expected_calls):
    with patch("ghsearch.terminal.sys") as mock_sys:
        mock_sys.stdout.isatty.return_value = isatty

        with ProgressPrinter(overwrite=overwrite) as printer:
            printer("Hello!")

    assert_click_echo_calls(*expected_calls)
