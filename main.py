from typing import Optional
from pydantic import BaseModel
from fastapi import FastAPI
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


@app.get("/url/{urlid}")
def read_item(urlid):
    return db.get(urlid)


@app.post("/add")
def add_item(url: URLItem):
    if APP_TOKEN == url.token:
        rand = randint(10000, 99999)
        db.put({
            "id": rand,
            "url": url.url,
            "notes": url.notes,
        })
    else:
        return {"msg": "Authentication failed"}
