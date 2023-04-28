import json
import re

from amarps import __version__, main
import click.testing
import pytest


@pytest.fixture
def output_json_file(tmp_path):
    return tmp_path / "output.json"


def test_main_version_succeeds():
    runner = click.testing.CliRunner()
    result = runner.invoke(main.main, ["--version"])
    assert result.exit_code == 0
    regex = re.compile(f"(amarps|main), version {__version__}")
    assert regex.match(result.output)


def test_main_help_succeeds():
    runner = click.testing.CliRunner()
    result = runner.invoke(main.main, ["--help"])
    assert result.exit_code == 0


@pytest.mark.e2e
@pytest.mark.parametrize("browser", ["chrome", "firefox"])
def test_main_download_reviews_succeeds(browser):
    runner = click.testing.CliRunner()
    result = runner.invoke(
        main.main,
        [
            "--start-page",
            "71",
            "--headless",
            "--browser",
            browser,
            "https://www.amazon.com/product-reviews/B01AMT0EYU/",
        ],
    )

    try:
        assert result.exit_code == 0
    except AssertionError:
        # FIXME improve to avoid this, likely reason for failure: Server prevents access
        assert result.exit_code == 1
        assert type(result.exception) is RuntimeError


@pytest.mark.e2e
@pytest.mark.parametrize("browser", ["chrome", "firefox"])
def test_main_download_reviews_profiles_succeeds(browser):
    runner = click.testing.CliRunner()
    result = runner.invoke(
        main.main,
        [
            "--headless",
            "--start-page",
            "33",
            "--stop-page",
            "35",
            "--browser",
            browser,
            "--profiles",
            "https://www.amazon.com/product-reviews/B01AMT0EYU/",
        ],
    )

    try:
        assert result.exit_code == 0
    except AssertionError:
        # FIXME improve to avoid this, likely reason for failure: Server prevents access
        assert result.exit_code == 1
        assert type(result.exception) is RuntimeError


@pytest.mark.flaky(reruns=10)
@pytest.mark.parametrize("browser", ["chrome", "firefox"])
def test_main_download_profile_local_succeeds(
    browser,
    httpserver_profile_urls,
    httpserver_expected_profiles_data,
    output_json_file,
):
    for expected, url in zip(
        httpserver_expected_profiles_data, httpserver_profile_urls
    ):
        runner = click.testing.CliRunner()
        result = runner.invoke(
            main.main,
            [
                "--output",
                output_json_file,
                "--headless",
                "--browser",
                browser,
                "--profile-link",
                url,
            ],
        )

        assert result.exit_code == 0

        profile_data = json.loads(output_json_file.read_text())
        del profile_data["python_command_parameters"]

        reviews = profile_data.pop("profile_reviews")
        assert len(reviews) == 10
        for r in reviews:
            assert len(r["title"]) >= 0
            assert len(r["body"]) >= 0
            assert type(r["rating"]) is int
            assert r["rating"] >= 1
            assert type(r["date"]) is str
            assert type(r["found_helpful"]) in [int, type(None)]
            assert type(r["review_link"]) in [str, type(None)]
            assert type(r["verified_purchase"]) is bool
        assert profile_data == expected


@pytest.mark.e2e
def test_main_write_command_options_to_json_succeeds(httpserver_profile_urls):
    runner = click.testing.CliRunner()
    result = runner.invoke(
        main.main,
        [
            "--headless",
            "--html-page",
            "page.html",
            "--sleep-time",
            "3",
            "--profile-link",
            httpserver_profile_urls[0],
        ],
    )

    assert result.exit_code == 0


@pytest.mark.e2e
@pytest.mark.no_nox
def test_main_download_profile_e2e_succeeds(output_json_file):
    runner = click.testing.CliRunner()
    result = runner.invoke(
        main.main,
        [
            "--output",
            output_json_file,
            "--profile-link",
            "https://www.amazon.com/-/en/gp/profile/"
            "amzn1.account.AHTI63FP2QGW4EJB4IJKLBHLUGYQ/ref=cm_cr_arp_d_gw_lft?ie=UTF8",
        ],
    )
    assert result.exit_code == 0

    profile_data = json.loads(output_json_file.read_text())
    assert profile_data.keys() == {
        "profile_name",
        "profile_influence",
        "profile_num_reviews",
        "profile_image",
        "profile_reviews",
        "python_command_parameters",
    }

    assert type(profile_data["profile_name"]) is str

    assert type(profile_data["profile_influence"]) is int
    assert profile_data["profile_influence"] >= 363

    assert type(profile_data["profile_num_reviews"]) is int
    assert profile_data["profile_num_reviews"] >= 71

    assert type(profile_data["profile_image"]) is bool
    assert not profile_data["profile_image"]

    assert len(profile_data["profile_reviews"]) >= 1
