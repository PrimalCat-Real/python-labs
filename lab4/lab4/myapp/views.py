from django.shortcuts import render, redirect
from django.http import HttpResponse

users = [
    {"id": 1, "name": "admin", "age": 30, "password": "admin", "role": "admin", "token": "admin-token"},
    {"id": 2, "name": "test", "age": 25, "password": "test", "role": "user", "token": "test-token"}
]

products = [
    {"id": 1, "name": "Product 1", "price": 100},
    {"id": 2, "name": "Product 2", "price": 200}
]

def get_user_by_token(token):
    for user in users:
        if user['token'] == token:
            return user
    return None

def index(request):
    auth_token = request.COOKIES.get('auth_token')
    user = get_user_by_token(auth_token)
    
    if not user:
        return redirect('login')
    
    return render(request, 'index.html', {'user': user, 'products': products})

def create_product(request):
    auth_token = request.COOKIES.get('auth_token')
    user = get_user_by_token(auth_token)
    
    if not user or user['role'] != 'user':
        return redirect('login')
    
    if request.method == 'POST':
        name = request.POST['name']
        price = int(request.POST['price'])
        products.append({"id": len(products) + 1, "name": name, "price": price})
        return redirect('index')
    
    return render(request, 'create_product.html')

def login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = next((u for u in users if u['name'] == username and u['password'] == password), None)
        if user:
            if user['role'] == 'admin':
                response = redirect('admin_panel')
            else:
                response = redirect('index')
                
            response.set_cookie('auth_token', user['token'])
            return response
        
        return render(request, 'login.html', {'error': 'Неправильные учетные данные'})
    
    return render(request, 'login.html')

def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        age = int(request.POST['age'])
        token = f'user-{len(users) + 1}-token'
        users.append({"id": len(users) + 1, "name": username, "password": password, "age": age, "token": token, "role": "user"})
        response = redirect('index')
        response.set_cookie('auth_token', token)
        return response
    
    return render(request, 'register.html')


def delete_user(request, user_id):
    auth_token = request.COOKIES.get('auth_token')
    user = get_user_by_token(auth_token)

    if not user or user['role'] != 'admin':
        return redirect('login')

    global users
    users = [u for u in users if u['id'] != int(user_id)]

    return redirect('admin_panel')


def update_user(request, user_id):
    auth_token = request.COOKIES.get('auth_token')
    user = get_user_by_token(auth_token)

    if not user or user['role'] != 'admin':
        return redirect('login')

    if request.method == 'POST':
        username = request.POST['username']
        age = int(request.POST['age'])
        for u in users:
            if u['id'] == int(user_id):
                u['name'] = username
                u['age'] = age
                break
        return redirect('admin_panel')

    user_to_update = next((u for u in users if u['id'] == int(user_id)), None)
    return render(request, 'update_user.html', {'user_to_update': user_to_update})


def delete_product(request, product_id):
    auth_token = request.COOKIES.get('auth_token')
    user = get_user_by_token(auth_token)

    if not user or user['role'] != 'admin':
        return redirect('login')

    global products
    products = [p for p in products if p['id'] != int(product_id)]

    return redirect('admin_panel')


def update_product(request, product_id):
    auth_token = request.COOKIES.get('auth_token')
    user = get_user_by_token(auth_token)

    if not user or user['role'] != 'admin':
        return redirect('login')

    if request.method == 'POST':
        name = request.POST['name']
        price = int(request.POST['price'])
        for p in products:
            if p['id'] == int(product_id):
                p['name'] = name
                p['price'] = price
                break
        return redirect('admin_panel')

    product_to_update = next((p for p in products if p['id'] == int(product_id)), None)
    return render(request, 'update_product.html', {'product_to_update': product_to_update})


def admin_panel(request):
    auth_token = request.COOKIES.get('auth_token')
    user = get_user_by_token(auth_token)

    print(auth_token, user)
    if not user or user['role'] != 'admin':
        return redirect('login')

    return render(request, 'admin_panel.html', {'users': users, 'products': products})
