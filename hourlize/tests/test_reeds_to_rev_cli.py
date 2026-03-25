"""Tests for ReEDS to reV click CLI"""
import json
from pathlib import Path
import tempfile
from collections import OrderedDict

import pandas as pd
from pandas.testing import assert_frame_equal
import pytest
from conftest import temporary_parent_directory
import path_fix as _

import reeds_to_rev_cli
from reeds_to_rev_cli import main


def test_main(test_cli_runner):
    """Test main() CLI command."""
    result = test_cli_runner.invoke(main)
    assert result.exit_code == 0


def test_run(test_cli_runner, test_techs, integration_data_path):
    """
    Integration test of run() CLI command to ensure
    it returns the expected outputs. This test covers the following techs:
    upv, wind-ons, wind-ofs.

    This is consistent with test_reeds_to_rev.test_reeds_to_rev_integration().
    """

    sc_path = integration_data_path.joinpath("supply_curves")
    reeds_source_path = integration_data_path.joinpath("reeds")

    with temporary_parent_directory(reeds_source_path) as temp_reeds:
        reeds_path = Path(temp_reeds.name)
        run_folder = reeds_path.joinpath("reeds")

        for tech in test_techs:
            result = test_cli_runner.invoke(
                main,
                [
                    "run",
                    reeds_path.as_posix(),
                    run_folder.as_posix(),
                    "--reduced_only",
                    "--tech",
                    tech,
                    "--sc_path",
                    sc_path.as_posix(),
                ],
            )
            assert result.exit_code == 0, "Command encountered an error"

            out_csv_name = f"df_sc_out_{tech}_reduced.csv"
            result_csv_path = run_folder.joinpath("outputs", out_csv_name)
            assert result_csv_path.exists()

            expected_csv_path = integration_data_path.joinpath(
                "expected_results", out_csv_name
            )
            assert expected_csv_path.exists()

            result_df = pd.read_csv(result_csv_path)
            expected_df = pd.read_csv(expected_csv_path)

            assert_frame_equal(result_df, expected_df)


def test_load_config_happy(standard_config_json_data):
    """
    Happy path test for load_config() function. Should load a valid config
    without raising any exceptions.
    """
    reeds_to_rev_cli.validate_config(standard_config_json_data)


def test_load_config_missing_param_error(standard_config_json_data):
    """
    Test that load_config() function raises a ConfigurationError when a required
    parameter is missing.
    """

    standard_config_json_data.pop("reeds_path")
    with pytest.raises(reeds_to_rev_cli.ConfigError):
        reeds_to_rev_cli.validate_config(standard_config_json_data)


def test_load_config_unknown_param_error(standard_config_json_data):
    """
    Test that load_config() function raises a ConfigurationError when an unknown/extra
    parameter is provided.
    """

    standard_config_json_data["unknown"] = "not a parameter"
    with pytest.raises(reeds_to_rev_cli.ConfigError):
        reeds_to_rev_cli.validate_config(standard_config_json_data)


def test_load_config_wrong_param_dtype_error(standard_config_json_data):
    """
    Test that load_config() function raises a ConfigurationError when a parameter
    has the wrong dtype
    """

    standard_config_json_data["reeds_path"] = True
    with pytest.raises(reeds_to_rev_cli.ConfigError):
        reeds_to_rev_cli.validate_config(standard_config_json_data)


def test_load_config_tech_supply_curves_error(standard_config_json_data):
    """
    Test that load_config() function raises a ConfigurationError when something is wrong
    with the tech_supply_curves parameter.
    """

    standard_config_json_data["tech_supply_curves"]["will_power"] = "/path/to/a/sc.csv"
    with pytest.raises(reeds_to_rev_cli.ConfigError):
        reeds_to_rev_cli.validate_config(standard_config_json_data)


def test_load_config_priority_error(standard_config_json_data):
    """
    Test that load_config() function raises a ConfigurationError when something is wrong
    with the priority parameter.
    """

    standard_config_json_data["priority"]["*cost_col*"] = "alternating"
    with pytest.raises(reeds_to_rev_cli.ConfigError):
        reeds_to_rev_cli.validate_config(standard_config_json_data)


def test_validate_tech_supply_curves_happy(standard_config_json_data):
    """
    Happy path test for validate_tech_supply_curves. Check that no error messages are
    returned when valid data is provided.
    """

    tech_supply_curves = standard_config_json_data["tech_supply_curves"]
    errors = reeds_to_rev_cli.validate_tech_supply_curves(tech_supply_curves)
    assert len(errors) == 0


def test_validate_tech_supply_curves_bad_tech(standard_config_json_data):
    """
    Test that validate_tech_supply_curves returns an error message if an invalid
    technology is provided.
    """

    tech_supply_curves = standard_config_json_data["tech_supply_curves"]
    tech_supply_curves["bicycle_power"] = "/path/to/bike_power_sc.csv"
    errors = reeds_to_rev_cli.validate_tech_supply_curves(tech_supply_curves)
    assert len(errors) == 1


def test_validate_tech_supply_curves_bad_path(standard_config_json_data):
    """
    Test that validate_tech_supply_curves returns an error message if an invalid
    file path is provided for a technology.
    """

    tech_supply_curves = standard_config_json_data["tech_supply_curves"]
    tech_supply_curves["upv"] = False
    errors = reeds_to_rev_cli.validate_tech_supply_curves(tech_supply_curves)
    assert len(errors) == 1


def test_validate_priority_happy(standard_config_json_data):
    """
    Happy path test for validate_priority. Check that no error messages are
    returned when valid data is provided.
    """

    priority = standard_config_json_data["priority"]
    errors = reeds_to_rev_cli.validate_priority(priority)
    assert len(errors) == 0


def test_validate_priority_bad_column(standard_config_json_data):
    """
    Test that validate_priority returns an error message if an invalid
    column is provided (i.e., not a string.)
    """

    priority = standard_config_json_data["priority"]
    priority[1] = "ascending"
    errors = reeds_to_rev_cli.validate_priority(priority)
    assert len(errors) == 1


def test_validate_priority_bad_sort_order(standard_config_json_data):
    """
    Test that validate_priority returns an error message if an invalid
    sort order is provided.
    """

    priority = standard_config_json_data["priority"]
    priority["*cost_col*"] = "alternating"
    errors = reeds_to_rev_cli.validate_priority(priority)
    assert len(errors) == 1


def test_get_priority_from_config_happy():
    """
    Check that the get_priority_from_config() returns columns in the expected order
    when the inputs are already ordered in ascending order.
    """

    config = OrderedDict(
        {
            "priority": {
                "a": "descending",
                "b": "ascending",
                "c": "descending",
                "d": "ascending",
            }
        }
    )
    cost_col = "supply_curve_cost_per_mw"
    priority = reeds_to_rev_cli.get_priority_from_config(config, cost_col)
    expected_key_order = ["a", "b", "c", "d"]
    expected_value_order = ["descending", "ascending", "descending", "ascending"]

    assert list(priority.keys()) == expected_key_order
    assert list(priority.values()) == expected_value_order


def test_get_priority_from_config_random():
    """
    Check that the get_priority_from_config() returns columns in the expected order
    when the inputs are in a random order.
    """

    config = OrderedDict(
        {
            "priority": {
                "b": "ascending",
                "d": "ascending",
                "a": "descending",
                "c": "descending",
            }
        }
    )
    cost_col = "supply_curve_cost_per_mw"
    priority = reeds_to_rev_cli.get_priority_from_config(config, cost_col)
    expected_key_order = ["b", "d", "a", "c"]
    expected_value_order = ["ascending", "ascending", "descending", "descending"]

    assert list(priority.keys()) == expected_key_order
    assert list(priority.values()) == expected_value_order


def test_get_priority_from_config_cost_col():
    """
    Check that the get_priority_from_config() returns columns in the expected order
    when the inputs are in a random order and *cost_col* substitution is required.
    """

    config = OrderedDict(
        {
            "priority": {
                "b": "ascending",
                "a": "descending",
                "*cost_col*": "ascending",
                "d": "ascending",
                "c": "descending",
            }
        }
    )
    cost_col = "supply_curve_cost_per_mw"
    priority = reeds_to_rev_cli.get_priority_from_config(config, cost_col)
    expected_key_order = ["b", "a", cost_col, "d", "c"]
    expected_value_order = [
        "ascending",
        "descending",
        "ascending",
        "ascending",
        "descending",
    ]

    assert list(priority.keys()) == expected_key_order
    assert list(priority.values()) == expected_value_order


def from_config_integration_helper(
    test_cli_runner, config_data, data_path, expected_outputs_data_path
):
    """
    Helper function for subsequent integration tests of from-config command.
    Handles all of the set up of data and testing, but inputs can be varied to use
    different configurations and expected outputs.

    Parameters
    ----------
    test_cli_runner : click.testing.CliRunner
        Used for running the from-config command.
    config_data : dict
        Configuration data for from-config.
    data_path : pathlib.Path
        Path to the folder containing the input data used for integration testing.
    expected_outputs_data_path : pathlib.Path
        Path to the folder containing the expected output data.
    """

    with tempfile.TemporaryDirectory() as out_dir:
        out_dir_path = Path(out_dir)
        # copy over the config to a new file, filling in actual integration_data_path
        temp_config = out_dir_path.joinpath("inputs_config.json")
        config_contents = json.dumps(config_data)
        config_contents = config_contents.replace("DATA_PATH", data_path.as_posix())
        with open(temp_config, "w") as f:
            f.write(config_contents)

        result = test_cli_runner.invoke(
            main, ["from-config", temp_config.as_posix(), out_dir]
        )
        assert result.exit_code == 0, "Command encountered an error"

        for tech in config_data["tech_supply_curves"]:
            out_csv_name = f"df_sc_out_{tech}_reduced.csv"
            result_csv_path = out_dir_path.joinpath(out_csv_name)
            assert result_csv_path.exists()

            expected_csv_path = expected_outputs_data_path.joinpath(out_csv_name)
            assert expected_csv_path.exists()

            result_df = pd.read_csv(result_csv_path)
            expected_df = pd.read_csv(expected_csv_path)

            assert_frame_equal(result_df, expected_df)


def test_from_config_standard_inputs(
    test_cli_runner, standard_config_json_data, integration_data_path
):
    """
    Integration test for from_config() CLI command. Ensure that it produces the expected
    outputs when passed a configuration file with "standard" inputs, which are
    consistent with the standard way of running rev_to_reeds.
    """
    from_config_integration_helper(
        test_cli_runner,
        standard_config_json_data,
        integration_data_path,
        integration_data_path.joinpath("expected_results"),
    )


def test_from_config_no_bin_constraint_inputs(
    test_cli_runner,
    no_bin_config_json_data,
    integration_data_path,
    from_config_data_path,
):
    """
    Integration test for from_config() CLI command. Ensure that it produces the expected
    outputs when passed a configuration file with constrain_on_bins = False, which is
    not the standard way of running ReEDS to reV.
    """
    from_config_integration_helper(
        test_cli_runner,
        no_bin_config_json_data,
        integration_data_path,
        from_config_data_path.joinpath("expected_results", "no_bin_constraint"),
    )


def test_from_config_priority_inputs(
    test_cli_runner,
    priority_inputs_config_json_data,
    integration_data_path,
    from_config_data_path,
):
    """
    Integration test for from_config() CLI command. Ensure that it produces the expected
    outputs when passed a configuration file with a non-standard input for the priority
    input.
    """

    from_config_integration_helper(
        test_cli_runner,
        priority_inputs_config_json_data,
        integration_data_path,
        from_config_data_path.joinpath("expected_results", "priority_inputs"),
    )


def test_from_config_multiple_priority_inputs(
    test_cli_runner,
    multiple_priority_inputs_config_json_data,
    integration_data_path,
    from_config_data_path,
):
    """
    Integration test for from_config() CLI command. Ensure that it produces the expected
    outputs when passed a configuration file with multiple priority columns. This
    helps ensure that priorities are not incorrectly reordered anywhere in the code.
    """

    from_config_integration_helper(
        test_cli_runner,
        multiple_priority_inputs_config_json_data,
        integration_data_path,
        from_config_data_path.joinpath("expected_results", "multiple_priority_inputs"),
    )


def test_from_config_expanded_capacity(
    test_cli_runner,
    expanded_inputs_config_json_data,
    expanded_data_path,
):
    """
    Test specific configuration for reeds to rev that results in expanded capacity
    for supply curve points. This test covers a former bug that was resulting in
    underreporting of the disaggregated capacity.
    """

    from_config_integration_helper(
        test_cli_runner,
        expanded_inputs_config_json_data,
        expanded_data_path,
        expanded_data_path.joinpath("expected_results"),
    )


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
