from copy import deepcopy
from pathlib import Path
import re
from typing import Final

from amarps.scraper import (
    _convert_date,
    AverageRating,
    FoundHelpful,
    MyInteger,
    NumRatings,
    ProfileReviewDate,
    ReviewDate,
    Scraper,
)
import pytest

PROFILES: Final = [
    {"profile_influence": 14, "profile_num_reviews": 53, "profile_image": True},
    {"profile_influence": 404, "profile_num_reviews": 129, "profile_image": False},
]


@pytest.fixture()
def testdata_dir():
    return Path(Path(__file__).parent, "data")


@pytest.fixture()
def httpserver_error_503_url(httpserver):
    httpserver.expect_request("/").respond_with_data("status code 503", 503)
    return httpserver.url_for("/")


@pytest.fixture()
def httpserver_error_404_url(httpserver):
    httpserver.expect_request("/").respond_with_data("status code 404", 404)
    return httpserver.url_for("/")


@pytest.fixture()
def httpserver_profile_urls(testdata_dir, httpserver):
    profiles_dir = Path(testdata_dir, "profiles")

    httpserver.expect_request("/profile1").respond_with_data(
        (profiles_dir / "OeffentlichesProfil1.html").read_text(),
        content_type="text/html",
    )
    profile_img_path = (
        "/OeffentlichesProfil1_files/amzn1.account(1).AGNYXWZ6MSS3E2CTREXYFDJBKYBQ"
    )
    httpserver.expect_request(profile_img_path).respond_with_data(
        (profiles_dir / profile_img_path[1:]).read_bytes(),
        content_type="image/jpeg",
    )
    httpserver.expect_request(profile_img_path).respond_with_data(
        (profiles_dir / profile_img_path[1:]).read_bytes(),
        content_type="image/jpeg",
    )
    profile_img_path = (
        "/OeffentlichesProfil1_files/amzn1.account.AGNYXWZ6MSS3E2CTREXYFDJBKYBQ"
    )
    tmp = profile_img_path.split("/")[-1]
    httpserver.expect_request(re.compile(f".*/{tmp}")).respond_with_data(
        (profiles_dir / profile_img_path[1:]).read_bytes(),
        content_type="image/jpeg",
    )

    httpserver.expect_request("/profile2").respond_with_data(
        (profiles_dir / "OeffentlichesProfil2.html").read_text(),
        content_type="text/html",
    )
    profile_img_path = (
        "/OeffentlichesProfil2_files/amzn1.account(1).AHGZZHFMCPMDOEXDXZM2DYZ2TJRQ"
    )
    httpserver.expect_request(profile_img_path).respond_with_data(
        (profiles_dir / profile_img_path[1:]).read_bytes(),
        content_type="image/jpeg",
    )
    profile_img_path = (
        "/OeffentlichesProfil2_files/amzn1.account.AHGZZHFMCPMDOEXDXZM2DYZ2TJRQ"
    )
    tmp = profile_img_path.split("/")[-1]
    httpserver.expect_request(re.compile(f".*/{tmp}")).respond_with_data(
        (profiles_dir / profile_img_path[1:]).read_bytes(),
        content_type="image/jpeg",
    )

    def prepare(pattern: str, content_type: str, is_binary: bool) -> None:
        for file in profiles_dir.glob(pattern):
            httpserver.expect_request(
                f"/{file.relative_to(profiles_dir)}"
            ).respond_with_data(
                file.read_bytes() if is_binary else file.read_text(),
                content_type=content_type,
            )

    prepare(r"*/*\.js$", "application/javascript", False)

    prepare(r"*/*\.jpg$", "image/jpeg", True)
    prepare(r"*/*\.png$", "image/png", True)
    prepare(r"*/*\.gif$", "image/gif", True)

    prepare(r"*/*\.css$", "text/css", False)

    prepare(r"Oeff*/*\.html$", "text/html", False)

    prepare(r"*/cm$", "text/plain", False)
    prepare(r"*/cms$", "text/plain", False)
    prepare(r"*/saved_resource$", "text/plain", False)
    prepare(r"*/Serving$", "text/plain", False)
    prepare(r"*/sync$", "text/plain", False)

    return [httpserver.url_for("/profile1"), httpserver.url_for("/profile2")]


@pytest.fixture()
def reviews_with_profile_link(httpserver_profile_urls):
    return [
        {"profile_link": httpserver_profile_urls[0], "body": "Content 1"},
        {"profile_link": httpserver_profile_urls[1], "body": "Content 2"},
    ]


@pytest.fixture()
def reviews_with_profile_link_error_403(httpserver, reviews_with_profile_link):
    httpserver.expect_request("/").respond_with_data("status code 403", 403)
    for r in reviews_with_profile_link:
        r["profile_link"] = httpserver.url_for("/")
    return reviews_with_profile_link


@pytest.fixture()
def expected_reviews(reviews_with_profile_link):
    return [{**a, **b} for a, b in zip(reviews_with_profile_link, PROFILES)]


@pytest.fixture()
def headless_chrome_arr():
    return Scraper(have_browser_headless=True)


@pytest.fixture()
def headless_firefox_arr():
    return Scraper(browser="firefox", have_browser_headless=True)


@pytest.fixture(params=["headless_chrome_arr", "headless_firefox_arr"])
def headless_arr(request):
    return request.getfixturevalue(request.param)


def test_Scraper_invalid_browser():
    with pytest.raises(ValueError, match="Invalid browser: invalid"):
        Scraper(browser="invalid")


@pytest.mark.parametrize(
    ("headless_arr", "error_message"),
    [
        ("headless_chrome_arr", "HTTP error: 503"),
        pytest.param(
            "headless_firefox_arr",
            "HTTP error: 500",
            marks=pytest.mark.flaky(reruns=7),
        ),
    ],
)
def test_get_html_data_server_error(
    request, httpserver_error_503_url, headless_arr, error_message
):
    headless_arr = request.getfixturevalue(headless_arr)
    with pytest.raises(ValueError, match=error_message):
        headless_arr._get_html_data(httpserver_error_503_url)


@pytest.mark.parametrize(
    "headless_arr",
    [
        "headless_chrome_arr",
        pytest.param(
            "headless_firefox_arr",
            marks=pytest.mark.xfail(reason="Trouble getting HTTP status"),
        ),
    ],
)
def test_get_html_data_client_error(request, httpserver_error_404_url, headless_arr):
    headless_arr = request.getfixturevalue(headless_arr)
    with pytest.raises(ValueError, match="HTTP error: 404"):
        headless_arr._get_html_data(httpserver_error_404_url)


@pytest.mark.e2e
@pytest.mark.parametrize(
    ("headless_arr", "check_status"),
    [
        ("headless_chrome_arr", True),
        pytest.param(
            "headless_firefox_arr",
            True,
            marks=pytest.mark.xfail(reason="Trouble getting HTTP status"),
        ),
        ("headless_firefox_arr", False),
    ],
)
def test_get_html_data_succeeds(request, headless_arr, check_status):
    headless_arr = request.getfixturevalue(headless_arr)
    html_page = headless_arr._get_html_data("http://www.example.com", check_status)
    assert "This domain is for use in illustrative examples in documents." in html_page


@pytest.mark.flaky(reruns=10)
def test_get_profile_data(headless_arr, httpserver_profile_urls):
    for expected, url in zip(PROFILES, httpserver_profile_urls):
        profile_data = headless_arr.get_profile_data(url)

        reviews = profile_data.pop("profile_reviews")
        assert len(reviews) == 10
        for r in reviews:
            assert len(r["title"]) >= 0
            assert len(r["body"]) >= 0
            assert r["rating"] >= 1
        assert profile_data == expected


@pytest.mark.flaky(reruns=10)
def test_add_profiles(headless_arr, reviews_with_profile_link, expected_reviews):
    reviews = deepcopy(reviews_with_profile_link)
    expected_reviews = expected_reviews
    headless_arr._add_profiles(reviews)

    profile_reviews_list = [r.pop("profile_reviews") for r in reviews]
    assert len(profile_reviews_list) == len(reviews)
    assert all([len(profile_reviews) > 0 for profile_reviews in profile_reviews_list])
    assert reviews == expected_reviews


def test_add_profiles_http_error_403(
    headless_chrome_arr, reviews_with_profile_link_error_403
):
    reviews = deepcopy(reviews_with_profile_link_error_403)[0:1]
    headless_chrome_arr._add_profiles(reviews)

    assert len(reviews) == 1
    assert "profile_influence" not in reviews[0]
    assert "profile_num_reviews" not in reviews[0]
    assert "profile_error" in reviews[0]


@pytest.mark.parametrize(
    "average_rating", ["4.2 out of 5.0", "4.1 out of 5.0", "4,2 von 5", "4,8 von 5"]
)
def test_format_AverageRating_succeeds(average_rating):
    average_rating = AverageRating().format(average_rating)
    assert type(average_rating) is float
    assert 1.0 <= average_rating <= 5.0


@pytest.mark.parametrize(
    "average_rating",
    ["", "4.1outof5.0", "4,1von5", "4,2von 5", " ", " 4,2", " 4.2"],
)
def test_format_AverageRating_fails(average_rating):
    with pytest.raises(ValueError):
        AverageRating().format(average_rating)


@pytest.mark.parametrize(
    "found_helpful",
    [
        "one person found this helpful",
        "one personfound this helpful",
        "2 people found this helpful",
        "2 peoplefound this helpful",
        "3 (ignored humans) found this helpful, this is also ignored",
        "-1 people found this helpful",  # should not happen
        None,
    ],
)
def test_format_FoundHelpful_succeeds(found_helpful):
    found_helpful = FoundHelpful().format(found_helpful)
    assert type(found_helpful) is int


@pytest.mark.parametrize(
    "found_helpful",
    [
        "oe person found this helpful",
        "2people found this helpful",
        "2.3 people found this helpful",
        "",
    ],
)
def test_format_FoundHelpful_fails(found_helpful):
    with pytest.raises(ValueError):
        FoundHelpful().format(found_helpful)


@pytest.mark.parametrize(
    "date,expected", [("Jan 3, 2023", "2023/01/03"), ("November 5, 2020", "2020/11/05")]
)
def test__convert_date(date, expected):
    assert _convert_date(date) == expected


INVALID_REVIEW_DATES = ["", "No date", "on", "2022/02/22", " - ", " · "]


@pytest.mark.parametrize("review_date", INVALID_REVIEW_DATES)
def test_format_ReviewDate_invalid(review_date):
    with pytest.raises(ValueError):
        ReviewDate().format(review_date)


@pytest.mark.parametrize("review_date", INVALID_REVIEW_DATES)
def test_format_ProfileReviewDate_invalid(review_date):
    with pytest.raises(ValueError):
        ProfileReviewDate().format(review_date)


@pytest.mark.parametrize(
    "value,expected", [("1", 1), ("11", 11), ("1.111", 1111), ("1,111", 1111)]
)
def test_format_MyInteger(value, expected):
    formatter = MyInteger()
    assert formatter.format(value) == expected


@pytest.mark.parametrize(
    "value,expected",
    [
        ("1234 global ratings", 1234),
        ("1234 globale Bewertungen", 1234),
        ("1234 global", 1234),
    ],
)
def test_format_NumRatings(value, expected):
    formatter = NumRatings()
    assert formatter.format(value) == expected


@pytest.mark.parametrize("value", ["", "1234", "123 ", "1 word", "1 globa"])
def test_format_NumRatings_invalid(value):
    with pytest.raises(ValueError):
        NumRatings().format(value)
