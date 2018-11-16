# tap-kit
Toolkit for simplifying build of singer taps

If an integration's API meets the following specification, then it's probably worth giving this a shot:

- Basic Auth
- REST API
- Catalog is generatable from schema files (i.e. doesn't need to query the integration API to determine data availability/ids/etc.)
- Straightforward pagination approach (e.g. next https://tools.ietf.org/html/rfc5988 OR simple param search)
