# tap-kit

## Overview

`tap-kit` is a toolkit for simplifying the build of Singer taps, serving as a helper library for common functionality.

This package could help if an API meets the following criteria:
- Basic Auth
- REST API
- Catalog is generatable from schema files (i.e. doesn't need to query the integration API to determine data availability/ids/etc.)
- Straightforward pagination approach (e.g. next https://tools.ietf.org/html/rfc5988 OR simple param search)

##Setup

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

## Example taps using `tap-kit`

- tap-chatitive (https://github.com/codyss/tap-chatitive)
- tap-greenhouse (https://github.com/codyss/tap-greenhouse)
- tap-outreach (https://github.com/codyss/tap-outreach)
