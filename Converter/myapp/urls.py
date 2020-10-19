from .views import my_view
from django.urls import path

urlpatterns = [
    path('', my_view, name="my-view"),
    path('conv', my_view, name='conv')
]
# Привязка функции к url адресу
