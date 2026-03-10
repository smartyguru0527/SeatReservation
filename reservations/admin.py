from django.contrib import admin
from .models import SeatType, Seat, MeetingRoom, SeatReservation, MeetingRoomReservation, SeatBlock, ReservationDisplaySetting


@admin.register(SeatType)
class SeatTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'order')


@admin.register(Seat)
class SeatAdmin(admin.ModelAdmin):
    list_display = ('row', 'number', 'seat_type', 'is_active')
    list_filter = ('row', 'seat_type', 'is_active')


@admin.register(MeetingRoom)
class MeetingRoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'capacity', 'color', 'order')


@admin.register(SeatReservation)
class SeatReservationAdmin(admin.ModelAdmin):
    list_display = ('guest_name', 'seat', 'date', 'created_at')
    list_filter = ('date',)
    date_hierarchy = 'date'


@admin.register(MeetingRoomReservation)
class MeetingRoomReservationAdmin(admin.ModelAdmin):
    list_display = ('guest_name', 'room', 'date', 'start_time', 'end_time', 'created_at')
    list_filter = ('date', 'room')
    date_hierarchy = 'date'


@admin.register(SeatBlock)
class SeatBlockAdmin(admin.ModelAdmin):
    list_display = ('name', 'order', 'color', 'row_start', 'row_end', 'col_start', 'col_end')
    list_editable = ('order', 'color', 'row_start', 'row_end', 'col_start', 'col_end')
    ordering = ('order', 'name')


@admin.register(ReservationDisplaySetting)
class ReservationDisplaySettingAdmin(admin.ModelAdmin):
    list_display = ('id', 'reserved_seat_color')
    list_display_links = ('id',)
    list_editable = ('reserved_seat_color',)
