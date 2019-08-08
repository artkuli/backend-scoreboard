import json
import os
import test

from datetime import datetime

# Keys for values to save in report (matched with terminalreporter.stats)
REPORT_KEYS = ["passed", "failed", "skipped"]


def pytest_addoption(parser):
    parser.addoption(
        "--onnx_backend",
        choices=[
            "ngraph_onnx.onnx_importer.backend",
            "onnxruntime.backend.backend",
            "onnx_tf.backend",
            "caffe2.python.onnx.backend",
        ],
        help="Select from available backends",
    )


def pytest_configure(config):
    onnx_backend_module = config.getvalue("onnx_backend")
    test.ONNX_BACKEND_MODULE = onnx_backend_module


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    # Set directory for results
    results_dir = os.environ.get("RESULTS_DIR", os.getcwd())

    # Collect and save the results
    report = _prepare_report(terminalreporter.stats)
    _save_report(report, results_dir)
    summary = _prepare_summary(report)
    trend = _load_trend(results_dir)
    current_trend = _update_trend(summary, trend)
    _save_trend(current_trend, results_dir)


def _prepare_report(stats):
    """Return tests results report

    Return results report based on pytest stats values
    that match keys listed in REPORT_KEYS.

    :param stats: [description]
    :type stats: [type]
    :return: [description]
    :rtype: [type]
    """
    report = {"date": datetime.now().strftime("%m/%d/%Y %H:%M:%S")}
    for key in REPORT_KEYS:
        stats_group = stats.get(key, [])
        if isinstance(stats_group, list):
            report[key] = []
            for record in stats_group:
                if hasattr(record, "nodeid"):
                    # Remove file name from test id
                    split_id = record.nodeid.split("::")
                    clear_id = filter(lambda x: ".py" not in x, split_id)
                    record_name = "::".join(clear_id)
                    report[key].append(record_name)
            report[key].sort()
    return report


def _prepare_summary(report):
    """Return tests summary including number of failed and passed tests.

    :param report: Dictionary with REPORT_KEYS and list of tests names as values.
    :type report: dict
    :return: Summary with length of each list in report.
    :rtype: dict
    """
    summary = dict()
    for key in report.keys():
        if isinstance(report.get(key), list):
            summary[key] = len(report.get(key))
    summary["date"] = report.get("date", datetime.now().strftime("%m/%d/%Y %H:%M:%S"))
    return summary


def _save_report(report, results_dir, file_name="report.json"):
    """Save report data to the file.

    :param report: Dictionary with REPORT_KEYS and list of tests names as values.
    :type report: dict
    :param results_dir: Path to direcotry with results.
    :type results_dir: str
    :param file_name: Name of report file, defaults to "report.json"
    :type file_name: str, optional
    """
    with open(os.path.join(results_dir, file_name), "w") as report_file:
        json.dump(report, report_file, sort_keys=True, indent=4)


def _save_trend(trend, results_dir, file_name="trend.json"):
    """Save trend data to the file.

    :param trend: List of summaries.
    :type trend: list
    :param results_dir: Path to direcotry with results.
    :type results_dir: str
    :param file_name: Name of trend file, defaults to "trend.json"
    :type file_name: str, optional
    """
    with open(os.path.join(results_dir, file_name), "w") as trend_file:
        json.dump(trend, trend_file, sort_keys=True, indent=4)


def _load_trend(results_dir, file_name="trend.json"):
    """Load and return trend list from file.

    Return list of summaries loaded from tests trend file.
    If file is broken, empty or not found create and return new trend list.

    :param results_dir: Path to direcotry with results.
    :type results_dir: str
    :param file_name: Name of trend file, defaults to "trend.json".
    :type file_name: str, optional
    :return: List of summaries.
    :rtype: list
    """
    try:
        with open(os.path.join(results_dir, file_name), "r") as trend_file:
            trend = json.load(trend_file)
    except (IOError, json.decoder.JSONDecodeError):
        trend = []
    return trend


def _update_trend(summary, trend):
    """Return updated trend.

    Append result summary if trend has less than two results or
    the last one result is different than current,
    otherwise replace last summary.

    :param summary: Contain length of each list in report.
    :type summary: dict
    :param trend: List of summaries.
    :type trend: list
    :return: Updated trend.
    :rtype: list
    """
    if (
        len(trend) < 2
        or len(summary.keys()) != len(trend[-1].keys())
        or any(
            trend[-1].get(key) != summary.get(key)
            for key in summary.keys()
            if key != "date"
        )
    ):
        trend.append(summary)
    else:
        trend[-1] = summary
    return trend
