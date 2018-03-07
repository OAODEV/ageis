from flask import jsonify


class AgiasException(Exception):

    def __init__(self):
        Exception.__init__(self)

    def to_dict(self):
        return {
            "status": self.status_code,
            "error": self.message,
            "charts": {
                "default": {
                    "type": None,
                    "data": None,
                },
                "options": [],
            },
        }


class ChartTypeNotAvailable(AgiasException):
    # TODO consider alternate status codes
    # 422 chosen from based on
    # https://www.bennadel.com/blog/2434-http-status-codes-for-invalid-data-400-vs-422.htm
    status_code = 422

    def __init__(self, message):
        AgiasException.__init__(self)
        self.message = message



class ReportNotFound(AgiasException):
    status_code = 400

    def __init__(self, message):
        AgiasException.__init__(self)
        self.message = message


