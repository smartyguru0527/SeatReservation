"""
Models for Seat and Meeting Room reservations.
"""
from django.db import models


class SeatType(models.Model):
    """Seat type: Motion desk, Work station, Mobile desk, Standard Seat, etc."""
    name = models.CharField(max_length=64)
    color = models.CharField(max_length=20, default='#14b8a6')
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class Seat(models.Model):
    """Individual seat in the shared seating area (e.g. F-5, G-7)."""
    row = models.CharField(max_length=4)   # F, G, I, J, L
    number = models.CharField(max_length=8)  # 5, 7, 9.
    seat_type = models.ForeignKey(SeatType, on_delete=models.PROTECT, null=True, blank=True)
    is_active = models.BooleanField(default=True)  # False = no seat

    class Meta:
        ordering = ['row', 'number']
        unique_together = [['row', 'number']]

    @property
    def label(self):
        return f'{self.row}-{self.number}'

    def __str__(self):
        return self.label


class SeatBlock(models.Model):
    """Logical block/group of seats used for mini-map grouping and layout."""
    name = models.CharField(max_length=64)
    order = models.PositiveSmallIntegerField(default=0)
    row_start = models.CharField(max_length=1)  # e.g. 'A'
    row_end = models.CharField(max_length=1)    # e.g. 'F'
    col_start = models.PositiveSmallIntegerField()
    col_end = models.PositiveSmallIntegerField()
    color = models.CharField(max_length=20, default='#a7f3d0', help_text='Mini map block/frame color')

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return f'{self.name} ({self.row_start}{self.col_start}-{self.row_end}{self.col_end})'


class ReservationDisplaySetting(models.Model):
    """Singleton-style settings for reservation UI."""
    reserved_seat_color = models.CharField(
        max_length=20,
        default='#2563eb',
        help_text='Background color for reserved seats in the seat grid and mini map',
    )

    class Meta:
        verbose_name = 'Reservation display setting'
        verbose_name_plural = 'Reservation display settings'

    def __str__(self):
        return 'Display settings'


class MeetingRoom(models.Model):
    """Meeting room with capacity and display color."""
    name = models.CharField(max_length=128)
    capacity = models.PositiveSmallIntegerField(default=4)
    color = models.CharField(max_length=20, default='#8b5cf6')
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class SeatReservation(models.Model):
    """Reservation of a seat for a given date."""
    seat = models.ForeignKey(Seat, on_delete=models.CASCADE)
    guest_name = models.CharField(max_length=128)
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['date', 'seat']
        unique_together = [['seat', 'date']]

    def __str__(self):
        return f'{self.guest_name} @ {self.seat.label} on {self.date}'


class MeetingRoomReservation(models.Model):
    """Reservation of a meeting room for a time slot on a date."""
    room = models.ForeignKey(MeetingRoom, on_delete=models.CASCADE)
    guest_name = models.CharField(max_length=128)
    title = models.CharField(max_length=200, blank=True)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['date', 'start_time']

    def __str__(self):
        return f'{self.guest_name} – {self.room.name} {self.date} {self.start_time}-{self.end_time}'
