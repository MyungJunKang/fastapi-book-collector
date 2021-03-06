from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from app.models import mongodb
from app.models.book import BookModel
from app.book_scraper import NaverBookScraper

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="데이터 수집기", version="0.0.1")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    # book = BookModel(keyword="KEYWORD", publisher="PUBLISHER",
    #                  price=0, image="IMAGE")
    # await mongodb.engine.save(book)
    return templates.TemplateResponse(
        "index.html", {"request": request, "title": "Book Collector"}
    )


@app.get("/search", response_class=HTMLResponse)
async def search(request: Request, q: str):
    keyword = q
    if not keyword:
        return templates.TemplateResponse(
            "./index.html",
            {"request": request, "title": "Book Collector"},
        )
    if await mongodb.engine.find_one(BookModel, BookModel.keyword == keyword):
        books = await mongodb.engine.find(BookModel, BookModel.keyword == keyword)
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "title": "Book Collector", "books": books},
        )
    naver_book_scraper = NaverBookScraper()
    books = await naver_book_scraper.search(keyword, 10)
    book_models = []
    for book in books:
        book_model = BookModel(
            keyword=keyword,
            publisher=book["publisher"],
            price=book["price"],
            image=book["image"],
        )
        book_models.append(book_model)
    await mongodb.engine.save_all(book_models)
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "title": "Book Collector", "books": books},
    )


@app.on_event("startup")
def on_app_start():
    mongodb.connect()


@app.on_event("shutdown")
async def on_app_shutdown():
    mongodb.close()
