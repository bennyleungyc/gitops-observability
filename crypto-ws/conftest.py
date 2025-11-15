import pytest
import threading
from py4j.java_gateway import JavaGateway, CallbackServerParameters

from py4j_python_implementation.ProtocolClient import ProtocolClient


def declare_listner():
    gateway = JavaGateway(
        callback_server_parameters=CallbackServerParameters())
    listener = ProtocolClient(gateway)
    app = gateway.entry_point
    app.registerListener(listener)
    return listener


# def pytest_configure(config):
#     print("111111")
#     config.addinivalue_line("markers", "slow: mark test as slow to run")
#     listener = declare_listner()
#     listener.connect()
#     pytest.fix_listener = listener


@pytest.fixture(scope='session')
def fix_listener(pytestconfig):
    # thread = threading.Thread(target=declare_listner)
    # thread.setDaemon(True)
    # thread.daemon = True
    # thread.start()

    fix_listener = declare_listner()
    fix_listener.connect()
    return fix_listener


def pytest_sessionstart(session):
    """
    Called after the Session object has been created and
    before performing collection and entering the run test loop.
    """


def pytest_sessionfinish(session, exitstatus):
    # fix_listener.
    """
    Called after whole test run finished, right before
    returning the exit status to the system.
    """


def pytest_unconfigure(config):
    """
    called before test process is exited.
    """


# content of plugins/example_plugin.py
def pytest_configure(config):
    pass


def pytest_unconfigure(config):
    pass
