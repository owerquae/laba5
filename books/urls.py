from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('ajax/search/', views.ajax_search, name='ajax_search'),
    path('edit/<int:pk>/', views.edit_book, name='edit_book'),
    path('delete/<int:pk>/', views.delete_book, name='delete_book'),
]
