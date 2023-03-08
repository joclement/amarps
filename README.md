[![Tests](https://github.com/joclement/amarps/workflows/Tests/badge.svg)](https://github.com/joclement/amarps/actions?workflow=Tests)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/joclement/amarps/main.svg)](https://results.pre-commit.ci/latest/github/joclement/amarps/main)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Versions](https://img.shields.io/pypi/pyversions/amarps)](https://img.shields.io/pypi/pyversions/amarps)

# Amazon Review Profile Scraper

A very basic tool to scrape the user reviews of a product on Amazon the profiles that created those reviews.

It is intended to be used for research to analyze the quality of a user review based on
other information belonging to the user.

## Usage

1. Install this tool `pip install amarps`.
2. Run `python -m amarps --help` to check the usage
3. Run e.g. `python -m amarps https://www.amazon.com/product-reviews/B07ZPL752N/`
