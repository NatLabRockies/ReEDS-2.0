import os, sys
sys.path.insert(1, os.path.join(sys.path[0], '..'))
import core
import importlib

data_type, data_source, report_path, report_format, html_num, output_dir, auto_open = sys.argv[1:]

report_dir = os.path.dirname(report_path)
sys.path.insert(1, report_dir)
report_name = os.path.basename(report_path)[:-3]
report = importlib.import_module(report_name)
core.static_report(data_type, data_source, report.static_presets, report_path, report_format, html_num, output_dir, auto_open)
