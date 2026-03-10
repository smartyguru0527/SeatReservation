from django.urls import path
from . import views

app_name = 'reservations'

urlpatterns = [
    path('', views.seat_reservation, name='seat_reservation'),
    path('meeting-rooms/', views.meeting_room_reservation, name='meeting_room_reservation'),

    # Seat APIs
    path('api/seat-status/', views.api_seat_status, name='api_seat_status'),
    path('api/seat-grid/', views.api_seat_grid, name='api_seat_grid'),
    path('api/seat-reserve/', views.api_seat_reserve, name='api_seat_reserve'),
    path('api/seat-quick-reserve/', views.api_seat_quick_reserve, name='api_seat_quick_reserve'),

    # Meeting room APIs
    path('api/room-schedule/', views.api_room_schedule, name='api_room_schedule'),
    path('api/room-reserve/', views.api_room_reserve, name='api_room_reserve'),
]
