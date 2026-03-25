"""
Tests for reeds_to_rev
"""
import logging
from pathlib import Path
import runpy
import sys
from conftest import temporary_parent_directory

import pandas as pd
from pandas.testing import assert_frame_equal
import pytest


def remove_stream_handlers(logger_name):
    """
    Removes any existing StreamHandlers from the logger named
    ``""``. This is necessary to avoid duplicate (or more) messages
    logging to stdout when running multiple tests involving reeds_to_rev.
    """

    stream_handlers = [
        h
        for h in logging.getLogger(logger_name).handlers
        if isinstance(h, logging.StreamHandler)
    ]
    for stream_handler in stream_handlers:
        logging.getLogger(logger_name).removeHandler(stream_handler)


def test_reeds_to_rev_usage(hourlize_path):
    """
    Basic test of reeds_to_rev.py to make sure it can be run
    as a command/script and will return usage instructions when
    --help is specified.
    """

    sys.argv = [None, "--help"]
    try:
        runpy.run_path(hourlize_path.joinpath("reeds_to_rev.py"), run_name="__main__")
    except SystemExit as e:
        assert e.code == 0, "reeds_to_rev.py encountered an error."


def test_reeds_to_rev_integration(test_techs, integration_data_path, hourlize_path):
    """
    Integration test of reeds_to_rev.py to ensure it returns the
    expected outputs. This test covers the following techs:
    upv, wind-ons, wind-ofs.
    """

    sc_path = integration_data_path.joinpath("supply_curves")
    reeds_source_path = integration_data_path.joinpath("reeds")

    with temporary_parent_directory(reeds_source_path) as temp_reeds:
        reeds_path = Path(temp_reeds.name)
        run_folder = reeds_path.joinpath("reeds")

        for tech in test_techs:
            remove_stream_handlers("reeds_to_rev")
            sys.argv = [
                None,
                reeds_path.as_posix(),
                run_folder.as_posix(),
                "cost",
                "--reduced_only",
                "--tech",
                tech,
                "--sc_path",
                sc_path.as_posix(),
            ]
            try:
                runpy.run_path(
                    hourlize_path.joinpath("reeds_to_rev.py"), run_name="__main__"
                )
            except SystemExit as e:
                assert e.code == 0, "reeds_to_rev.py encountered an error."

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


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
