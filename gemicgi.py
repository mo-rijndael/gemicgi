import mimetypes
import sys
from datetime import datetime
from io import StringIO
from os import environ
from pathlib import Path
from typing import TextIO, Union, Iterable
from urllib.parse import urlparse, unquote, quote, ParseResult
from contextlib import contextmanager


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
    gateway_interface:      str
    server_software:        str
    gemini_url:             ParseResult = urlparse
    script_name:            str
    path_info:              str
    query_string:           str = unquote
    server_name:            str
    hostname:               str
    server_port:            int = int
    remote_host:            str
    remote_addr:            str
    tls_client_hash:        str
    tls_client_not_before:  datetime = datetime.fromisoformat
    tls_client_not_after:   datetime = datetime.fromisoformat
    remote_user:            str

    def __init__(self):
        for var, type_ in self.__annotations__.items():
            parser = self.__class__.__dict__.get(var)
            value = environ[var.upper()]
            if parser:
                value = parser(value)
            self.__dict__[var] = value


class Cgi:
    _request: Request | None
    response_code: int
    meta: str
    buffer: TextIO

    def __init__(self):
        self._request = None
        self.response_code = Status.SUCCESS
        self.meta = "text/gemini"
        self.buffer = StringIO(newline='\r\n')

    @property
    def request(self) -> Request:
        if self._request is None:
            self._request = Request()
        return self._request

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
            self.buffer.seek(0)
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

    # Beautiful API goes here
    def _line_finished(self) -> bool:
        if self.buffer.tell() == 0:
            return True
        try:
            self.buffer.seek(self.buffer.tell() - 2)
        except ValueError:
            return False
        last_two = self.buffer.read(2)
        return last_two == '\r\n'

    def ensure_newline(self):
        if not self._line_finished():
            self.buffer.write('\n')

    def line(self, line: str):
        self.ensure_newline()
        self.buffer.write(f"{line}\n")

    def h1(self, heading: str):
        self.line(f"# {heading}")

    def h2(self, heading: str):
        self.line(f"## {heading}")

    def h3(self, heading: str):
        self.line(f"### {heading}")

    def link(self, url: str, text: str = None, percent_encode=False):
        if percent_encode:
            url = quote(url)
        if text:
            self.line(f"=> {url} {text}")
        else:
            self.line(f"=> {url}")

    def quote(self, text: str):
        self.line(f"> {text}")

    @contextmanager
    def preformat(self, additional: str = ""):
        self.line(f"```{additional}")
        yield
        self.line("```")

    def list(self, data: Union[str, Iterable[str]]):
        if isinstance(data, str):
            return self.line(f"* {data}")
        else:
            for i in data:
                self.list(i)

cgi = Cgi()
