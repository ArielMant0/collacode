import requests

ENDPOINT = "https://openlibrary.org/search.json?"


def search_openlibray_by_isbn(isbn: str):
    try:
        tmp = isbn.replace(" ", "").replace("-", "")
        resp = _make_openlibray_request(f"isbn={tmp}&lang=en")
        result = _make_openlibray_result(resp.json())
        if len(result) > 0:
            result[-1]["isbn"] = tmp
            result[-1]["url"] = f"https://openlibrary.org/isbn/{tmp}"
        return result
    except:
        return []

def search_openlibray_by_author(author: str):
    try:
        tmp = "+".join(author.lower().split(" "))
        resp = _make_openlibray_request(f"author={tmp}&lang=en")
        return _make_openlibray_result(resp.json())
    except:
        return []

def search_openlibray_by_title(title: str):
    try:
        tmp = "+".join(title.lower().split(" "))
        resp = _make_openlibray_request(f"title={tmp}&lang=en")
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
                "isbn": d["isbn"][0],
                "url": f"https://openlibrary.org/isbn/{d['isbn'][0]}"
            })
            if "subtitle" in d:
                result[-1]["title"] += ": " + d["subtitle"]

            # cover
            if "cover_i" in d:
                result[-1]["img"] = f"https://covers.openlibrary.org/a/id/{d['cover_i']}-M.jpg"

            # description (sorta)
            if "subject" in d and len(d['subject']) > 0:
                result[-1]["description"] = ". ".join(d['subject'][0:5])

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