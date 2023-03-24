import json
import sys
from typing import Optional

import click
import click_log

from . import __version__
from .scraper import logger, Scraper


@click.command()
@click_log.simple_verbosity_option(logger, show_default=True)
@click.version_option(version=__version__)
@click.argument(
    "link",
    type=str,
)
@click.option(
    "--profiles/--no-profiles",
    help="Download profile information",
    default=True,
    show_default=True,
)
@click.option(
    "--start-page",
    "-s",
    help="From which page should downloading the reviews start",
    type=int,
    default=0,
    show_default=True,
)
@click.option(
    "--stop-page",
    help="At which page should downloading the reviews stop (stop-page is included)",
    type=int,
    default=None,
    show_default=True,
)
@click.option(
    "--output",
    "-o",
    help="Write json output",
    type=click.File("w"),
    default=sys.stdout,
    show_default=True,
)
@click.option(
    "--profile-link/--no-profile-link",
    help="The given link points to a profile and not a product",
    default=False,
    show_default=True,
)
@click.option(
    "--html-page",
    "-p",
    help="Save the last accessed html page (useful for debugging)",
    type=click.File("w"),
)
@click.option(
    "--browser",
    "-b",
    help="Set which browser should be used",
    type=click.Choice(["chrome", "firefox"]),
    default="chrome",
    show_default=True,
)
@click.option(
    "--headless/--no-headless",
    "have_browser_headless",
    help="Run browser in background making it more easily detectable as a web scraper",
    default=False,
    show_default=True,
)
@click.option(
    "--sleep-time",
    help="Time to wait for user input when the 1st request fails",
    type=int,
    default=60,
    show_default=True,
)
def main(
    link: str,
    profiles: bool,
    start_page: int,
    stop_page: Optional[int],
    output: click.File,
    profile_link: bool,
    html_page: click.File,
    browser: str,
    have_browser_headless: bool,
    sleep_time: int,
) -> None:
    """Download amazon product reviews and reviewers profile information

    LINK is an URL to the reviews of an amazon product or to an amazon profile.
    Link must be of the form 'https://www.amazon.com/product-reviews/B01AMT0EYU/' and
    must end with a '/'."
    """
    arr = Scraper(html_page, browser, have_browser_headless)
    if profile_link:
        data = arr.get_profile_data(link)
    else:
        data = arr.extract(link, profiles, start_page, stop_page, sleep_time)

    output.write(json.dumps(data))
