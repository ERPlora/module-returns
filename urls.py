from django.urls import path

from . import views

app_name = 'returns'

urlpatterns = [
    # Dashboard
    path('', views.index, name='index'),

    # Return list
    path('list/', views.return_list, name='return_list'),

    # Return CRUD
    path('add/', views.return_add, name='return_add'),
    path('<uuid:return_id>/', views.return_detail, name='return_detail'),
    path('<uuid:return_id>/edit/', views.return_edit, name='return_edit'),
    path('<uuid:return_id>/delete/', views.return_delete, name='return_delete'),

    # Return actions
    path('<uuid:return_id>/approve/', views.return_approve, name='return_approve'),
    path('<uuid:return_id>/reject/', views.return_reject, name='return_reject'),
    path('<uuid:return_id>/complete/', views.return_complete, name='return_complete'),

    # Return items
    path('<uuid:return_id>/items/add/', views.item_add, name='item_add'),
    path('<uuid:return_id>/items/<uuid:item_id>/delete/', views.item_delete, name='item_delete'),

    # Reasons
    path('reasons/', views.reasons, name='reasons'),
    path('reasons/add/', views.reason_add, name='reason_add'),
    path('reasons/<uuid:reason_id>/edit/', views.reason_edit, name='reason_edit'),
    path('reasons/<uuid:reason_id>/delete/', views.reason_delete, name='reason_delete'),

    # Store credits
    path('credits/', views.credits, name='credits'),
    path('credits/add/', views.credit_add, name='credit_add'),
    path('credits/lookup/', views.credit_lookup, name='credit_lookup'),

    # Refunds (completed returns view)
    path('refunds/', views.refunds, name='refunds'),

    # Settings
    path('settings/', views.settings_view, name='settings'),
]
