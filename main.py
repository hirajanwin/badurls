from typing import Optional
from pydantic import BaseModel
from fastapi import FastAPI
from deta import Deta
from random import randint
from dotenv import load_dotenv
import os

load_dotenv()
DETA_TOKEN = os.getenv("DETA_TOKEN")
deta = Deta(DETA_TOKEN)  # configure your Deta project
db = deta.Base("domains")  # access your DB
app = FastAPI()

class URLItem(BaseModel):
    url: str
    notes: Optional[str] = None


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/url/{urlID}")
def read_item(urlID: int):
    return deta.get(urlID)


@app.post("/add")
def add_item(url: URLItem):
    count = 0
    while True:
        rand = randint(1000, 9999)
        try:
            db.get(rand)
            count = count + 1
            if count <= 10:
                break
        except:
            db.put({
                "id": rand,
                "url": url.url,
                "notes": url.notes,
            })
            break
