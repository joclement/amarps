from copy import deepcopy

from amarps.scraper import (
    _convert_date,
    AverageRating,
    FoundHelpful,
    HttpError,
    MyInteger,
    NumRatings,
    ProfileReviewDate,
    ReviewDate,
    Scraper,
)
import pytest


@pytest.fixture()
def httpserver_error_503_url(httpserver):
    httpserver.expect_request("/").respond_with_data("status code 503", 503)
    return httpserver.url_for("/")


@pytest.fixture()
def httpserver_error_404_url(httpserver):
    httpserver.expect_request("/").respond_with_data("status code 404", 404)
    return httpserver.url_for("/")


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
def expected_reviews(reviews_with_profile_link, httpserver_expected_profiles_data):
    return [
        {**a, **b}
        for a, b in zip(reviews_with_profile_link, httpserver_expected_profiles_data)
    ]


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
    "headless_arr",
    [
        "headless_chrome_arr",
        pytest.param("headless_firefox_arr", marks=pytest.mark.flaky(reruns=7)),
    ],
)
def test_get_html_data_server_error(request, httpserver_error_503_url, headless_arr):
    headless_arr = request.getfixturevalue(headless_arr)
    with pytest.raises(HttpError, match="HTTP error: 50[0|3]"):
        headless_arr._get_html_data(httpserver_error_503_url, 0)


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
    with pytest.raises(HttpError, match="HTTP error: 404"):
        headless_arr._get_html_data(httpserver_error_404_url, 0)


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
    html_page = headless_arr._get_html_data("http://www.example.com", 0, check_status)
    assert "This domain is for use in illustrative examples in documents." in html_page


@pytest.mark.flaky(reruns=10)
def test_get_profile_data(
    headless_arr, httpserver_profile_urls, httpserver_expected_profiles_data
):
    for expected, url in zip(
        httpserver_expected_profiles_data, httpserver_profile_urls
    ):
        profile_data = headless_arr.get_profile_data(url)

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


def test_get_profile_data_http_error_403(
    headless_chrome_arr, reviews_with_profile_link_error_403
):
    review = deepcopy(reviews_with_profile_link_error_403)[0]
    profile_data = headless_chrome_arr.get_profile_data(review["profile_link"])

    assert "profile_name" not in profile_data
    assert "profile_influence" not in profile_data
    assert "profile_num_reviews" not in profile_data
    assert "profile_error" in profile_data


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
    assert AverageRating().format(average_rating) == average_rating


@pytest.mark.parametrize(
    "found_helpful",
    [
        "one person found this helpful",
        "one personfound this helpful",
        "2 people found this helpful",
        "2 peoplefound this helpful",
        "3 (ignored humans) found this helpful, this is also ignored",
        "1,384 people found this helpful",
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


@pytest.mark.parametrize(
    "inputValue,expected",
    [
        ("aus den Vereinigten Staaten vom 23. Januar 2023", "2023/01/23"),
        ("aus den USA 🇺🇸 am 23. Januar 2023", "2023/01/23"),
    ],
)
def test_format_ReviewDate(inputValue, expected):
    assert ReviewDate().format(inputValue) == expected


INVALID_REVIEW_DATES = ["", "No date", "on", "2022/02/22", " - ", " · "]


@pytest.mark.parametrize("review_date", INVALID_REVIEW_DATES)
def test_format_ReviewDate_invalid(review_date):
    assert ReviewDate().format(review_date) == review_date


@pytest.mark.parametrize("review_date", INVALID_REVIEW_DATES)
def test_format_ProfileReviewDate_invalid(review_date):
    assert ProfileReviewDate().format(review_date) == review_date


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
    assert NumRatings().format(value) == value
