"""Pytest fixtures"""
import json
from pathlib import Path
import tempfile
import shutil
from contextlib import contextmanager

import pytest
from click.testing import CliRunner

TEST_PATH = Path(__file__).parent
TEST_DATA_PATH = TEST_PATH.joinpath("data")
INTEGRATION_DATA_PATH = TEST_DATA_PATH.joinpath("r2r_integration")
FROM_CONFIG_DATA_PATH = TEST_DATA_PATH.joinpath("r2r_from_config")
EXPANDED_DATA_PATH = TEST_DATA_PATH.joinpath("r2r_expanded")
STANDARD_CONFIG_JSON_PATH = FROM_CONFIG_DATA_PATH.joinpath("standard_inputs.json")
NO_BINS_CONFIG_JSON_PATH = FROM_CONFIG_DATA_PATH.joinpath(
    "no_bin_constraint_inputs.json"
)
PRIORITY_INPUTS = FROM_CONFIG_DATA_PATH.joinpath("priority_inputs.json")
MULTI_PRIORITY_INPUTS = FROM_CONFIG_DATA_PATH.joinpath("multiple_priority_inputs.json")
EXPANDED_INPUTS = EXPANDED_DATA_PATH.joinpath("config.json")


@pytest.fixture
def test_cli_runner():
    """Return a click CliRunner for testing commands"""
    return CliRunner()


@pytest.fixture
def test_path():
    """Path to the folder containing tests."""
    return TEST_PATH


@pytest.fixture
def test_data_path():
    """Path to the folder containing test data."""
    return TEST_DATA_PATH


@pytest.fixture
def integration_data_path():
    """Path to the folder containing integration test data
    for ReEDS to reV."""
    return INTEGRATION_DATA_PATH


@pytest.fixture
def from_config_data_path():
    """Path to the folder containing integration test data for the from-config
    command of ReEDS to reV."""
    return FROM_CONFIG_DATA_PATH


@pytest.fixture
def expanded_data_path():
    """Path to the folder containing test data that results in expanded capacity for
    ReEDS to reV."""
    return EXPANDED_DATA_PATH


@pytest.fixture
def hourlize_path():
    """Path to the folder containing the hourlize scripts."""
    return TEST_PATH.parent


@pytest.fixture
def standard_config_json_path():
    """
    Path to a valid configuration json for the reeds_to_rev_cli.py from-config
    command.
    """
    return STANDARD_CONFIG_JSON_PATH


@pytest.fixture
def standard_config_json_data():
    """
    Return data from a standard configuration json for the reeds_to_rev_cli.py
    from-config command.
    """
    with open(STANDARD_CONFIG_JSON_PATH, "r") as f:
        data = json.load(f)

    return data


@pytest.fixture
def no_bin_config_json_data():
    """
    Return data from no bin constraint configuration json for the reeds_to_rev_cli.py
    from-config command.
    """
    with open(NO_BINS_CONFIG_JSON_PATH, "r") as f:
        data = json.load(f)

    return data


@pytest.fixture
def priority_inputs_config_json_data():
    """
    Return data from priority inputs configuration json for the reeds_to_rev_cli.py
    from-config command.
    """
    with open(PRIORITY_INPUTS, "r") as f:
        data = json.load(f)

    return data


@pytest.fixture
def multiple_priority_inputs_config_json_data():
    """
    Return data from multiple priority inputs configuration json for the
    reeds_to_rev_cli.py from-config command.
    """
    with open(MULTI_PRIORITY_INPUTS, "r") as f:
        data = json.load(f)

    return data


@pytest.fixture
def expanded_inputs_config_json_data():
    """
    Return data from configuration json that results in expanded capacity for the
    reeds_to_rev_cli.py from-config command.
    """
    with open(EXPANDED_INPUTS, "r") as f:
        data = json.load(f)

    return data


@pytest.fixture
def test_techs():
    """List of technologies to test."""
    return ["wind-ons", "wind-ofs", "upv", "dupv"]


@contextmanager
def temporary_parent_directory(source_data_path):
    """
    Recursively copies a folder from source_data path to a
    a new tempfile.TemporaryDirectory parent directory.
    To be used as a context manager, e.g.,
    ```with temporary_parent_directory(Path("/my/source/folder")) as temp:
            # do stuff
    ```

    Parameters
    ----------
    source_data_path : pathlib.Path
        Path to folder containing source data to be copied.

    Yields
    ------
    tempfile.TemporaryDirectory
        Temporary directory containing a folder with the name, structure,
        and contents of the source_data_path
    """

    tempdir = tempfile.TemporaryDirectory()
    temp_dir_path = Path(tempdir.name)
    dst_folder = temp_dir_path.joinpath(source_data_path.name)
    shutil.copytree(source_data_path, dst_folder)
    try:
        yield tempdir
    finally:
        tempdir.cleanup()
        assert Path(temp_dir_path).exists() is False
