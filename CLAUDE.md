# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

BbRest is a Python library that wraps the Blackboard Learn REST API to make it more accessible and developer-friendly. The library solves several key problems:

1. **Self-healing token management**: Blackboard tokens expire in one hour, and this library automatically renews them when needed
2. **Version-aware API generation**: Only exposes REST endpoints available for the connected Blackboard version
3. **Dynamic method generation**: Generates Python methods at runtime from the Blackboard swagger definition, providing tab-completion and parameter hints
4. **Synchronous and asynchronous support**: All methods support both `sync=True` (default) and `sync=False` for async operations

## Core Architecture

### Main Class: BbRest

The `BbRest` class in [bbrest.py](bbrest.py) is the heart of the library. On initialization:

1. Authenticates with Blackboard OAuth2 to get an access token
2. Retrieves the Blackboard version to determine available APIs
3. Downloads the swagger definition from AWS S3
4. Dynamically generates Python methods for all supported endpoints using `exec()`
5. Loads an entitlement map from [ent_map.json](ent_map.json) to translate permission strings to readable descriptions

### Dynamic Method Generation

The `method_generator()` function (line 206-251 in bbrest.py) uses Python's `exec()` to create methods at runtime:

- Parses endpoint paths to extract required parameters (e.g., `{userId}`, `{courseId}`)
- Adds optional parameters like `payload`, `params`, `limit`, and `sync`
- Attaches methods to the class instance using `types.MethodType`
- Sets docstrings with API descriptions, parameters, and permissions

### Token Management

- `is_expired()`: Checks if the token has expired using the `maya` library for time handling
- `refresh_token()`: Renews the token, supporting both client credentials and authorization code flows
- All API calls via `call()` automatically check expiration and refresh if needed

### Dual Execution Modes

- **Synchronous** (`sync=True`): Uses `requests` library, returns `Response` objects
- **Asynchronous** (`sync=False`): Uses `aiohttp`, returns coroutines that must be awaited
- Both modes support automatic pagination when `limit` parameter is provided

### Parameter Cleaning

The `clean_kwargs()` helper function (line 489-511) provides convenience shortcuts:
- Converts simple IDs to fully-qualified format (e.g., `userId='test'` becomes `userId='userName:test'`)
- Allows passing raw IDs starting with `_` or containing `:` unchanged
- Handles `courseId`, `userId`, `columnId`, and `groupId` parameters

## Development Setup

### Installation with Poetry (Recommended)

```bash
poetry install
poetry run jupyter lab  # For interactive development
```

### Installation with pip

```bash
pip install -r requirements.txt
```

### Running Tests

Create a `.env` file with your Blackboard credentials:

```
BB_APPKEY=your_app_key
BB_SECRET=your_app_secret
BB_URL=https://blackboard.school.edu
```

Run the test file:

```bash
python test.py
```

## Key Files

- **[bbrest.py](bbrest.py)**: Main library code (546 lines)
- **[ent_map.json](ent_map.json)**: Maps Blackboard permission strings to human-readable descriptions
- **[setup.py](setup.py)**: Standard setuptools configuration for pip
- **[pyproject.toml](pyproject.toml)**: Poetry configuration (version 0.4.7)
- **[test.py](test.py)**: Basic connection test

## Dependencies

Core dependencies:
- `maya`: Human-friendly time/date handling (used for token expiration)
- `requests`: Synchronous HTTP client
- `aiohttp`: Asynchronous HTTP client

Dev dependencies:
- `jupyterlab`: Interactive development environment
- `black`: Code formatter

## Important Implementation Details

### Version Handling

The library retrieves the Blackboard version via `/learn/api/public/v1/system/version` and uses semantic versioning (major.minor.0) to filter available APIs. If version retrieval fails, it defaults to "3000.0.0" to include all APIs.

### Pagination

When calling methods that return lists (methods ending in 's' or 'Children'), the library:
- Defaults to `limit=100`
- Automatically follows `paging.nextPage` links
- Returns aggregated results in a single response
- Preserves paging information if more results exist

### Swagger Definition

Downloaded from: `https://devportal-docstore.s3.amazonaws.com/learn-swagger.json`

The library parses this to extract:
- API paths and HTTP methods
- Parameter definitions
- Version availability ranges
- Permission requirements

## Common Usage Patterns

### Basic API Call

```python
from bbrest import BbRest
bb = BbRest(key, secret, url)
r = bb.GetCourse(courseId='2832102')
```

### Convenience ID Shortcuts

```python
# These are equivalent:
bb.GetUser(userId='test_user')
bb.call('GetUser', userId='userName:test_user')
```

### Async Usage

```python
user_info = await bb.GetUser('test_user', sync=False)

# Multiple concurrent calls:
tasks = [bb.GetUser(user, sync=False) for user in users]
results = await asyncio.gather(*tasks)
```

## Authentication Flows

Supports two OAuth2 grant types:

1. **Client Credentials** (default): For system-level integrations
2. **Authorization Code**: For user-delegated access, requires `code` and `redirect_uri` parameters

## Notes for Future Development

- The library uses `exec()` extensively for dynamic method generation - this is intentional and core to the design
- Method names come directly from Blackboard's swagger `summary` field with spaces removed
- Six methods have name collisions and are disambiguated in `supported_functions()`: GetChildren, GetMemberships, and Download
- The `ent_map.json` file must be in the same directory as the script (loaded on line 36)
- Async responses differ from sync: success returns raw data dict, failure returns dict with status
