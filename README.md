# tap-kit

## Overview

`tap-kit` is a toolkit for simplifying the build of Singer taps, serving as a helper library for common functionality.

This package could help if an API meets the following criteria:
- Basic Auth
- REST API
- Catalog is generatable from schema files (i.e. doesn't need to query the integration API to determine data availability/ids/etc.)
- Straightforward pagination approach (e.g. next https://tools.ietf.org/html/rfc5988 OR simple param search)

## Setup

### Development

1. Setup virtual environment: `virtualenv --python=3.7 .venv`
1. Activate: `source .venv/bin/activate`
1. Install packages: `poetry install`
    1. Install poetry with: `curl -sSL https://install.python-poetry.org | python3 -`

### Dependency

Add the following to your `setup.py`:

```python
    install_requires=[
        "tap-kit @ git+https://github.com/Radico/tap-kit.git@master"
    ],
    dependency_links=[
        "https://github.com/Radico/tap-kit/tarball/master#egg=tap-kit-0.1.1",
    ]
``` 

From there, import any desired classes and functions like you would for other packages:
```python
from tap_kit import TapExecutor
from tap_kit.streams import Stream
```

## Publish

1. Update `pyproject.toml` with any metadata changes, including a version update.
1. `poetry build`
1. `poetry publish -r artifactory`
    1. Make sure that credentials are added to your env variables for: `POETRY_HTTP_BASIC_ARTIFACTORY_USERNAME` and `POETRY_HTTP_BASIC_ARTIFACTORY_PASSWORD`

## Example taps using `tap-kit`

- tap-chatitive (https://github.com/codyss/tap-chatitive)
- tap-greenhouse (https://github.com/codyss/tap-greenhouse)
- tap-outreach (https://github.com/codyss/tap-outreach)
