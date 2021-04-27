from typing import Optional
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, Request, Depends, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from deta import Deta
from random import randint
from dotenv import load_dotenv
import os
import sentry_sdk
from datetime import date
import secrets


# Load Sentry

sentry_sdk.init(
    dsn="https://0b626e39891a4dab8a4f191cc88f3469@o309026.ingest.sentry.io/5599097",
    traces_sample_rate=1.0
)

# Setup

load_dotenv()
DETA_TOKEN = os.getenv("DETA_TOKEN")
APP_TOKEN = os.getenv("APP_TOKEN")
APP_USER = os.getenv("APP_USER")
deta = Deta(DETA_TOKEN)  # configure your Deta project
db = deta.Base("domains")  # access your DB
app = FastAPI()
security = HTTPBasic()
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.middleware("http")
async def sentry_exception(request: Request, call_next):
    # Credit: https://philstories.medium.com/integrate-sentry-to-fastapi-7250603c070f
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        with sentry_sdk.push_scope() as scope:
            scope.set_context("request", request)
            user_id = "database_user_id" # when available
            scope.user = {
                "ip_address": request.client.host,
                "id": user_id
            }
            sentry_sdk.capture_exception(e)
        raise e

def get_current_username(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, APP_USER)
    correct_password = secrets.compare_digest(credentials.password, APP_TOKEN)
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

class URLItem(BaseModel):
    url: str
    notes: Optional[str] = None
    
class DELURLItem(BaseModel):
    url: str


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
def read_all(request: Request, hidden: Optional[bool] = False):
    try:
        if hidden == False:
            request = next(db.fetch({"show": True}))
        else:
            request = next(db.fetch({"show": False}))
        return request
    except:
        raise HTTPException(status_code=404, detail="Items not found")


@app.post("/add")
@limiter.limit("10/minute")
def add_item(url: URLItem, request: Request, username: str = Depends(get_current_username)):
    try:
        rand = randint(10000, 99999)
        today = str(date.today())
        db.insert({
            "id": rand,
            "url": url.url,
            "notes": url.notes,
            "date": today,
            "show": False
            })
        return {"msg": "Success!",
                "user": username,
                "data": {
                    "id": rand,
                    "url": url.url,
                    "notes": url.notes}
                }
    except:
        raise HTTPException(status_code=500, detail="Server error")
    

@app.delete("/delete")
@limiter.limit("5/minute")
def delete_item(url: DELURLItem, request: Request, username: str = Depends(get_current_username)):
    try:
        dburl = next(db.fetch({"url": url.url}))[0]
        db.delete(dburl["key"])
        return {"msg": "Success!",
                "username": username,
                "deleted_url": url.url,
                "deleted_id": dburl["id"],
                "deleted_key": dburl["key"]}
    except:
        raise HTTPException(status_code=404, detail="Item not found")
    

@app.get("/shields/{shield_type}")
@limiter.limit("100/minute")
def shields(shield_type: str, request: Request):
    if shield_type == "count":
        domain_count = len(list(db.fetch(query=None))[0])
        return {
            "schemaVersion": 1,
            "label": "number of domains",
            "message": str(domain_count),
            "color": "blue"
            }
    else:
        raise HTTPException(status_code=404, detail="Type not found")
