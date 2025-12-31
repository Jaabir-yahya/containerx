import json
from core.engine.retail import process_retail_sale

def run_scenario(path):
    with open(path) as f:
        data = json.load(f)

    return process_retail_sale(
        data["customer"],
        data["items"],
        data["payment"]
    )