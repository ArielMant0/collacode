import numpy as np
from krippendorff import alpha

def get_irr_score(coders, items, tags):
    tag_scores = []
    item_scores = []

    id_to_tag = {}
    id_to_item = {}
    id_to_coder = {}

    print(f"{len(tags)} tags")
    for t in tags:
        try:
            data = np.zeros((len(coders),len(items)))

            for i, c in enumerate(coders):
                id_to_coder[c["id"]] = i
                for j, item in enumerate(items):
                    id_to_item[item["id"]] = j
                    data[i][j] = np.nan

            for j, item in enumerate(items):
                users = set()
                for dts in item["tags"]:
                    users.add(dts["created_by"])
                    if dts["tag_id"] != t["id"]:
                        continue

                    i = id_to_coder[dts["created_by"]]
                    data[i][j] = 2

                for u in users:
                    i = id_to_coder[u]
                    if np.isnan(data[i][j]):
                        data[i][j] = 1

            result = alpha(reliability_data=data, level_of_measurement='nominal')
            # print(t["name"], result)

            tag_scores.append({ "tag_id": t["id"], "alpha": None if np.isinf(result) or np.isnan(result) else result })
        except:
            print("error")

    for item in items:
        try:
            data = np.zeros((len(coders),len(tags)))
            data.fill(np.nan)

            for i, c in enumerate(coders):
                id_to_coder[c["id"]] = i
                for j, t in enumerate(tags):
                    id_to_tag[t["id"]] = j

            users = set()
            for dts in item["tags"]:
                if dts["tag_id"] not in id_to_tag:
                    continue

                users.add(dts["created_by"])
                i = id_to_coder[dts["created_by"]]
                j = id_to_tag[dts["tag_id"]]
                data[i][j] = 2

            if len(users) < 2:
                item_scores.append({ "item_id": item["id"], "alpha": None })
                continue

            for u in users:
                i = id_to_coder[u]
                for j in range(0, len(tags)):
                    if data[i][j] != 2:
                        data[i][j] = 1

            result = alpha(reliability_data=data, level_of_measurement='nominal')
            # print(item["name"], result)

            item_scores.append({ "item_id": item["id"], "alpha": None if np.isinf(result) or np.isnan(result) else result })
        except ValueError as e:
            print("error:", e)
            print(item["name"])
            print(data)


    return { "tags": tag_scores, "items": item_scores }
