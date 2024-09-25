from fastapi import FastAPI, Form, Depends, Request, Cookie
from fastapi.responses import RedirectResponse, HTMLResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy import ForeignKey, create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import uuid
from pydantic import BaseModel

app = FastAPI(
    title="Лабораторна робота №1",
)

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
templates = Jinja2Templates(directory="templates")

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    age = Column(Integer, nullable=False)
    password = Column(String, nullable=False)
    token = Column(String, unique=True, index=True, nullable=False)
    role = Column(String, nullable=False)

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    price = Column(Integer, nullable=False)

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    quantity = Column(Integer, nullable=False)

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def generate_token():
    return str(uuid.uuid4())

def create_default_admin(db: Session):
    admin_user = db.query(User).filter(User.name == "admin").first()
    if not admin_user:
        admin_token = generate_token()
        new_admin = User(name="admin", password="admin", age=30, token=admin_token, role="admin")
        db.add(new_admin)
        db.commit()

with SessionLocal() as db:
    create_default_admin(db)

class UserSchema(BaseModel):
    name: str
    age: int
    password: str
    role: str
    class Config:
        schema_extra = {
            "example": {
                "name": "John Doe",
                "age": 30,
                "password": "strongpassword123",
                "role": "user"
            }
        }

class ProductSchema(BaseModel):
    name: str
    price: int
    class Config:
        schema_extra = {
            "example": {
                "name": "Laptop",
                "price": 1200
            }
        }

class OrderSchema(BaseModel):
    user_id: int
    product_id: int
    quantity: int
    class Config:
        schema_extra = {
            "example": {
                "user_id": 1,
                "product_id": 2,
                "quantity": 3
            }
        }

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, auth_token: str = Cookie(None), db: Session = Depends(get_db)):
    if auth_token is None:
        return RedirectResponse("/login")
    user = db.query(User).filter(User.token == auth_token).first()
    if not user:
        return RedirectResponse("/login")
    if user.role == "admin":
        return RedirectResponse("/admin_panel")
    products = db.query(Product).all()
    return templates.TemplateResponse("index.html", {"request": request, "user": user, "products": products})

@app.get("/create_product", response_class=HTMLResponse)
async def create_product_form(request: Request, auth_token: str = Cookie(None), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.token == auth_token).first()
    if not user or user.role != "user":
        return RedirectResponse("/login")
    return templates.TemplateResponse("create_product.html", {"request": request})

@app.post("/create_product", response_class=HTMLResponse, summary="Create a new product", description="Allows the user to create a new product by providing a name and price.")
async def create_product(request: Request, name: str = Form(...), price: int = Form(...), auth_token: str = Cookie(None), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.token == auth_token).first()
    if not user or user.role != "user":
        return RedirectResponse("/login")
    new_product = Product(name=name, price=price)
    db.add(new_product)
    db.commit()
    return RedirectResponse("/", status_code=302)

@app.get("/login", response_class=HTMLResponse)
async def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login", response_class=HTMLResponse, summary="User login", description="Allows users to log in and get a session token.")
async def login(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.name == username).first()
    if user and user.password == password:
        response = RedirectResponse("/admin_panel" if user.role == "admin" else "/", status_code=302)
        response.set_cookie(key="auth_token", value=user.token, httponly=True, max_age=3600, path='/', samesite='Lax')
        return response
    return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})

@app.get("/register", response_class=HTMLResponse)
async def register_form(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register", response_class=HTMLResponse, summary="User registration", description="Allows new users to register.")
async def register(request: Request, username: str = Form(...), password: str = Form(...), age: int = Form(...), db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.name == username).first()
    if existing_user:
        return templates.TemplateResponse("register.html", {"request": request, "error": "User already exists"})
    token = generate_token()
    new_user = User(name=username, password=password, age=age, token=token, role="user")
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    response = RedirectResponse("/", status_code=302)
    response.set_cookie(key="auth_token", value=new_user.token, httponly=True, max_age=3600, path='/', samesite='Lax')
    return response

@app.get("/admin_panel", response_class=HTMLResponse)
async def admin_panel(request: Request, auth_token: str = Cookie(None), db: Session = Depends(get_db)):
    if auth_token is None:
        return RedirectResponse("/login")
    user = db.query(User).filter(User.token == auth_token).first()
    if not user:
        return RedirectResponse("/login")
    if user.role != "admin":
        return RedirectResponse("/login")
    users = db.query(User).all()
    products = db.query(Product).all()
    return templates.TemplateResponse("admin_panel.html", {"request": request, "users": users, "products": products})

@app.post("/delete_user/{user_id}", response_class=HTMLResponse, summary="Delete a user", description="Allows admin to delete users.")
async def delete_user(user_id: int, db: Session = Depends(get_db), auth_token: str = Cookie(None)):
    user = db.query(User).filter(User.token == auth_token).first()
    if not user or user.role != "admin":
        return RedirectResponse("/login")
    user_to_delete = db.query(User).filter(User.id == user_id).first()
    if user_to_delete:
        db.delete(user_to_delete)
        db.commit()
    return RedirectResponse("/admin_panel", status_code=302)

@app.post("/update_user/{user_id}", response_class=HTMLResponse, summary="Update user details", description="Allows admin to update user details.")
async def update_user(user_id: int, username: str = Form(...), age: int = Form(...), db: Session = Depends(get_db), auth_token: str = Cookie(None)):
    admin = db.query(User).filter(User.token == auth_token, User.role == "admin").first()
    if not admin:
        return RedirectResponse("/login")
    user_to_update = db.query(User).filter(User.id == user_id).first()
    if user_to_update:
        user_to_update.name = username
        user_to_update.age = age
        db.commit()
    return RedirectResponse("/admin_panel", status_code=303)

@app.post("/delete_product/{product_id}", response_class=HTMLResponse, summary="Delete a product", description="Allows admin to delete products.")
async def delete_product(product_id: int, db: Session = Depends(get_db), auth_token: str = Cookie(None)):
    admin = db.query(User).filter(User.token == auth_token, User.role == "admin").first()
    if not admin:
        return RedirectResponse("/login")
    product_to_delete = db.query(Product).filter(Product.id == product_id).first()
    if product_to_delete:
        db.delete(product_to_delete)
        db.commit()
    return RedirectResponse("/admin_panel", status_code=302)

@app.post("/update_product/{product_id}", response_class=HTMLResponse, summary="Update product details", description="Allows admin to update product details.")
async def update_product(product_id: int, name: str = Form(...), price: int = Form(...), db: Session = Depends(get_db), auth_token: str = Cookie(None)):
    admin = db.query(User).filter(User.token == auth_token, User.role == "admin").first()
    if not admin:
        return RedirectResponse("/login")
    product_to_update = db.query(Product).filter(Product.id == product_id).first()
    if product_to_update:
        product_to_update.name = name
        product_to_update.price = price
        db.commit()
    return RedirectResponse("/admin_panel", status_code=303)
