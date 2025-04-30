---
id: installation
sidebar_position: 1
title: Installation
keywords: [tutorial]
tags: [tutorial]

---

# Installing petrovisor

`petrovisor` can be installed using `pip` or `uv` from [PyPI](https://pypi.org/project/petrovisor/), [GitHub](https://github.com/Datagration/petrovisor-python-api.git), or directly from the source.


## Prerequisites

- Python 3.7 or higher, Python 3.12 (Recommended)
- [pip](https://pypi.org/project/pip/) (Python package installer) or [uv](https://docs.astral.sh/uv/) (extremely fast Python package and project manager, written in Rust)

## Installation Options

### From PyPI (Recommended)

```bash
pip install petrovisor
```

or

```bash
uv pip install petrovisor
```

### From GitHub

```bash
pip install git+https://github.com/Datagration/petrovisor-python-api.git
```

or

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
pip install .
```

or 

```bash
uv pip install .
```

## Verify Installation

You can verify that petrovisor is installed correctly by importing it in Python:

```python
import petrovisor as pv
print(pv.__version__)
```

## Dependencies

REST API interface is implemented using [requests](https://github.com/psf/requests)

Other dependencies include
- [pydantic](https://github.com/pydantic/pydantic)
- [numpy](https://github.com/numpy/numpy)
- [pandas](https://github.com/pandas-dev/pandas)
- [openpyxl](https://github.com/theorchard/openpyxl/tree/master)
- [xlsxwriter](https://github.com/jmcnamara/XlsxWriter)