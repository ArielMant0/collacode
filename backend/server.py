import json
import os
import pandas as pd

from flask import Flask, Response
from flask_cors import CORS

app = Flask(__name__)
app.config["DEBUG"] = True
CORS(app)

DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

@app.route('/api/v1/datasets', methods=['GET'])
def columns():
    datasets = []
    for directory in os.listdir(DATA_PATH):
        with open(os.path.join(DATA_PATH, directory + "/meta.json"), "r") as file:
            datasets.append(json.load(file))
    return Response(response=json.dumps(datasets))

app.run(port=8000)
