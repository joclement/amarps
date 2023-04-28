import os
from signal import SIGINT
import threading
import time

from amarps.events import WaitHandler
import pytest


@pytest.fixture()
def call_sigint():
    pid = os.getpid()

    def sigint():
        time.sleep(3)
        os.kill(pid, SIGINT)

    thread = threading.Thread(target=sigint)
    thread.daemon = True
    thread.start()


def test_WaitHandler_simple_succeeds():
    handler = WaitHandler()
    handler.wait(1)


def test_WaitHandler_negative_succeeds():
    handler = WaitHandler()
    start = time.time()
    handler.wait(-1)
    assert time.time() - start < 1


def test_WaitHandler_twice_succeeds():
    handler = WaitHandler()
    start = time.time()
    handler.wait(1)
    handler.wait(2)
    assert time.time() - start > 3


def test_WaitHandler_interrupt_succeeds(call_sigint):
    handler = WaitHandler()
    start = time.time()
    handler.wait(33)
    assert time.time() - start < 7
