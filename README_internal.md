# Internal guide: OpenSky collection pipeline

This document is for the project team. Each person must use their own OpenSky and MongoDB credentials. Do not share or commit `.env` or `credentials.json`; both are ignored by Git.

## Current project focus

We are focusing on **airport arrivals** and **airport departures** first. These are the two datasets to use for the next stage of analysis and visualisation.

Current aircraft **states** may also be useful as supplementary live data, so the states request remains available behind its collection switch.

The **interval flights** call remains in the code as it is. Leave it alone for now: do not change, analyse, or build new features around it until we decide it is needed.

## Local setup

From the repository root, create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install the existing requirements and the official OpenSky Python client:

```bash
python -m pip install -r requirements.txt
python -m pip install pymongo
python -m pip install "git+https://github.com/openskynetwork/opensky-api.git#subdirectory=python"
```

## Credentials and `.env`

Create your local environment file from the template:

```bash
cp .env.example .env
```

Create an OpenSky API client in your own OpenSky account and download its `credentials.json` file. Put it in the repository root:

```text
sep26_bde_int_dst_airlines/
├── .env
├── credentials.json
├── README_internal.md
└── src/
```

The JSON file is supplied by OpenSky and contains your `clientId` and `clientSecret`. Do not copy either value into source code or commit the file.

Set these values in `.env`:

```dotenv
# Paths are relative when scripts are run from src/data.
CREDENTIALS_PATH=path-to-your-credentials.json

# Your own MongoDB Atlas database user.
DB_USERNAME=your-mongodb-username
DB_PASSWORD=your-mongodb-password
```

`CREDENTIALS_PATH` is used by `make_dataset.py`. `make_dataset.py` URL-encodes the MongoDB username and password before building the Atlas connection URI, so passwords with characters such as `@` or `:` are supported.

## What `make_dataset.py` does

Run the script from `src/data`, because its local data paths are relative to that directory:

```bash
cd src/data
python make_dataset.py
```

The script performs the following steps:

1. Loads the local `.env` file and authenticates with OpenSky using `credentials.json`. The official client refreshes the OAuth token automatically.
2. Converts the chosen IATA airport code (`FRA`) to OpenSky's ICAO airport code (`EDDF`).
3. Converts the configured local start and end date-times to Unix timestamps using `Europe/Berlin`.
4. Calls the selected OpenSky endpoints.
5. Converts each returned OpenSky object to a plain dictionary using `vars()`. This is required because JSON and MongoDB cannot directly store `StateVector` and flight-client objects.
6. Stores the selected dictionaries either in local JSON cache files or in MongoDB Atlas.

The airport code and time window are example inputs. Change them before running a new collection.

## Configure what is collected

At the top of `src/data/make_dataset.py`, `COLLECT_DATA` controls both the endpoint calls and destination:

```python
COLLECT_DATA = {
    "data": {
        "arrivals": True,
        "departures": True,
        "states": True,
        "intervals": True,
    },
    "destination": "database",  # use "cache" for local JSON files
}
```

For the current scope, keep `arrivals` and `departures` enabled. States are optional. Do not alter the `intervals` section yet.

## Storage behavior

When `destination` is `"cache"`, the script writes selected data to:

```text
src/data/cached_data/states.json
src/data/cached_data/arrivals.json
src/data/cached_data/departures.json
src/data/cached_data/intervals.json
```

When `destination` is `"database"`, it inserts the same dictionary records into the `airline-data` database, using one collection per dataset name (`states`, `arrivals`, `departures`, and `intervals`). Empty responses are skipped.

MongoDB inserts create new documents on every run. Until unique keys or upsert logic are added, rerunning the same collection can create duplicates.

## Airport reference data

`src/data/static/airport_icao_codes.json` is the local airport lookup file. It contains ICAO and IATA codes plus airport name, location, coordinates, elevation, and timezone. `convert_iata_to_icao()` searches it so a familiar IATA code such as `FRA` becomes the ICAO code `EDDF`, which OpenSky's airport endpoints require.

## Check OpenSky flight quota

`src/data/check_rate_limits.py` makes an arrival request and prints the response status plus OpenSky's quota headers. Run it from `src/data`:

```bash
python check_rate_limits.py
```

Useful results:

- `200`: the request succeeded;
- `404`: no flights were found for that airport and time window;
- `429`: the flight-endpoint quota is exhausted; use the reported retry time before trying again.

Use the local cache for UI work whenever possible so beta testing does not consume additional flight-query credits.

## Run the Streamlit visualisation

Start Streamlit from the visualisation folder:

```bash
cd src/visualization
streamlit run visualize.py
```

If Streamlit is not installed in the active virtual environment, install it first:

```bash
python -m pip install streamlit
```
