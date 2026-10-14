"""Check the OpenSky flight-endpoint quota for one arrival query."""

from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import requests
from opensky_api import TokenManager


AIRPORT = "EDDF"
LOCAL_TZ = ZoneInfo("Europe/Berlin")
BEGIN = int(datetime(2026, 10, 10, 12, 0, tzinfo=LOCAL_TZ).timestamp())
END = int(datetime(2026, 10, 10, 13, 0, tzinfo=LOCAL_TZ).timestamp())
CREDENTIALS_FILE = Path(__file__).resolve().parents[2] / "credentials.json"


def main() -> None:
    """Request airport arrivals and print the OpenSky quota response headers."""
    token_manager = TokenManager.from_json_file(CREDENTIALS_FILE)
    response = requests.get(
        "https://opensky-network.org/api/flights/arrival",
        headers=token_manager.auth_headers(),
        params={"airport": AIRPORT, "begin": BEGIN, "end": END},
        timeout=15,
    )

    print(f"Status: {response.status_code} {response.reason}")
    print(f"Credits remaining: {response.headers.get('X-Rate-Limit-Remaining')}")
    print(f"Retry after: {response.headers.get('X-Rate-Limit-Retry-After-Seconds')}")

    if response.status_code == 200:
        print(f"Arrivals returned: {len(response.json())}")
    elif response.status_code == 404:
        print("No arrivals found for this airport and time window.")
    elif response.status_code == 429:
        print("The flight-endpoint quota is exhausted; wait before retrying.")


if __name__ == "__main__":
    main()
