---
sidebar_position: 1
title: Installation
keywords: [tutorial]
tags: [tutorial]
---

# Installing petrovisor

`petrovisor` can be installed using [uv](https://docs.astral.sh/uv/) (recommended) or `pip` from [PyPI](https://pypi.org/project/petrovisor/), [GitHub](https://github.com/Datagration/petrovisor-python-api.git), or directly from the source.

## Prerequisites

- Python 3.7+, Python 3.12+ recommended (tested on 3.7–3.14)
- [uv](https://docs.astral.sh/uv/) — **Recommended**: an extremely fast Python package and project manager written in Rust (10–100× faster than pip)

Install uv:

```bash
# Unix / macOS
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or via pip
pip install uv
```

## Installation Options

### From PyPI (Recommended)

```bash
uv pip install petrovisor
```

<details>
<summary>Using pip instead</summary>

```bash
pip install petrovisor
```

</details>

### From GitHub

```bash
uv pip install git+https://github.com/Datagration/petrovisor-python-api.git
```

<details>
<summary>Using pip instead</summary>

```bash
pip install git+https://github.com/Datagration/petrovisor-python-api.git
```

</details>

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

<details>
<summary>Using pip instead</summary>

```bash
pip install .
```

</details>

## Verify Installation

```python
import petrovisor as pv
print(pv.__version__)
```

## Development Setup

For contributors, install with development dependencies:

```bash
uv pip install -e ".[dev]"
```

## Dependencies

REST API interface is implemented using [requests](https://github.com/psf/requests)

Other dependencies include
- [pydantic](https://github.com/pydantic/pydantic)
- [numpy](https://github.com/numpy/numpy)
- [pandas](https://github.com/pandas-dev/pandas)
- [openpyxl](https://github.com/theorchard/openpyxl/tree/master)
- [xlsxwriter](https://github.com/jmcnamara/XlsxWriter)
