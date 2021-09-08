from unittest.mock import call

import pytest

from ghsearch.output import DefaultPrinter, JsonPrinter, RepoListPrinter, YamlPrinter

from . import build_mock_content_file


@pytest.mark.parametrize(
    "printer_cls, expected_calls",
    [
        (
            DefaultPrinter,
            [
                call("No results!"),
                call(
                    "(For limitations of GitHub's code search see https://docs.github.com/en/github/"
                    "searching-for-information-on-github/searching-code#considerations-for-code-search)"
                ),
            ],
        ),
        (RepoListPrinter, []),
    ],
)
def test_print_no_results(printer_cls, expected_calls, assert_click_echo_calls):
    printer_cls().print(["query"], {})
    assert_click_echo_calls(*expected_calls)


@pytest.mark.parametrize(
    "printer_cls, expected_calls",
    [
        (
            DefaultPrinter,
            [
                call("Results:"),
                call(" 2 - org/repo1: https://www.github.com/org/repo1/search?utf8=✓&q=query"),
                call("\t- README.md"),
                call("\t- file.txt"),
            ],
        ),
        (RepoListPrinter, [call("org/repo1")]),
    ],
)
def test_print_results_slingle_repo(printer_cls, expected_calls, assert_click_echo_calls):
    printer_cls().print(
        ["query"],
        [
            build_mock_content_file("org/repo1", "README.md"),
            build_mock_content_file("org/repo1", "file.txt"),
        ],
    )

    assert_click_echo_calls(*expected_calls)


@pytest.mark.parametrize(
    "printer_cls, expected_calls",
    [
        (
            DefaultPrinter,
            [
                call("Results:"),
                call(" 2 - org/repo1: https://www.github.com/org/repo1/search?utf8=✓&q=query"),
                call("\t- README.md"),
                call("\t- file.txt"),
                call(" 1 - org/repo2: https://www.github.com/org/repo2/search?utf8=✓&q=query"),
                call("\t- file-2.json"),
            ],
        ),
        (RepoListPrinter, [call("org/repo1"), call("org/repo2")]),
        (
            JsonPrinter,
            [
                call(
                    '[{"full_name": "org/repo1", "html_url": "https://www.github.com/org/repo1", "fork": false, "owner": "org", "name": "repo1", "results": [{"path": "README.md", "name": "README.md", "size": 1000, "html_url": "https://www.github.com/org/repo1/blob/master/README.md"}, {"path": "file.txt", "name": "file.txt", "size": 1000, "html_url": "https://www.github.com/org/repo1/blob/master/file.txt"}]}, {"full_name": "org/repo2", "html_url": "https://www.github.com/org/repo2", "fork": false, "owner": "org", "name": "repo2", "results": [{"path": "file-2.json", "name": "file-2.json", "size": 1000, "html_url": "https://www.github.com/org/repo2/blob/master/file-2.json"}]}]'  # noqa: E501
                )
            ],
        ),
        (
            YamlPrinter,
            [
                call(
                    "- fork: false\n"
                    "  full_name: org/repo1\n"
                    "  html_url: https://www.github.com/org/repo1\n"
                    "  name: repo1\n"
                    "  owner: org\n"
                    "  results:\n"
                    "  - html_url: https://www.github.com/org/repo1/blob/master/README.md\n"
                    "    name: README.md\n"
                    "    path: README.md\n"
                    "    size: 1000\n"
                    "  - html_url: https://www.github.com/org/repo1/blob/master/file.txt\n"
                    "    name: file.txt\n"
                    "    path: file.txt\n"
                    "    size: 1000\n"
                    "- fork: false\n"
                    "  full_name: org/repo2\n"
                    "  html_url: https://www.github.com/org/repo2\n"
                    "  name: repo2\n"
                    "  owner: org\n"
                    "  results:\n"
                    "  - html_url: https://www.github.com/org/repo2/blob/master/file-2.json\n"
                    "    name: file-2.json\n"
                    "    path: file-2.json\n"
                    "    size: 1000\n"
                    ""
                )
            ],
        ),
    ],
)
def test_print_results_multiple_repos(printer_cls, expected_calls, assert_click_echo_calls):
    printer_cls().print(
        ["query"],
        [
            build_mock_content_file("org/repo1", "README.md"),
            build_mock_content_file("org/repo1", "file.txt"),
            build_mock_content_file("org/repo2", "file-2.json"),
        ],
    )

    assert_click_echo_calls(*expected_calls)


def test_run_with_qualifiers(assert_click_echo_calls):
    DefaultPrinter().print(
        ["query", "org:foo", "filename:bar"],
        [
            build_mock_content_file("org/repo1", "README.md"),
            build_mock_content_file("org/repo1", "file.txt"),
        ],
    )

    assert_click_echo_calls(
        call("Results:"),
        call(" 2 - org/repo1: https://www.github.com/org/repo1/search?utf8=✓&q=query%20filename%3Abar"),
        call("\t- README.md"),
        call("\t- file.txt"),
    )
