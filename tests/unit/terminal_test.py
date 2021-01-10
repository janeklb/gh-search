from unittest.mock import call

from ghsearch.terminal import ProgressPrinter


def test_progress_printer(assert_click_echo_calls):

    with ProgressPrinter() as printer:
        printer("Hello!")

    assert_click_echo_calls(
        call("\r\033[?25lHello!", nl=False),
        call("\r\033[?25l      ", nl=False),
        call("\r\033[?25h"),
    )


def test_progress_printer_verbose(assert_click_echo_calls):
    with ProgressPrinter(overwrite=False) as printer:
        printer("Hello!")

    assert_click_echo_calls(call("Hello!"))
