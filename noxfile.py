import os

import nox
from nox_poetry import Session, session


nox.options.sessions = "lint", "pre_commit", "mypy", "tests"
LOCATIONS = "src", "tests", "noxfile.py"


@session(python=["3.8", "3.9", "3.10", "3.11"])
def tests(session: Session) -> None:
    args = session.posargs or [
        "--cov=amarps",
        "-m",
        "not no_nox",
        "--random-order",
        "-n",
        "auto",
    ]
    session.install(".")
    session.install(
        "pytest",
        "pytest-cov",
        "pytest-httpserver",
        "pytest-random-order",
        "pytest-rerunfailures",
        "pytest-xdist",
    )
    session.run("pytest", env={"GITHUB_TOKEN": os.environ["GITHUB_TOKEN"]}, *args)


@session(python="3.9")
def lint(session: Session) -> None:
    session.install("flake8", "flake8-import-order")
    session.run("flake8", *LOCATIONS)


@session(python="3.9")
def pre_commit(session: Session) -> None:
    session.install("pre-commit")
    session.run("pre-commit", "run", "-a")


@session(python="3.9")
def mypy(session: Session) -> None:
    args = [
        "--allow-untyped-decorators",
        "--disable-error-code",
        "return",
        "src",
    ]
    session.install("mypy")
    session.run("mypy", *args)
