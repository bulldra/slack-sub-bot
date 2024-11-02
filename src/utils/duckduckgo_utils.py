from duckduckgo_search import DDGS

import utils.scraping_utils as scraping_utils


def search(query: str, num: int = 10) -> [dict[str, str]]:
    search_results = []
    ddgs = DDGS()
    for r in ddgs.text(query, region="jp-jp", timelimit="y"):
        search_results.append(r)
        if len(search_results) >= num:
            break
    return search_results


def url_list(query: str, num: int = 10) -> [str]:
    search_results = search(query, num)
    return [r["href"] for r in search_results]


def scraping(query: str, num: int = 10) -> [scraping_utils.Site]:
    sites: [scraping_utils.Site] = []
    for url in url_list(query, num):
        try:
            if scraping_utils.is_allow_scraping(url):
                sites.append(scraping_utils.scraping(url))
        except ValueError as e:
            e.args = (f"ReadTimeout: {url}",)
            continue
    return sites
