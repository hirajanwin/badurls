from typing import Optional
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException
from deta import Deta
from random import randint
from dotenv import load_dotenv
import os


# Setup

load_dotenv()
DETA_TOKEN = os.getenv("DETA_TOKEN")
APP_TOKEN = os.getenv("APP_TOKEN")
deta = Deta(DETA_TOKEN)  # configure your Deta project
db = deta.Base("domains")  # access your DB
app = FastAPI()


class URLItem(BaseModel):
    url: str
    notes: Optional[str] = None
    token: str


@app.get("/")
def read_root():
    return {"msg": "Hello World!"}


@app.get("/api/url/{urlid}")
def read_item(urlid: int):
    try:
        request = next(db.fetch({"id": urlid}))[0]
        return request
    except:
        raise HTTPException(status_code=404, detail="Item not found")


@app.get("/api/urls")
def read_all():
    try:
        request = next(db.fetch({"show": True}))
        return request
    except:
        raise HTTPException(status_code=404, detail="Items not found")


@app.post("/api/add")
def add_item(url: URLItem):
    if APP_TOKEN == url.token:
        rand = randint(10000, 99999)
        db.insert({
            "id": rand,
            "url": url.url,
            "notes": url.notes,
            "show": False
        })
        return {"msg": "Success!",
                "data": {
                    "id": rand,
                    "url": url.url,
                    "notes": url.notes}
                }
    else:
        raise HTTPException(status_code=401, detail="Unauthorized")
