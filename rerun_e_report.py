"""Refresh report files for an existing run directory and rerun e_report.gms.

This is intended for cases where e_report.gms, e_report_dump.py, or
e_report_params.csv changed after a run directory was created.
"""

from __future__ import annotations

import argparse
import csv
import glob
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


REPORT_FILES = ("e_report.gms", "e_report_dump.py", "e_report_params.csv")
RESTART_RE = re.compile(r"^(?P<case>.+)_(?P<year>\d+)i(?P<iteration>\d+)\.g00$", re.IGNORECASE)


def repo_root() -> Path:
    return Path(__file__).resolve().parent


def resolve_casepath(casepath: str) -> Path:
    path = Path(casepath).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(f"Case path does not exist: {path}")
    if not (path / "e_report.gms").exists():
        raise FileNotFoundError(f"Expected e_report.gms in case path: {path}")
    return path


def iter_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        lines = [line for line in handle if not line.lstrip().startswith("#")]
    reader = csv.DictReader(lines)
    return list(reader)


def truncate_comment(comment: str, limit: int = 255) -> str:
    return comment[:limit]


def regenerate_report_param_files(case_path: Path) -> tuple[Path, Path]:
    csv_path = case_path / "e_report_params.csv"
    gms_path = case_path / "e_report_params.gms"
    list_path = case_path / "e_report_paramlist.txt"

    rows = iter_csv_rows(csv_path)
    gms_lines: list[str] = []
    list_lines: list[str] = []

    for row in rows:
        param = (row.get("param") or "").strip()
        units = (row.get("units") or "").strip()
        comment = truncate_comment((row.get("comment") or "").strip())
        input_flag = (row.get("input") or "").strip()
        if not param:
            continue
        list_lines.append(param.split("(", 1)[0])
        if input_flag == "1":
            continue
        gms_lines.append(f'parameter {param:<50} "--{units}-- {comment}" ;')

    gms_path.write_text("\n".join(gms_lines) + "\n", encoding="utf-8")
    list_path.write_text("\n".join(list_lines) + "\n", encoding="utf-8")
    return gms_path, list_path


def sync_report_files(case_path: Path, source_root: Path) -> None:
    for filename in REPORT_FILES:
        shutil.copy2(source_root / filename, case_path / filename)


def read_switch(case_path: Path, key: str, default: str = "0") -> str:
    switches_path = case_path / "inputs_case" / "switches.csv"
    with switches_path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        for row in reader:
            if not row:
                continue
            if row[0] == key:
                return row[1] if len(row) > 1 else default
    return default


def choose_restart_file(case_path: Path, restart_arg: str | None) -> Path:
    if restart_arg:
        restart_path = Path(restart_arg)
        if not restart_path.is_absolute():
            restart_path = (case_path / restart_path).resolve()
        if not restart_path.exists():
            raise FileNotFoundError(f"Restart file does not exist: {restart_path}")
        return restart_path

    g00_dir = case_path / "g00files"
    candidates = sorted(g00_dir.glob("*.g00"))
    if not candidates:
        raise FileNotFoundError(f"No .g00 files found in {g00_dir}")

    case_name = case_path.name
    ranked: list[tuple[int, int, Path]] = []
    for candidate in candidates:
        match = RESTART_RE.match(candidate.name)
        if not match:
            continue
        if match.group("case") != case_name:
            continue
        ranked.append((int(match.group("year")), int(match.group("iteration")), candidate))

    if ranked:
        ranked.sort(key=lambda item: (item[0], item[1]))
        return ranked[-1][2]

    return max(candidates, key=lambda item: item.stat().st_mtime)


def build_gams_command(case_path: Path, restart_file: Path) -> list[str]:
    case_name = case_path.name
    calc_powfrac = read_switch(case_path, "GSw_calc_powfrac", default="0")
    return [
        "gams",
        "e_report.gms",
        f"o=lstfiles\\report_{case_name}.lst",
        f"r={restart_file}",
        "gdxcompress=1",
        "logOption=4",
        "logFile=gamslog.txt",
        "appendLog=1",
        f"--fname={case_name}",
        f"--GSw_calc_powfrac={calc_powfrac}",
    ]


def run_report(case_path: Path, command: list[str]) -> int:
    print(f"Case: {case_path}")
    print("Command:")
    print(" ".join(command))
    completed = subprocess.run(command, cwd=case_path)
    return completed.returncode


def run_dump(case_path: Path) -> int:
    command = [sys.executable, "e_report_dump.py", str(case_path), "-c"]
    print("Dump command:")
    print(" ".join(command))
    completed = subprocess.run(command, cwd=case_path)
    return completed.returncode


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Refresh report files for an existing run directory and rerun e_report.gms.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("casepath", help="Path to a runs/{case} directory")
    parser.add_argument(
        "--restart",
        help="Optional path to a specific .g00 restart file. Defaults to the latest case restart.",
    )
    parser.add_argument(
        "--sync-report-files",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Copy e_report.gms, e_report_dump.py, and e_report_params.csv from the repo root into the case directory before rerunning.",
    )
    parser.add_argument(
        "--regenerate-params",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Regenerate e_report_params.gms and e_report_paramlist.txt from the case-local e_report_params.csv before rerunning.",
    )
    parser.add_argument(
        "--run-dump",
        action="store_true",
        help="Run e_report_dump.py after e_report.gms succeeds.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the resolved actions without invoking GAMS.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = repo_root()
    case_path = resolve_casepath(args.casepath)

    if args.sync_report_files:
        sync_report_files(case_path, root)
        print(f"Synced report files into {case_path}")

    if args.regenerate_params:
        gms_path, list_path = regenerate_report_param_files(case_path)
        print(f"Regenerated {gms_path}")
        print(f"Regenerated {list_path}")

    restart_file = choose_restart_file(case_path, args.restart)
    command = build_gams_command(case_path, restart_file)

    if args.dry_run:
        print(f"Selected restart: {restart_file}")
        print("Dry run only; not executing GAMS.")
        return 0

    print(f"Selected restart: {restart_file}")
    return_code = run_report(case_path, command)
    if return_code:
        return return_code

    if args.run_dump:
        return run_dump(case_path)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())