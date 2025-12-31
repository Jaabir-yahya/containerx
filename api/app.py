from fastapi import FastAPI
from core.engine.retail import process_retail_sale

app = FastAPI()

@app.post("/retail/sale")
def retail_sale(payload: dict):
    order_id = process_retail_sale(
        payload["customer"],
        payload["items"],
        payload["payment"]
    )
    return {"order_id": order_id}