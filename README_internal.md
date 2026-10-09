# Internal setup: OpenSky API connection

This README is for the project team.

I created the branch `First-API-Connections-Adam` and added the first OpenSky API connection. The current implementation:

- obtains and refreshes an OpenSky access token;
- sends an authenticated request to the `/api/states/all` endpoint; and
- prints the basic, unprocessed JSON response.

## Set up your local environment

Everyone must use their own virtual environment and their own OpenSky credentials. Do not share credentials or commit a populated `.env` file. (it should already be ignored by .gitignore)

From the repository root, create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install the project requirements:

```bash
python -m pip install -r requirements.txt
```

Create your local environment file from the provided template:

```bash
cp .env.example .env
```

Then replace the placeholders in `.env` with your own OpenSky API credentials:

```dotenv
CLIENT_ID=your-own-opensky-client-id
CLIENT_SECRET=your-own-opensky-client-secret
```

## Run the current API request

With the virtual environment active, run:

```bash
python src/data/make_dataset.py
```

The script currently prints the raw JSON response. Parsing, validation, and saving the response as a dataset still need to be added.
