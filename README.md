# PetroVisor API
[![PyPI Latest Release](https://img.shields.io/pypi/v/petrovisor.svg)](https://pypi.org/project/petrovisor/)

Python interface to PetroVisor REST API.

# Documentation

## Python API Documentation
For comprehensive guides, tutorials, and API reference, please visit our [official documentation site](https://datagration.github.io/petrovisor-python-api/).

## REST API Reference
The complete PetroVisor REST API specification, including all available endpoints and data models, is accessible through our Swagger documentation:

- [PetroVisor Web API (US Region)](https://api.us1.petrovisor.com/index.html?__hstc=187844791.915eb7f16db6760da47f18781132b2ac.1677840296877.1677840296877.1678450552784.2&__hssc=187844791.4.1678450552784&__hsfp=3193161031)  
- [PetroVisor Web API (EU Region)](https://api.eu1.petrovisor.com/index.html?__hstc=187844791.915eb7f16db6760da47f18781132b2ac.1677840296877.1677840296877.1678450552784.2&__hssc=187844791.4.1678450552784&__hsfp=3193161031)

# Installing petrovisor

`petrovisor` can be installed using [uv](https://docs.astral.sh/uv/) (recommended) or `pip` from [PyPI](https://pypi.org/project/petrovisor/), [GitHub](https://github.com/Datagration/petrovisor-python-api.git), or directly from the source.

## Prerequisites

- Python 3.7+, Python 3.12+ recommended (tested on 3.7-3.14)
- [uv](https://docs.astral.sh/uv/) - **Recommended**: An extremely fast Python package and project manager written in Rust (10-100x faster than pip)
  - Install with: `curl -LsSf https://astral.sh/uv/install.sh | sh` (Unix) or `powershell -c "irm https://astral.sh/uv/install.ps1 | iex"` (Windows)
  - Or use `pip install uv` as fallback

## Installation Options

### From PyPI (Recommended)

```bash
uv pip install petrovisor
```

### From GitHub

```bash
uv pip install git+https://github.com/Datagration/petrovisor-python-api.git
```

### From Source

1. Clone the repository
```bash
git clone https://github.com/Datagration/petrovisor-python-api.git
cd petrovisor-python-api
```

2. Install the package
```bash
uv pip install .
```

## Verify Installation

You can verify that petrovisor is installed correctly by importing it in Python:

```python
import petrovisor as pv
print(pv.__version__)
```

## Development Setup

For contributors, you can install development dependencies with:

```bash
uv pip install -e ".[dev]"
```

Note that package installation dependencies are defined in `pyproject.toml`, while the `requirements.txt` file includes additional packages needed for development, testing, and documentation.

## Package Build System

This package uses [Hatchling](https://hatch.pypa.io/) as its build system. Hatchling is a modern, extensible Python build backend that follows the latest packaging standards (PEP 517/518).

## Uninstalling petrovisor

Uninstall `petrovisor` package:

```bash
uv pip uninstall petrovisor
```

## Dependencies

REST API interface is implemented using [requests](https://github.com/psf/requests)

Other dependencies include
- [pydantic](https://github.com/pydantic/pydantic)
- [numpy](https://github.com/numpy/numpy)
- [pandas](https://github.com/pandas-dev/pandas)
- [openpyxl](https://github.com/theorchard/openpyxl/tree/master)
- [xlsxwriter](https://github.com/jmcnamara/XlsxWriter)

# How to use

### Authorization

If one uses Jupyter notebook or running Python script from console for authorization the user required to specify the `workspace`  and `discovery_url`.

```python
workspace = 'Workspace Name'
# url for authentification (US or EU)
discovery_url = r'https://identity.us1.petrovisor.com' # US
discovery_url = r'https://identity.eu1.petrovisor.com' # EU
```

`username` and `password` credentials can be entered either by using the login dialog
```python
api = pv.PetroVisor(workspace = workspace,
                    discovery_url = discovery_url)
```

or by specifying `username` and `password` arguments directly
```python
api = pv.PetroVisor(workspace = workspace,
                    discovery_url = discovery_url,
                    username = username,
                    password = password)
```

### Examples: Get, Post, Put, Delete requests

Basic API requests such as `get`, `post`, `put`, `delete` consist of main URL/route part,
as well as an optional `data` and `query` string arguments.
`data` and `query` arguments can presented by the built-in Python dictionary.

#### Put request

```python
name = 'Well'
api.put(f'Entities/{name}', data = {
  'Name': name,
  'EntityTypeName': 'Well',
  'Alias': 'Well Alias',
  'IsOpportunity': False,
})
```

#### Post request

```python
old_name = 'Well'
new_name = 'New Well'
api.post(f'Entities/Rename', query = {
    'OldName': old_name,
    'NewName': new_name,
})
```

#### Get request

```python
name = 'New Well'
api.get(f'Entities/{name}')
```

#### Delete request

```python
name = 'New Well'
api.delete(f'Entities/{name}')
```

More examples can be found in the `examples` directory of the repository.
