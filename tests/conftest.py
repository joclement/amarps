from pathlib import Path
import re
from typing import Final

import pytest


def pytest_configure(config):
    config.addinivalue_line("markers", "e2e: end-to-end test.")
    config.addinivalue_line("markers", "no_nox: skip test on nox.")


PROFILES: Final = [
    {
        "profile_name": "NAME1",
        "profile_influence": 14,
        "profile_num_reviews": 53,
        "profile_image": True,
    },
    {
        "profile_name": "name2",
        "profile_influence": 404,
        "profile_num_reviews": 129,
        "profile_image": False,
    },
]


@pytest.fixture()
def httpserver_expected_profiles_data():
    return PROFILES


@pytest.fixture()
def testdata_dir():
    return Path(Path(__file__).parent, "data")


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
