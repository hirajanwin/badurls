from typing import Optional
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException
from deta import Deta
from random import randint
from dotenv import load_dotenv
import os
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address


# Setup

load_dotenv()
DETA_TOKEN = os.getenv("DETA_TOKEN")
APP_TOKEN = os.getenv("APP_TOKEN")
deta = Deta(DETA_TOKEN)  # configure your Deta project
db = deta.Base("domains")  # access your DB

limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


class URLItem(BaseModel):
    url: str
    notes: Optional[str] = None
    token: str


@app.get("/")
@limiter.limit("100/second")
def read_root():
    return {"msg": "Hello World!"}


@app.get("/url/{urlid}")
@limiter.limit("50/second")
def read_item(urlid: int):
    try:
        request = next(db.fetch({"id": urlid}))[0]
        return request
    except:
        raise HTTPException(status_code=404, detail="Item not found")


@app.get("/urls")
@limiter.limit("50/second")
def read_all():
    try:
        request = next(db.fetch({"show": True}))
        return request
    except:
        raise HTTPException(status_code=404, detail="Items not found")


@app.post("/add")
@limiter.limit("10/minute")
def add_item(url: URLItem):
    if APP_TOKEN == url.token:
        rand = randint(10000, 99999)
        db.insert({
            "id": rand,
            "url": url.url,
            "notes": url.notes
        })
        return {"msg": "Success!",
                "data": {
                    "id": rand,
                    "url": url.url,
                    "notes": url.notes}
                }
    else:
        raise HTTPException(status_code=401, detail="Unauthorized")
