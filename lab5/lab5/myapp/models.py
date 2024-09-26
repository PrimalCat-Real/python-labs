from django import forms
from django.db import models

class User(models.Model):
    ROLES = [
        ('admin', 'Admin'),
        ('user', 'User'),
    ]
    name = models.CharField(max_length=100)
    age = models.IntegerField()
    password = models.CharField(max_length=100)
    token = models.CharField(max_length=255, unique=True)
    role = models.CharField(max_length=10, choices=ROLES)

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'price']
        labels = {
            'name': 'Product Name',
            'price': 'Product Price',
        }

        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['name', 'age', 'password']
        labels = {
            'name': 'User Name',
            'age': 'Age',
            'password': 'Password',
        }

        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'age': forms.NumberInput(attrs={'class': 'form-control'}),
            'password': forms.PasswordInput(attrs={'class': 'form-control'}),
        }