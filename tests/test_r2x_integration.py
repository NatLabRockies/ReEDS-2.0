import os
from utils import get_missing_files, get_missing_columns


def test_r2x_integration(casepath, fmap):
    file_list = [
        value["fname"] for _, value in fmap.items() if value.get("mandatory", False)
    ]
    file_column_dict = {
        value["fname"]: value.get("column_mapping").keys()
        for _, value in fmap.items()
        if value.get("column_mapping")  # Only process files with column_mapping
        if value.get("mandatory", False)
    }

    # Verify files first.
    missing_files = get_missing_files(casepath, file_list)
    assert len(missing_files) == 0, f"The following files are missing: {missing_files}"

    missing_columns = []
    for fname, expected_columns in file_column_dict.items():
        for path_prefix in ["outputs", "inputs_case", "inputs_params"]:
            fpath = os.path.join(casepath, path_prefix, fname)
            if os.path.isfile(fpath):
                missing_columns = get_missing_columns(fpath, expected_columns)
        assert (
            len(missing_columns) == 0
        ), f"Missing columns in {fpath}: {missing_columns}"
