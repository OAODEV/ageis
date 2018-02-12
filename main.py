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
OPSIS_PROTO = os.environ.get("OPSIS_PROTO", "https")
OPSIS_VERSION = os.environ.get("OPSIS_API_VERSION", "v1")
NERIUM_DOMAIN = os.environ.get("NERIUM_DOMAIN")
NERIUM_PROTO = os.environ.get("NERIUM_PROTO", "https")
NERIUM_VERSION = os.environ.get("NERIUM_API_VERSION", "v1")


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
        url = "{}://{}/{}/{}/?{}".format(
            NERIUM_PROTO,
            NERIUM_API_VERSION,
            NERIUM_DOMAIN,
            query_name,
            q,
        )
        response = requests.get(
            "{}://{}/{}/{}/".format(
                OPSIS_PROTO,
                OPSIS_DOMAIN,
                OPSIS_VERSION,
                chart_type,
            ),
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
