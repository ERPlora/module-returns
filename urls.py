"""
Tables Module URL Configuration
"""

from django.urls import path
from . import views

app_name = 'tables'

urlpatterns = [
    # Dashboard / Floor View
    path('', views.floor_view, name='floor_view'),

    # Areas
    path('areas/', views.area_list, name='area_list'),
    path('areas/create/', views.area_create, name='area_create'),
    path('areas/<int:pk>/', views.area_detail, name='area_detail'),
    path('areas/<int:pk>/edit/', views.area_edit, name='area_edit'),
    path('areas/<int:pk>/delete/', views.area_delete, name='area_delete'),

    # Tables
    path('tables/', views.table_list, name='table_list'),
    path('tables/create/', views.table_create, name='table_create'),
    path('tables/<int:pk>/', views.table_detail, name='table_detail'),
    path('tables/<int:pk>/edit/', views.table_edit, name='table_edit'),
    path('tables/<int:pk>/delete/', views.table_delete, name='table_delete'),

    # Table Actions
    path('tables/<int:pk>/open/', views.table_open, name='table_open'),
    path('tables/<int:pk>/close/', views.table_close, name='table_close'),
    path('tables/<int:pk>/transfer/', views.table_transfer, name='table_transfer'),
    path('tables/<int:pk>/block/', views.table_block, name='table_block'),
    path('tables/<int:pk>/unblock/', views.table_unblock, name='table_unblock'),

    # Settings
    path('settings/', views.settings_view, name='settings'),

    # API
    path('api/status/', views.api_tables_status, name='api_status'),
    path('api/areas/', views.api_areas, name='api_areas'),
]
