from flask import (
    Flask,
    request,
    jsonify,
)

import requests
import yaml
import os
import logging


app = Flask(__name__)

OPSIS_DOMAIN = os.environ.get("OPSIS_DOMAIN")


def load_reports():
    reports_path = os.environ.get("REPORT_DEF_PATH", "./reports")
    report_defs = []
    for root, _, files in os.walk(reports_path):
        for f in [f for f in files if f.endswith(".yaml")]:
            filepath = os.path.join(root, f)
            with open(filepath, 'r') as yamlfile:
                report_defs += yaml.load_all(yamlfile.read())

    reports = {}
    for report_def in report_defs:
        displays = {}
        for display in report_def["displays"]:
            displays[display["name"]] = display["charts"]
        reports[report_def['name']] = (report_def['query'], displays)

    return reports


class ReportException(Exception):
    status_code = 400

    def __init__(self, message="Not Found"):
        Exception.__init__(self)
        self.message = message

    def to_dict(self):
        d = {"message": self.message}
        return d


@app.route("/v1/<display>/<report_name>")
def report(display, report_name):
    # TODO don't load reports on every request
    reports = load_reports()
    query_name, displays = reports.get(report_name, (None, {}))
    chart_types = displays.get(display, None)

    if not all([query_name, displays, chart_types]):
        raise ReportException(
            "Report {} for {} Not Found".format(report_name, display),
        )

    charts = []
    for chart_type in chart_types:
        # TODO refactor to coordinate result set format
        q = str(request.query_string, "utf-8") # :/
        url = "http://nerium/v1/{}/?{}".format(query_name, q)
        logging.info("requesting {}".format(url))
        response = requests.get(
            "https://{}/v1/{}/".format(OPSIS_DOMAIN, chart_type),
            params={"formatted_results_location": url},
        )
        charts.append(response.text)

    return jsonify(charts=charts)

@app.route("/health")
def health():
    return jsonify({"health": "OK"})


@app.errorhandler(ReportException)
def handle_exception(e):
    response = jsonify(e.to_dict())
    response.status_code = e.status_code
    return response
