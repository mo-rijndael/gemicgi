import mimetypes
import sys
from datetime import datetime
from traceback import print_exc
from io import StringIO
from os import environ
from pathlib import Path
from typing import TextIO
from urllib.parse import urlparse, unquote


GEMINI_MIME = "text/gemini"
mimetypes.add_type(GEMINI_MIME, "gmi")
mimetypes.add_type(GEMINI_MIME, "gemini")

class Status:
    INPUT = 10
    SENSITIVE_INPUT = 11
    SUCCESS = 20
    TEMPORARY_REDIRECT = 30
    PERMANENT_REDIRECT = 31
    TEMPORARY_FAILURE = 40
    SERVER_UNAVAILABLE = 41
    CGI_ERROR = 42
    PROXY_ERROR = 43
    SLOW_DOWN = 44
    PERMANENT_FAILURE = 50
    NOT_FOUND = 51
    GONE = 52
    PROXY_REQUEST_REFUSED = 53
    BAD_REQUEST = 59
    CLIENT_CERT_REQUIRED = 60
    CLIENT_CERT_NOT_AUTHORIZED = 61
    CLIENT_CERT_INVALID = 62


class Request:
    GATEWAY_INTERFACE: str
    SERVER_SOFTWARE: str
    GEMINI_URL: urlparse
    SCRIPT_NAME: str
    PATH_INFO: str
    QUERY_STRING: unquote
    SERVER_NAME: str
    HOSTNAME: str
    SERVER_PORT: int
    REMOTE_HOST: str
    REMOTE_ADDR: str
    TLS_CLIENT_HASH: str
    TLS_CLIENT_NOT_BEFORE: datetime.fromisoformat
    TLS_CLIENT_NOT_AFTER: datetime.fromisoformat
    REMOTE_USER: str

    def __init__(self):
        for var, parser in self.__annotations__.items():
            self.__dict__[var.lower()] = parser(environ[var])


class Cgi:
    request: Request
    response_code: int
    meta: str
    buffer: TextIO

    def __init__(self):
        self.request = Request()
        self.response_code = Status.SUCCESS
        self.meta = "text/gemini"
        self.buffer = StringIO()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_val is not None:
            self.response_code = Status.CGI_ERROR
            self.meta = str(exc_val).splitlines()[0]
        self.flush()

    def flush(self, to=sys.stdout):
        header = f"{self.response_code} {self.meta}\r\n"
        to.write(header)
        if self.response_code == Status.SUCCESS:
            to.writelines(self.buffer)
        to.flush()

    def error(self, code: int, meta: str):
        self.response_code = code
        self.meta = meta

    def serve_static(self, file: Path):
        if not file.exists():
            return self.error(Status.NOT_FOUND, "Not Found")
        self.buffer = file.open()
        self.meta = mimetypes.guess_type(file)[0] or GEMINI_MIME