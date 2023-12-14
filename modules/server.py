import uvicorn

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from .logger import logger
from .models import Url, UrlCreate
from .url_helper import bijective_encode, get_url_title, bijective_decode, get_short_url

app = FastAPI(debug=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins="*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get(
    "/short/{url_id}",
)
def get_url(url_id: str):
    id_ = bijective_decode(url_id)
    url = Url.get(id_)
    url.access_count += 1
    url.update()
    return RedirectResponse(url.url)


@app.post("/short")
def new_url(url_create: UrlCreate):
    url = Url().from_url_create(url_create)
    url.label = get_url_title(url.url)
    id_ = url.save()
    encoded_id = bijective_encode(id_)

    return {"url": get_short_url(encoded_id), "label": url.label}


@app.get("/top-urls")
def get_top_urls():
    urls = Url.get_top_urls()
    return [url.model_dump() for url in urls]


def start_server():
    logger.info("Starting server... ")
    uvicorn.run(app, host="0.0.0.0", port=8080)
