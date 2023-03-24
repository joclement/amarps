import importlib.resources
import json
import logging
from math import isclose
import sys
from time import sleep
from typing import Any, Dict, Final, List, Optional, Union

from click import File
import dateparser
import requests
from selectorlib import Extractor
from selectorlib.formatter import Formatter
from seleniumwire import webdriver


logger = logging.getLogger(__name__)


def _get_page_url(base_url: str, page: int) -> str:
    return base_url + f"ref=cm_cr_arp_d_paging_btm_next_{page}?pageNumber={page}"


def _convert_date(value: str) -> str:
    logger.debug(value)

    date = dateparser.parse(value)
    if date is None:
        raise ValueError(f"Not a suitable date: {date}")

    return date.strftime("%Y/%m/%d")


def _split(value: str, sep: str, maxsplit: int = 1) -> List[str]:
    parts = value.split(sep, maxsplit)
    if len(parts) < 2:
        raise ValueError(f"Input '{value}' not splittable with separator '{sep}'")
    logger.debug(parts)
    return parts


class ReviewDate(Formatter):
    def format(self, date: str) -> str:
        return _convert_date(" ".join(_split(date, " ", 10)[-3:]))


class ProfileReviewDate(Formatter):
    def format(self, date: str) -> str:
        return _convert_date(_split(date, " · ")[-1])


def _convert_rating(rating: str) -> float:
    logger.debug(rating)
    return float(_split(rating, " ")[0].replace(",", ".", 1))


class AverageRating(Formatter):
    def format(self, rating: str) -> float:
        return _convert_rating(rating)


class ReviewRating(Formatter):
    def format(self, rating: str) -> Optional[int]:
        try:
            return int(_convert_rating(rating))
        except TypeError as e:
            logger.error(e)
            return None


def _convert_integer(number: str) -> int:
    logger.debug(number)
    return int(number.replace(",", "", 1).replace(".", "", 1))


class MyInteger(Formatter):
    def format(self, integer: str) -> int:
        return _convert_integer(integer)


class NumRatings(Formatter):
    def format(self, num_ratings: str) -> int:
        return _convert_integer(_split(num_ratings, " global")[0])


class FoundHelpful(Formatter):
    def format(self, found_helpful: Optional[str]) -> int:
        logger.debug(found_helpful)
        if found_helpful is None:
            return 0
        found_helpful = _split(found_helpful, " ")[0]
        if found_helpful.lower() in ["one", "eine"]:
            return 1
        else:
            return int(found_helpful)


class VerifiedPurchase(Formatter):
    def format(self, verified_purchase: Optional[str]) -> bool:
        logger.debug(verified_purchase)
        return (
            verified_purchase is not None and "Verified Purchase" in verified_purchase
        )


class HttpError(Exception):
    def __init__(self, status_code: int):
        self.status_code = status_code

    def __str__(self):
        return f"HTTP error: {self.status_code}"


def _init_browser_driver(
    browser: str, have_browser_headless: bool
) -> Union[webdriver.Chrome, webdriver.Firefox]:
    if browser == "chrome":
        from selenium.webdriver.chrome.service import Service
        from seleniumwire.webdriver import Chrome as BrowserDriver
        from seleniumwire.webdriver import ChromeOptions as BrowserDriverOptions
        from webdriver_manager.chrome import ChromeDriverManager as BrowserDriverManager
    elif browser == "firefox":
        from selenium.webdriver.firefox.service import Service
        from seleniumwire.webdriver import Firefox as BrowserDriver
        from seleniumwire.webdriver import FirefoxOptions as BrowserDriverOptions
        from webdriver_manager.firefox import GeckoDriverManager as BrowserDriverManager
    else:
        raise ValueError(f"Invalid browser: {browser}")

    options = BrowserDriverOptions()
    options.set_capability("loggingPrefs", {"performance": "ALL"})
    if have_browser_headless:
        options.add_argument("--headless")
    return BrowserDriver(
        options=options,
        service=Service(BrowserDriverManager().install()),
    )


class ImageSrcToBool(Formatter):
    def format(self, image_url: str) -> Optional[bool]:
        response = requests.get(image_url)
        if not response.ok:
            return None
        return not isclose(len(response.content), 7186, rel_tol=0.05)


class Scraper:
    def __init__(
        self,
        html_page_writer: Optional[File] = None,
        browser: str = "chrome",
        have_browser_headless: bool = False,
    ):
        self._html_page_writer = html_page_writer
        self.have_browser_headless = have_browser_headless
        self._webdriver = _init_browser_driver(browser, self.have_browser_headless)

        self._review_extractor = Extractor.from_yaml_string(
            importlib.resources.read_text("amarps", "review_page_selectors.yml"),
            formatters=Formatter.get_all(),
        )
        self._profile_extractor = Extractor.from_yaml_string(
            importlib.resources.read_text("amarps", "profile_page_selectors.yml"),
            formatters=Formatter.get_all(),
        )

        self._IGNORE_PROFILE_HTTP_STATUS_CODES: Final = [403, 503]

    def __del__(self):
        if hasattr(self, "_webdriver"):
            self._webdriver.close()

    def _raise_for_status(self) -> None:
        try:
            status = self._webdriver.last_request.response.status_code
            if status >= 400:
                raise HttpError(status)
        except AttributeError:
            logger.warning("Failed to get HTTP status code")

    def _get_html_data(self, url: str, check_status: bool = True) -> str:
        logger.info(f"Download {url}")

        self._webdriver.get(url)
        self._webdriver.execute_script("window.scrollTo(0,20)")

        html_page = self._webdriver.page_source
        if self._html_page_writer is not None:
            self._html_page_writer.write(html_page)

        if check_status:
            self._raise_for_status()

        return html_page

    def _get_data(self, url: str) -> Dict[str, Any]:
        return self._review_extractor.extract(self._get_html_data(url), base_url=url)

    def get_profile_data(self, url: str) -> Dict[str, Any]:
        try:
            logger.info(f"Download profile {url}")
            profile_data = self._profile_extractor.extract(
                self._get_html_data(url), base_url=url
            )
            logger.info(json.dumps(profile_data, indent=4))
        except TypeError as e:
            logger.error(e)
            profile_data["profile_error"] = f"Error: {e}"

        return profile_data

    def _add_profiles(self, reviews: List[Dict[str, Any]]) -> None:
        for review in reviews:
            if review["profile_link"] is not None:
                try:
                    profile_data = self.get_profile_data(review["profile_link"])
                    if profile_data["profile_reviews"] is None:
                        profile_data["profile_error"] = "No data could be extracted"
                except HttpError as e:
                    logger.error(e)
                    profile_data = {"profile_error": str(e)}
                    if e.status_code not in self._IGNORE_PROFILE_HTTP_STATUS_CODES:
                        raise
                review.update(profile_data)
            else:
                logger.warning("No profile link was extracted")

    def _get_reviews(
        self,
        base_url: str,
        data: Dict[str, Any],
        start_page: int,
        stop_page: Optional[int],
    ) -> List[Dict[str, Any]]:
        reviews = []
        page = start_page
        if stop_page is None:
            stop_page = sys.maxsize
        current_url = _get_page_url(base_url, page)
        reviews_exist = True
        reviews_data = data["reviews"]

        while reviews_exist and page <= stop_page:
            reviews_exist = False
            logger.info(json.dumps(reviews_data, indent=4))

            for r in reviews_data:
                r["url"] = current_url
                reviews.append(r)

            page += 1
            current_url = _get_page_url(base_url, page)
            next_page_data = self._get_data(current_url)
            if "reviews" in next_page_data and next_page_data["reviews"] is not None:
                reviews_exist = True
                reviews_data = next_page_data["reviews"]
                review_count = len(reviews_data)
                logger.info(f"number reviews: {review_count}")

        return reviews

    def extract(
        self,
        base_url: str,
        download_profiles: bool,
        start_page: int,
        stop_page: Optional[int],
        sleep_time: int,
    ) -> Dict[str, Any]:
        data = self._get_data(_get_page_url(base_url, start_page))

        if data["reviews"] is None or len(data["reviews"]) == 0:
            logger.warning("Failed to extract review data")
            if not self.have_browser_headless:
                logger.warning(
                    f"The query will be retried in {sleep_time} seconds, "
                    "please try to solve a CAPTCHA or login if possible"
                )
                sleep(sleep_time)
                data = self._get_data(_get_page_url(base_url, start_page))

        data["reviews"] = self._get_reviews(base_url, data, start_page, stop_page)

        if download_profiles:
            self._add_profiles(data["reviews"])

        return data
