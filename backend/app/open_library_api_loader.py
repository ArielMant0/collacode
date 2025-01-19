import requests

ENDPOINT = "https://openlibrary.org/search.json?"


def search_openlibray_by_author(author: str):
    try:
        tmp = "+".join(author.lower().split(" "))
        resp = _make_openlibray_request(f"author={tmp}")
        return _make_openlibray_result(resp.json())
    except:
        return []

def search_openlibray_by_title(title: str):
    try:
        tmp = "+".join(title.lower().split(" "))
        resp = _make_openlibray_request(f"title={tmp}")
        return _make_openlibray_result(resp.json())
    except:
        return []

def _make_openlibray_result(response):
    result = []
    for d in response["docs"]:
        try:
            result.append({
                "title": d["title"],
                "author": d["author_name"][0],
                "year": int(d["first_publish_year"]),
                "ISBN": int(d["isbn"][0])
            })
        except:
            continue
    return result

def _make_openlibray_request(search_query):
    try:
        response = requests.get(ENDPOINT + search_query)
        response.raise_for_status()
    except requests.exceptions.HTTPError as errh:
        raise SystemExit(errh)
    except requests.exceptions.ConnectionError as errc:
        print ("Error Connecting:", errc)
    except requests.exceptions.Timeout as errt:
        print ("Timeout Error:", errt)
    except requests.exceptions.RequestException as err:
        raise SystemExit(err)

    return response