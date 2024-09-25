import os
from fastapi import FastAPI, Form, Depends, Request, Cookie
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from pymongo import MongoClient
from bson.objectid import ObjectId
import uuid
from pydantic import BaseModel

app = FastAPI(
    title="Лабораторна робота №3",
)

MONGO_URL = os.getenv("MONGO_URL", "mongodb://root:password@mongo:27017/example_db?authSource=admin")

mongo_client = MongoClient(MONGO_URL)
db = mongo_client["example_db"]

if "users" not in db.list_collection_names():
    db.create_collection("users")

if "products" not in db.list_collection_names():
    db.create_collection("products")

if "orders" not in db.list_collection_names():
    db.create_collection("orders")
users_collection = db["users"]
products_collection = db["products"]
orders_collection = db["orders"]

templates = Jinja2Templates(directory="templates")

def generate_token():
    return str(uuid.uuid4())


class UserSchema(BaseModel):
    name: str
    age: int
    password: str
    role: str


class ProductSchema(BaseModel):
    name: str
    price: int


class OrderSchema(BaseModel):
    user_id: str
    product_id: str
    quantity: int

def create_default_admin():
    admin_user = users_collection.find_one({"role": "admin"})
    if not admin_user:
        admin_token = generate_token()
        admin_user = {
            "name": "admin",
            "age": 30,
            "password": "admin",
            "token": admin_token,
            "role": "admin"
        }
        users_collection.insert_one(admin_user)
        print("create admin account:", admin_token)
    else:
        print("admin account created.")

@app.on_event("startup")
async def startup_event():
    create_default_admin()
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, auth_token: str = Cookie(None)):
    if auth_token is None:
        return RedirectResponse("/login")
    
    user = db.users.find_one({"token": auth_token})
    if not user:
        return RedirectResponse("/login")
    
    if user["role"] == "admin":
        return RedirectResponse("/admin_panel")
    
    products = list(db.products.find())
    return templates.TemplateResponse("index.html", {"request": request, "user": user, "products": products})


@app.get("/create_product", response_class=HTMLResponse)
async def create_product_form(request: Request, auth_token: str = Cookie(None)):
    user = db.users.find_one({"token": auth_token})
    if not user or user["role"] != "user":
        return RedirectResponse("/login")
    
    return templates.TemplateResponse("create_product.html", {"request": request})


@app.post("/create_product", response_class=HTMLResponse)
async def create_product(request: Request, name: str = Form(...), price: int = Form(...), auth_token: str = Cookie(None)):
    user = db.users.find_one({"token": auth_token})
    if not user or user["role"] != "user":
        return RedirectResponse("/login")
    
    new_product = {
        "name": name,
        "price": price
    }
    db.products.insert_one(new_product)
    return RedirectResponse("/", status_code=302)


@app.get("/login", response_class=HTMLResponse)
async def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login", response_class=HTMLResponse)
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    user = db.users.find_one({"name": username})
    if user and user["password"] == password:
        response = RedirectResponse("/admin_panel" if user["role"] == "admin" else "/", status_code=302)
        response.set_cookie(key="auth_token", value=user["token"], httponly=True, max_age=3600, path='/', samesite='Lax')
        return response
    return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})


@app.get("/register", response_class=HTMLResponse)
async def register_form(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@app.post("/register", response_class=HTMLResponse)
async def register(request: Request, username: str = Form(...), password: str = Form(...), age: int = Form(...)):
    existing_user = db.users.find_one({"name": username})
    if existing_user:
        return templates.TemplateResponse("register.html", {"request": request, "error": "User already exists"})
    
    token = generate_token()
    new_user = {
        "name": username,
        "password": password,
        "age": age,
        "token": token,
        "role": "user"
    }
    db.users.insert_one(new_user)
    response = RedirectResponse("/", status_code=302)
    response.set_cookie(key="auth_token", value=token, httponly=True, max_age=3600, path='/', samesite='Lax')
    return response


@app.get("/admin_panel", response_class=HTMLResponse)
async def admin_panel(request: Request, auth_token: str = Cookie(None)):
    if auth_token is None:
        return RedirectResponse("/login")
    
    user = db.users.find_one({"token": auth_token})
    if not user or user["role"] != "admin":
        return RedirectResponse("/login")
    
    users = list(db.users.find())
    products = list(db.products.find())
    return templates.TemplateResponse("admin_panel.html", {"request": request, "users": users, "products": products})


@app.post("/delete_user/{user_id}", response_class=HTMLResponse)
async def delete_user(user_id: str, auth_token: str = Cookie(None)):
    admin = db.users.find_one({"token": auth_token, "role": "admin"})
    if not admin:
        return RedirectResponse("/login")
    
    db.users.delete_one({"_id": ObjectId(user_id)})
    return RedirectResponse("/admin_panel", status_code=302)


@app.post("/update_user/{user_id}", response_class=HTMLResponse)
async def update_user(user_id: str, username: str = Form(...), age: int = Form(...), auth_token: str = Cookie(None)):
    admin = db.users.find_one({"token": auth_token, "role": "admin"})
    if not admin:
        return RedirectResponse("/login")
    
    db.users.update_one({"_id": ObjectId(user_id)}, {"$set": {"name": username, "age": age}})
    return RedirectResponse("/admin_panel", status_code=303)


@app.post("/delete_product/{product_id}", response_class=HTMLResponse)
async def delete_product(product_id: str, auth_token: str = Cookie(None)):
    admin = db.users.find_one({"token": auth_token, "role": "admin"})
    if not admin:
        return RedirectResponse("/login")
    
    db.products.delete_one({"_id": ObjectId(product_id)})
    return RedirectResponse("/admin_panel", status_code=302)


@app.post("/update_product/{product_id}", response_class=HTMLResponse)
async def update_product(product_id: str, name: str = Form(...), price: int = Form(...), auth_token: str = Cookie(None)):
    admin = db.users.find_one({"token": auth_token, "role": "admin"})
    if not admin:
        return RedirectResponse("/login")
    
    db.products.update_one({"_id": ObjectId(product_id)}, {"$set": {"name": name, "price": price}})
    return RedirectResponse("/admin_panel", status_code=303)
