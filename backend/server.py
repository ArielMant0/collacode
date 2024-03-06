import json
import os
import pandas as pd
from pathlib import Path

from flask import request, Flask, Response, jsonify
from flask_cors import CORS

app = Flask(__name__)
app.config["DEBUG"] = True
CORS(app)

DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

@app.route('/api/v1/datasets', methods=['GET'])
def datasets():
    datasets = []
    for directory in os.listdir(DATA_PATH):
        p = Path(DATA_PATH).joinpath(directory)
        meta = p.joinpath("meta.json")
        if p.is_dir() and meta.exists():
            with open(meta, "r") as file:
                datasets.append(json.load(file))

    return jsonify(datasets)

@app.get('/api/v1/<dataset>/<subset>')
def get_data_subset(dataset, subset):
    if subset not in ["data", "data_tags", "codes", "users", "tags"]:
        return Response(status=500)

    fp = Path(os.path.join(DATA_PATH, dataset + f"/{subset}.csv"))
    if not fp.exists():
        return Response(status=500)

    df = pd.read_csv(fp, sep=";", quotechar='"', index_col=False)

    return df.to_json(orient="records")

@app.post('/api/v1/<dataset>/<subset>/add')
def add(dataset, subset):
    if subset not in ["data", "data_tags", "codes", "tags"]:
        return Response(status=500)

    fp = Path(os.path.join(DATA_PATH, dataset + f"/{subset}.csv"))
    if not fp.exists():
        return Response(status=500)

    df = pd.read_csv(fp, sep=";", quotechar='"', index_col=False)

    if subset == "data":
        df["year"] = pd.to_numeric(df["year"], downcast="integer", errors='coerce')
        df["title"] = df["title"].astype(str)

        ndf = pd.DataFrame(request.json["rows"])
        ndf["id"] = [int(i) for i in range(df.shape[0], df.shape[0]+ndf.shape[0])]
        ndf["played"] = ndf["played"].transform(lambda x: x == "True" or x == "true")
        ndf["played"] = ndf["played"].astype(bool)
        ndf["title"] = ndf["title"].astype(str)
        ndf.loc[ndf["year"] == ""] = 0
        ndf["year"] = pd.to_numeric(ndf["year"], downcast="integer", errors='coerce')

        if df.shape[0] == 0:
            df = ndf
        else:
            df = pd.concat([df, ndf], ignore_index=True)
            df.drop_duplicates(subset="title", keep="first", inplace=True, ignore_index=True)

        df.to_csv(fp, sep=";", quotechar='"', index=False)

    return Response(status=200)

@app.post('/api/v1/<dataset>/<subset>/update')
def update(dataset, subset):
    if subset not in ["data", "data_tags", "codes", "tags"]:
        return Response(status=500)

    fp = Path(os.path.join(DATA_PATH, dataset + f"/{subset}.csv"))
    if not fp.exists():
        return Response(status=500)

    df = pd.read_csv(fp, sep=";", quotechar='"', index_col=False)

    if subset == "data_tags":
        user_id = request.json["user_id"]
        code_id = request.json["code_id"]
        game_id = request.json["game_id"]
        created = request.json["created"]
        ndf = pd.DataFrame(request.json["tags"])
        noIDS = ndf.loc[ndf["tag_id"] == ""]
        noIDS["tag_id"].fill

app.run(port=8000)
