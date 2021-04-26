from typing import Optional
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from deta import Deta
from random import randint
from dotenv import load_dotenv
import os
import sentry_sdk


# Load Sentry

sentry_sdk.init(
    "https://0b626e39891a4dab8a4f191cc88f3469@o309026.ingest.sentry.io/5599097",
    traces_sample_rate=1.0
)

# Setup

load_dotenv()
DETA_TOKEN = os.getenv("DETA_TOKEN")
APP_TOKEN = os.getenv("APP_TOKEN")
deta = Deta(DETA_TOKEN)  # configure your Deta project
db = deta.Base("domains")  # access your DB
app = FastAPI()
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


class URLItem(BaseModel):
    url: str
    notes: Optional[str] = None
    token: str


@app.get("/")
@limiter.limit("1000/minute")
def read_root(request: Request):
    return {"msg": "API SERVED BY INTERNETSHERIFF.ORG - COPYRIGHT 2021"}


@app.get("/url/{urlid}")
@limiter.limit("100/minute")
def read_item(urlid: int, request: Request):
    try:
        request = next(db.fetch({"id": urlid}))[0]
        return request
    except:
        raise HTTPException(status_code=404, detail="Item not found")


@app.get("/urls")
@limiter.limit("100/minute")
def read_all(request: Request):
    try:
        request = next(db.fetch({"show": True}))
        return request
    except:
        raise HTTPException(status_code=404, detail="Items not found")


@app.post("/add")
@limiter.limit("10/minute")
def add_item(url: URLItem, request: Request):
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
    

@app.delete("/delete")
@limiter.limit("5/minute")
def delete_item(url: str, token: str, request: Request):
    try:
        if APP_TOKEN == token:
            dburl = next(db.fetch({"url": url}))[0]
            db.delete(dburl["key"])
            return {"msg": "Success!",
                    "deleted_url": url,
                    "deleted_key": dburl["key"]}
        else:
            raise HTTPException(status_code=401, detail="Unauthorized")
    except Exception as exception:
        return {"error": execption}
        
            