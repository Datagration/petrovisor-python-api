---
sidebar_position: 2
title: Basic Usage
keywords: [tutorial]
tags: [tutorial]
---

# Basic Usage

This guide will show you how to get started with petrovisor by walking through some basic examples.

## Importing the Package

```python
import petrovisor as pv
```

## Connecting to PetroVisor

The first step is to establish a connection to your PetroVisor instance:

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