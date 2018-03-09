from flask import (
    Flask,
    request,
    jsonify,
)

from errors import (
    AgiasException,
    ChartTypeNotAvailable,
    ReportNotFound,
)

from urllib.parse import (
    urlsplit,
    urlunsplit,
)

import requests
import yaml
import os


app = Flask(__name__)


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


def get_format_requirements(reports):
    return requests.get("http://opsis/v1/").json


@app.route("/v1/<display>/<report_name>", strict_slashes=False)
def report(display, report_name):
    # load reports on every request until it's a bottleneck
    reports = load_reports()
    query_name, displays = reports.get(report_name, ("", {}))
    chart_types = displays.get(display, [])

    required_formats = requests.get("http://opsis/v1/").json

    if not all([query_name, displays, chart_types]):
        raise ReportNotFound(
            "Report {} for {} Not Found".format(report_name, display),
        )

    # TODO consider how discovery of parameters will work, this one is now
    # reserved and cannot be used by a query
    specified_chart_type = request.args.get("ag_chart", "")
    if specified_chart_type and specified_chart_type not in chart_types:
        error_tmpl = (
            "Chart type {} not available for {} report. "
            "Expecting one of {}"
        )
        raise ChartTypeNotAvailable(error_message.format(
            specified_chart_type,
            report_name,
            chart_types,
        ))
    elif specified_chart_type:
        chart_types = [specified_chart_type]

    # The zero chart object
    chart = {
        "type": None,
        "data": None,
        "alternates": [],
    }

    # We get and render the first (default) chart type
    chart_type = chart_types[0]
    q = str(request.query_string, "utf-8") # :/
    required_format = required_formats.get(chart_type, None)
    if required_format:
        q = "&".join([q, "ne_format={}".format(required_format)])
    url = "http://nerium/v1/{}/?{}".format(query_name, q)
    response = requests.get(
        "http://opsis/v1/{}/".format(chart_type),
        params={
            "formatted_results_location": url,
            "report_name": report_name,
            "display": display,
        }
    )
    chart["data"] = response.text
    chart["type"] = chart_type

    # HATEOAS for optional chart types
    for chart_type in chart_types[1:]:
        split_url = urlsplit(request.url)
        chart_request_query_param = "ag_chart={}".format(chart_type)
        chart_request_query = "&".join([
            split_url.query,
            chart_request_query_param,
        ])
        chart_request_url = urlunsplit((
            split_url.scheme,
            split_url.netloc,
            split_url.path,
            chart_request_query,
            split_url.fragment,
        ))
        chart['alternates'].append({
            "type": chart_type,
            "uri": chart_request_url,
        })

    return jsonify(
        chart=chart,
        status=200,
        error=None,
    )


@app.route("/healthz")
def healthz():
    return jsonify({"health": "OK"})


@app.route("/")
def health():
    return jsonify({"health": "OK"})


@app.errorhandler(AgiasException)
def handle_exception(e):
    response = jsonify(e.to_dict())
    response.status_code = e.status_code
    return response

