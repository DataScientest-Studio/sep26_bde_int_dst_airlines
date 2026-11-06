# Internal guide: OpenSky collection pipeline

This document describes the OpenSky collection pipeline used by the project. OpenSky, MongoDB, and Neon credentials are kept outside version control in `.env` and credential JSON files.

## Current project focus

We are focusing on **airport arrivals** and **airport departures** first. These are the two datasets to use for the next stage of analysis and visualisation.

Current aircraft **states** are collected as live snapshots. Arrival and departure data is collected for configured airport/time windows.

## Project environment

The project uses a Python virtual environment at `.venv`. Its dependencies include the project requirements, PyMongo, and the official OpenSky Python client:

```bash
python -m pip install -r requirements.txt
python -m pip install pymongo
python -m pip install "git+https://github.com/openskynetwork/opensky-api.git#subdirectory=python"
```

## Credentials and `.env`

The environment configuration is represented by `.env.example`; the active configuration is stored in the uncommitted `.env` file:

```bash
cp .env.example .env
```

The collection pipeline uses separate OpenSky credential JSON files for airport arrivals/departures and states. The configured files are stored in the repository root:

```text
sep26_bde_int_dst_airlines/
├── .env
├── credentials-arrdep.json
├── credentials-states.json
├── README_internal.md
└── src/
```

Each JSON file is supplied by OpenSky and contains a `clientId` and `clientSecret`. These values are not stored in source code.

The `.env` configuration contains values in this form:

```dotenv
# Paths are relative when scripts are run from src/data.
CREDENTIALS_ARRDEP_PATH=path-to-your-arrivals-departures-credentials.json
CREDENTIALS_STATES_PATH=path-to-your-states-credentials.json

# MongoDB Atlas connection string from Atlas → Connect → Drivers.
MONGO_URI=mongodb+srv://your-mongodb-username:your-mongodb-password@your-cluster.mongodb.net/?retryWrites=true&w=majority
DB_NAME=airline-data

# Neon PostgreSQL connection string.
DATABASE_URL=your-neon-connection-string
```

`CREDENTIALS_ARRDEP_PATH` is used for airport arrivals/departures and `CREDENTIALS_STATES_PATH` is used for live states. `MONGO_URI` is read directly by `make_dataset.py`; URL-encode special characters in the username or password if required by your Atlas connection string.

## What `make_dataset.py` does

`make_dataset.py` runs from `src/data`, because its local data paths are relative to that directory. Its collection modes are invoked in this form:

```bash
cd src/data
python make_dataset.py --type states
```

`states` collects a live aircraft-state snapshot. `arrdep` collects hourly FRA arrivals/departures from 06:00 through 22:00, plus BER, MUC, and HAM data for 09:00, 14:00, and 19:00.

Both collection modes save to MongoDB and Neon by default. The optional `--destination cache` setting writes local JSON cache files instead:

```bash
python make_dataset.py --type states --destination cache
```

The script loads `.env`, authenticates with OpenSky, converts the returned objects to dictionaries, cleans date/callsign/airport fields, then stores the results.

## Scheduled collection

The project uses the following crontab entries for automated collection:

```cron
0 9,14,19 * * * cd /Users/adam/PycharmProjects/sep26_bde_int_dst_airlines/src/data && /Users/adam/PycharmProjects/sep26_bde_int_dst_airlines/.venv/bin/python make_dataset.py --type states >> opensky_states.log 2>&1
0 23 * * * cd /Users/adam/PycharmProjects/sep26_bde_int_dst_airlines/src/data && /Users/adam/PycharmProjects/sep26_bde_int_dst_airlines/.venv/bin/python make_dataset.py --type arrdep >> opensky_arrdep.log 2>&1
```

They collect live states at 09:00, 14:00, and 19:00, and airport arrivals/departures at 23:00 every day.

The log files are written to `src/data`.

## Storage behavior

When `destination` is `"cache"`, the script writes selected data to:

```text
src/data/cached_data/states.json
src/data/cached_data/arrivals.json
src/data/cached_data/departures.json
```

When `destination` is `"database"`, it inserts the same dictionary records into the `airline-data` database, using one collection per dataset name (`states`, `arrivals`, and `departures`).

MongoDB inserts create new documents on every run. Until unique keys or upsert logic are added, rerunning the same collection can create duplicates.

## Airport reference data

`src/data/static/airport_icao_codes.json` is the local airport lookup file. It contains ICAO and IATA codes plus airport name, location, coordinates, elevation, and timezone. `convert_iata_to_icao()` searches it so a familiar IATA code such as `FRA` becomes the ICAO code `EDDF`, which OpenSky's airport endpoints require.

## Check OpenSky flight quota

`src/data/check_rate_limits.py` makes an arrival request and prints the response status plus OpenSky's quota headers:

```bash
python check_rate_limits.py
```

Useful results:

- `200`: the request succeeded;
- `404`: no flights were found for that airport and time window;
- `429`: the flight-endpoint quota is exhausted; use the reported retry time before trying again.

Use the local cache for UI work whenever possible so beta testing does not consume additional flight-query credits.

## Streamlit visualisation

The Streamlit visualisation is served from the visualisation folder:

```bash
cd src/visualization
streamlit run visualize.py
```
