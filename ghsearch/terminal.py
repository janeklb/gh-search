import contextlib
import re
import sys

import click

HIDE_CURSOR = "\033[?25l"
SHOW_CURSOR = "\033[?25h"
_ansi_re = re.compile(r"\033\[[;?0-9]*[a-zA-Z]")


def _strip_ansi(value):
    return _ansi_re.sub("", value)


def _term_len(x):
    return len(_strip_ansi(x))


class ProgressPrinter(contextlib.AbstractContextManager):
    def __init__(self, overwrite=True):
        self.overwrite = overwrite and sys.stdout.isatty()
        self.verbose = not overwrite
        self.last_width = 0

    def __enter__(self):
        def printer(message, force=False):
            if self.overwrite:
                if force:
                    click.echo(f"\n{message}")
                else:
                    self._overwrite_previous_line(message)
            elif self.verbose:
                click.echo(message)

        return printer

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.overwrite:
            self._overwrite_previous_line()
            click.echo("\r" + SHOW_CURSOR, nl=False)
        return None

    def _overwrite_previous_line(self, message=""):
        line_width = _term_len(message)
        click.echo(f"\r{HIDE_CURSOR}{message}{' ' * (self.last_width - line_width)}", nl=False)
        self.last_width = line_width
