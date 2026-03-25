import os
import json
import pytest

DATA_TEST_DIR = "data"

def pytest_addoption(parser):
    parser.addoption("--casepath", action="store", help="File path to ReEDS run.")


# Read file map
@pytest.fixture()
def fmap(request):
    tests_dir = os.path.dirname(request.module.__file__)
    data_filename = os.path.join(tests_dir, DATA_TEST_DIR, "r2x_files.json")
    with open(data_filename, "r") as f:
        return json.load(f)


# Get folder of ReEDS path
@pytest.fixture()
def casepath(pytestconfig):
    return pytestconfig.getoption("casepath")
