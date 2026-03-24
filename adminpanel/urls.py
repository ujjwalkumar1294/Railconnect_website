from django.urls import path
from . import views

app_name = 'adminpanel'

urlpatterns = [
    # DASHBOARD
    path('', views.admin_dashboard, name='dashboard'),

    # TRAINS
    path('trains/', views.train_list_admin, name='train_list'),
    path('trains/create/', views.train_create, name='train_create'),
    path('trains/edit/<int:train_id>/', views.train_edit, name='train_edit'),
    path('trains/delete/<int:train_id>/', views.train_delete, name='train_delete'),

    # ROUTES
    path('trains/<int:train_id>/routes/', views.manage_routes, name='manage_routes'),
    path('trains/<int:train_id>/routes/add/', views.add_route_station, name='add_route_station'),
    path('trains/<int:train_id>/routes/<int:route_id>/delete/', views.delete_route_station, name='delete_route_station'),

    # STATIONS
    path('stations/', views.station_list, name='station_list'),
    path('stations/create/', views.station_create, name='station_create'),
    path('stations/<int:pk>/delete/', views.station_delete, name='station_delete'),

    # BOOKINGS
    path('bookings/', views.booking_list_admin, name='booking_list'),
    path('bookings/<int:pk>/delete/', views.booking_delete, name='booking_delete'),

    # USERS
    path('users/', views.user_list, name='user_list'),

    # REPORTS
    path('reports/', views.reports, name='reports'),
]