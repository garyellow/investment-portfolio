import requests


def fetch_json(url: str, params: dict = None, headers: dict = None) -> dict | list | None:
    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception:
        return None
