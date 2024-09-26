import uuid
from django.db import IntegrityError
from django.shortcuts import render, redirect
from django.http import HttpResponse
from myapp.models import Product, ProductForm, User, UserForm


def get_user_by_token(token):
    return User.objects.filter(token=token).first()


def index(request):
    auth_token = request.COOKIES.get('auth_token')
    user = get_user_by_token(auth_token)

    if not user:
        return redirect('login')

    products = Product.objects.all().order_by('price')
    return render(request, 'index.html', {'user': user, 'products': products})


def create_product(request):
    auth_token = request.COOKIES.get('auth_token')
    user = get_user_by_token(auth_token)

    if not user or user.role != 'user':
        return redirect('login')

    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('index')
    else:
        form = ProductForm()

    return render(request, 'create_product.html', {'form': form})


def login(request):
    create_default_admin()
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = User.objects.filter(name=username, password=password).first()

        if user:
            response = redirect('admin_panel' if user.role == 'admin' else 'index')
            response.set_cookie('auth_token', user.token)
            return response

        return render(request, 'login.html', {'error': 'Invalid credentials'})

    return render(request, 'login.html')


def register(request):
    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            try:
                user = form.save(commit=False)
                user.token = str(uuid.uuid4())
                user.role = 'user'
                user.save()
                response = redirect('index')
                response.set_cookie('auth_token', user.token)
                return response
            except IntegrityError:
                return render(request, 'register.html', {'form': form, 'error': 'An error occurred during registration. Please try again.'})
    else:
        form = UserForm()
    
    return render(request, 'register.html', {'form': form})

def delete_user(request, user_id):
    auth_token = request.COOKIES.get('auth_token')
    user = get_user_by_token(auth_token)

    if not user or user.role != 'admin':
        return redirect('login')

    User.objects.filter(id=user_id).delete()
    return redirect('admin_panel')


def update_user(request, user_id):
    auth_token = request.COOKIES.get('auth_token')
    user = get_user_by_token(auth_token)

    if not user or user.role != 'admin':
        return redirect('login')

    if request.method == 'POST':
        username = request.POST['username']
        age = int(request.POST['age'])

        User.objects.filter(id=user_id).update(name=username, age=age)
        return redirect('admin_panel')

    user_to_update = User.objects.filter(id=user_id).first()
    return render(request, 'update_user.html', {'user_to_update': user_to_update})


def delete_product(request, product_id):
    auth_token = request.COOKIES.get('auth_token')
    user = get_user_by_token(auth_token)

    if not user or user.role != 'admin':
        return redirect('login')

    Product.objects.filter(id=product_id).delete()
    return redirect('admin_panel')


def update_product(request, product_id):
    auth_token = request.COOKIES.get('auth_token')
    user = get_user_by_token(auth_token)

    if not user or user.role != 'admin':
        return redirect('login')

    if request.method == 'POST':
        name = request.POST['name']
        price = float(request.POST['price'])

        Product.objects.filter(id=product_id).update(name=name, price=price)
        return redirect('admin_panel')

    product_to_update = Product.objects.filter(id=product_id).first()
    return render(request, 'update_product.html', {'product_to_update': product_to_update})


def admin_panel(request):
    auth_token = request.COOKIES.get('auth_token')
    user = get_user_by_token(auth_token)

    if not user or user.role != 'admin':
        return redirect('login')

    users = User.objects.all()
    products = Product.objects.all()
    return render(request, 'admin_panel.html', {'users': users, 'products': products})


def create_default_admin():
    if not User.objects.filter(role='admin').exists():
        try:
            User.objects.create(
                name='admin',
                password='admin',
                age=30,
                token=str(uuid.uuid4()),
                role='admin'
            )
            print("Default admin created: username=admin, password=admin")
        except IntegrityError:
            print("Failed to create admin: Integrity Error")


def search_products(request):
    query = request.GET.get('q')
    if query:
        products = Product.objects.filter(name__icontains=query)
    else:
        products = Product.objects.all()

    return render(request, 'search_results.html', {'products': products})


def sorted_users(request):
    auth_token = request.COOKIES.get('auth_token')
    user = get_user_by_token(auth_token)

    if not user or user.role != 'admin':
        return redirect('login')

    users = User.objects.all().order_by('name')
    return render(request, 'sorted_users.html', {'users': users})


def user_count(request):
    auth_token = request.COOKIES.get('auth_token')
    user = get_user_by_token(auth_token)

    if not user or user.role != 'admin':
        return redirect('login')

    user_count = User.objects.count()
    return render(request, 'user_count.html', {'user_count': user_count})