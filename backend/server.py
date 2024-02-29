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
        with open(os.path.join(DATA_PATH, directory + "/meta.json"), "r") as file:
            datasets.append(json.load(file))

    return jsonify(datasets)

@app.route('/api/v1/<dataset>/<subset>', methods=['GET', 'POST'])
def data(dataset, subset):
    if subset not in ["data", "data_tags", "codes", "users", "tags"]:
        return Response(status=500)

    fp = Path(os.path.join(DATA_PATH, dataset + f"/{subset}.csv"))
    if not fp.exists():
        return Response(status=500)

    df = pd.read_csv(fp, sep=";", quotechar='"')

    if request.method == 'GET':
        return df.to_json(orient="records")
    elif subset == "data":
        ndf = pd.DataFrame(request.json["rows"])
        ndf["id"] = [i for i in range(df.shape[0], df.shape[0]+ndf.shape[0])]

        df = df.join(ndf, on="title", how="left")
        print(df)
        df.to_csv(fp, sep=";", quotechar='"', index_label="id")

    return Response(status=200)

app.run(port=8000)
