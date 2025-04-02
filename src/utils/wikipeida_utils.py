import requests


def get_random_page() -> dict[str, int | str]:
    result: dict[str, int | str] = get_random_index()
    return get_page(result["id"])


def get_random_index() -> dict[str, int | str]:
    url = "https://ja.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "list": "random",
        "rnnamespace": 0,
        "rnlimit": 1,
    }
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    return response.json()["query"]["random"][0]


def get_page(pageid) -> dict[str, int | str]:
    url = "https://ja.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "prop": "extracts",
        "pageids": pageid,
        "explaintext": True,
        "exsectionformat": "plain",
    }
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    return response.json()["query"]["pages"][str(pageid)]
