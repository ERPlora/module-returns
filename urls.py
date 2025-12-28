"""
Returns & Refunds Module URL Configuration
"""

from django.urls import path
from . import views

app_name = 'returns'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Returns
    path('returns/', views.return_list, name='return_list'),
    path('returns/create/', views.return_create, name='return_create'),
    path('returns/<int:pk>/', views.return_detail, name='return_detail'),
    path('returns/<int:pk>/edit/', views.return_edit, name='return_edit'),
    path('returns/<int:pk>/approve/', views.return_approve, name='return_approve'),
    path('returns/<int:pk>/process/', views.return_process, name='return_process'),
    path('returns/<int:pk>/cancel/', views.return_cancel, name='return_cancel'),

    # Return Lines
    path('returns/<int:pk>/lines/add/', views.line_add, name='line_add'),
    path('returns/<int:pk>/lines/<int:line_pk>/remove/', views.line_remove, name='line_remove'),

    # Return Reasons
    path('reasons/', views.reason_list, name='reason_list'),
    path('reasons/create/', views.reason_create, name='reason_create'),
    path('reasons/<int:pk>/edit/', views.reason_edit, name='reason_edit'),
    path('reasons/<int:pk>/delete/', views.reason_delete, name='reason_delete'),

    # Store Credits
    path('credits/', views.credit_list, name='credit_list'),
    path('credits/create/', views.credit_create, name='credit_create'),
    path('credits/<int:pk>/', views.credit_detail, name='credit_detail'),
    path('credits/lookup/', views.credit_lookup, name='credit_lookup'),

    # Settings
    path('settings/', views.settings_view, name='settings'),
]
