# Internal setup: OpenSky Python API

This README is for the project team. Everyone must create their own local environment and use their own OpenSky API credentials. Never share or commit `credentials.json`; it is already listed in `.gitignore`.

## Set up the Python environment

From the repository root, create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install the existing project requirements:

```bash
python -m pip install -r requirements.txt
```

We now use OpenSky's Python API client. Install it directly from the official GitHub repository:

```bash
pip install "git+https://github.com/openskynetwork/opensky-api.git#subdirectory=python"
```

## Add your OpenSky credentials

Create an API client from your own OpenSky account and download its `credentials.json` file. Put the file in the **repository root**, alongside this README:

```text
sep26_bde_int_dst_airlines/
├── credentials.json
├── README_internal.md
└── src/
```

The OpenSky-generated file uses this structure:

```json
{
  "clientId": "your-own-client-id",
  "clientSecret": "your-own-client-secret"
}
```

The Python client reads this file, obtains OAuth tokens, and refreshes them automatically.

## Set your timezone

In `src/data/make_dataset.py`, change the following line in `time_to_unix()` to your own IANA timezone:

```python
local_tz = ZoneInfo("THEIR TZ")
```

For example:

```python
local_tz = ZoneInfo("Europe/Berlin")
```

This matters because the arrival search converts the entered local date and time to Unix timestamps. Using the correct timezone also handles daylight-saving offsets correctly.

## What `make_dataset.py` currently does

The script now uses the OpenSky Python API rather than making a raw `requests` call. It:

1. loads your API credentials from the repository-root `credentials.json`;
2. opens an authenticated OpenSky API session with automatic token refresh;
3. retrieves the current aircraft states and prints the first state found;
4. pauses until you press Enter;
5. converts the example IATA airport code `FRA` to the ICAO code `EDDF`;
6. converts the configured local start and end times to Unix timestamps;
7. requests arrivals at that airport during the time window; and
8. prints the first matching arrival.

The airport and time window are currently hard-coded examples. The script demonstrates the connection and lookup flow; it does not save a finished dataset yet.

## What `airport_icao_codes.json` is

`src/data/static/airport_icao_codes.json` is a local airport reference file. Each entry is keyed by its ICAO airport code and includes metadata such as its IATA code, airport name, city, country, coordinates, elevation, and timezone.

OpenSky's airport-arrival endpoint expects a four-character ICAO code, while users commonly know the three-character IATA code. The `convert_iata_to_icao()` function searches this file to translate an input such as `FRA` into `EDDF`. It raises `ValueError` when no matching IATA code exists.

## Run the current script

The current file paths are relative to `src/data`, so run the script from that directory:

```bash
cd src/data
python make_dataset.py
```
