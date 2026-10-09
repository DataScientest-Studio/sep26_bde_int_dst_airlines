import requests

from data.token_manager import token_refresh

token = token_refresh()

# Use it for any API call - the token is refreshed automatically.
response = requests.get(
    "https://opensky-network.org/api/states/all",
    headers=token,
)

# Print soup of unparsed data
print(response.json())