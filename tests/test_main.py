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
@pytest.mark.xfail(reason="Probably server prevents access")
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
    assert result.exit_code == 0


@pytest.mark.e2e
@pytest.mark.xfail(reason="Probably server prevents access")
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
    assert result.exit_code == 0


# TODO make test pass again
@pytest.mark.e2e
@pytest.mark.no_nox
@pytest.mark.skip(reason="Fails currently")
def test_main_download_profile_succeeds(output_json_file):
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
    assert len(profile_data) == 4
    assert type(profile_data["profile_influence"]) is int
    assert profile_data["profile_influence"] >= 363
    assert type(profile_data["profile_num_reviews"]) is int
    assert profile_data["profile_num_reviews"] >= 71
    assert type(profile_data["profile_image"]) is bool
    assert not profile_data["profile_image"]
    assert len(profile_data["profile_reviews"]) >= 1
