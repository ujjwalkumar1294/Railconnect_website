from django.contrib import admin
from django.urls import path, include
from user import views as user_views
from trains import views as train_views
from bookings import views as booking_views

urlpatterns = [
    path('admin/', admin.site.urls),

    # User pages
    path('', user_views.landing, name='landing'),
    path('register/', user_views.register, name='register'),
    path('login/', user_views.login, name='login'),
    path('logout/', user_views.logout, name='logout'),

    # Train pages
    path('trains/', train_views.train_list, name='train_list'),

    # Booking pages
    path('book/<int:train_id>/', booking_views.book_train, name='book_train'),
    path('summary/<int:booking_id>/', booking_views.booking_summary, name='booking_summary'),
    path('cancel/<int:booking_id>/', booking_views.cancel_booking, name='cancel_booking'),
    path('my-bookings/', booking_views.my_bookings, name='my_bookings'),
    path('ticket/<int:booking_id>/', booking_views.view_ticket, name='view_ticket'),
    path("download/<int:booking_id>/", booking_views.download_ticket, name="download_ticket"),

    #  ADMIN PANEL
    path('adminpanel/', include('adminpanel.urls')),
]