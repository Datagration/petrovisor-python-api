# PetroVisor API
[![PyPI Latest Release](https://img.shields.io/pypi/v/petrovisor.svg)](https://pypi.org/project/petrovisor/)

Python interface to PetroVisor REST API.
*This lib is currently in development and is subject to change.*

# Install

Install `petrovisor` package from `pip`

    pip install petrovisor

or from the source

    python -m pip install .

Make sure that `pip`, `setuptools` and `build` are up to date

    python -m pip install --upgrade pip
    python -m pip install --upgrade setuptools
    python -m pip install --upgrade build

# Uninstall

Uninstall `petrovisor` package

    python -m pip uninstall petrovisor

# Dependencies

REST API interface is implemented using [requests](https://github.com/psf/requests)

Other dependencies include
- [pandas](https://github.com/pandas-dev/pandas)
- [numpy](https://github.com/numpy/numpy)

# Documentation

Details of the API endpoints and data models can be found in the Swagger links below, which are always up-to-date.

[PetroVisor Web API (US1)](https://api.us1.petrovisor.com/index.html?__hstc=187844791.915eb7f16db6760da47f18781132b2ac.1677840296877.1677840296877.1678450552784.2&__hssc=187844791.4.1678450552784&__hsfp=3193161031)  
[PetroVisor Web API (EU1)](https://api.eu1.petrovisor.com/index.html?__hstc=187844791.915eb7f16db6760da47f18781132b2ac.1677840296877.1677840296877.1678450552784.2&__hssc=187844791.4.1678450552784&__hsfp=3193161031)

Other documentation can be found by the following link.

[PetroVisor REST API](https://www.datagration.com/knowledge/how-do-i-acccess-the-petrovisor-rest-api)

# How to use

### Authorization

If one uses Jupyter notebook or running Python script from console for authorization the user required to specify the `workspace`  and `discovery_url`.

```python
# workspace
workspace = 'Workspace Name'
# url
discovery_url = r'https://identity.us1.petrovisor.com' # US
# discovery_url = r'https://identity.eu1.petrovisor.com' # EU (alternative)
```

`username` and `password` credentials can be entered either by using the login dialog
```python
pv_api = pv.PetroVisor(workspace = workspace,
                       discovery_url = discovery_url)
```

or by specifying `username` and `password` arguments directly
```python
pv_api = pv.PetroVisor(workspace = workspace,
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
pv_api.put(f'Entities/{name}', data = {
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
pv_api.post(f'Entities/Rename', query = {
    'OldName': old_name,
    'NewName': new_name,
})
```

#### Get request

```python
name = 'New Well'
pv_api.get(f'Entities/{name}')
```

#### Delete request

```python
name = 'New Well'
pv_api.delete(f'Entities/{name}')
```

More examples can be found in the `examples` directory of the repository.
