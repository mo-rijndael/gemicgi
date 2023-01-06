# GemiCGI
Very simple (just one file) CGI «framework» to simplify scripts.
Designed for [Gemini](https://gemini.circumlunar.space) hypertext markup language.
Supports servers compatible with [Stargazer](https://git.sr.ht/~zethra/stargazer/tree/HEAD/doc/stargazer.ini.5.txt) CGI

# Installation
Since GemiCGI is just one file with no dependencies except standart library, you can just grab file and put it:
- Next to your script
- In `/usr/local/lib/python3.*/site-packages/`
- In `~/.local/lib/python3.*/site-packages/`

Also, you can build it with `poetry` and install wheel
```commandline
poetry build
pip install dist/gemicgi-*.whl
```

I don't think GemiCGI has enough value to upload it to PyPI

# Usage

```python
import datetime
import gemicgi
from pathlib import Path

# This will initialize request from environment variables, see stargazer doc for details
cgi = gemicgi.Cgi()

# This will give you request object. Attributes are just lowercase version of environment variables, parsed if applicable
assert isinstance(cgi.request.tls_client_not_before, datetime.datetime)

# Ability to serve a file (with MIME type guessed from extension)
cgi.serve_static(Path(__file__))
cgi.flush()

# Write strings to a buffer
cgi.buffer.write("# Hello gemini!")
cgi.flush()

# Or fail with error
cgi.error(gemicgi.Status.NOT_FOUND, "Idk where to find it")
cgi.flush()
```

Alternatively, you can use it like context manager
```python
import gemicgi

with gemicgi.Cgi() as cgi:
    cgi.buffer.write("# Hiii")
# No manual flush() required. Also, it will automatically return code 42(CGI_ERROR) on unhandled exception
```

Also, there is a nice wrappers for filling buffer!
```python
import gemicgi

with gemicgi.Cgi() as cgi:
    cgi.h1("Gemtext example")
    cgi.line("Plain text line")
    cgi.quote("Wise quote")
    cgi.link("gemini://wise-man.example.org", "Author")
    with cgi.preformat():
        # Write to buffer any way you like, context manager close preformat automatically
        cgi.line("Like this")
        cgi.buffer.write("Or like this\r\n")
        cgi.h1("This won't be rendered, but why not?")
    cgi.list("List element...")
    cgi.list([
        "Bunch",
        "Of",
        "List",
        "Elements"
    ])
```

# TODOs:
- A way to set response code not via error (not all codes are errors)
- GitHub CI to build wheels
- Add cool features but keep it simple