"""
Views for Seat and Meeting Room reservation pages.
"""
from datetime import date, time, timedelta
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone

from .models import Seat, SeatType, SeatReservation, MeetingRoom, MeetingRoomReservation, SeatBlock, ReservationDisplaySetting


def _last_update():
    return timezone.now().strftime('%m/%d %H:%M:%S')


def seat_reservation(request):
    """Seat Reservation page"""
    setting = ReservationDisplaySetting.objects.first()
    context = {
        'page_title': 'Seat Reservation',
        'page_subtitle': "Check today's seat reservations based on the shared seating system!",
        'active_nav': 'seats',
        'last_update': _last_update(),
        'today': date.today(),
        'reserved_seat_color': (setting.reserved_seat_color if setting else '#2563eb'),
        'selected_seat_color': (setting.selected_seat_color if setting else '#ef4444'),
    }
    return render(request, 'reservations/seat_reservation.html', context)


def meeting_room_reservation(request):
    """Meeting Room Reservation page: calendar grid + sidebar."""
    context = {
        'page_title': 'Meeting Room Reservation',
        'page_subtitle': 'Check reservation status and book a meeting room.',
        'active_nav': 'rooms',
        'last_update': _last_update(),
        'today': date.today(),
    }
    return render(request, 'reservations/meeting_room_reservation.html', context)


# ----- Seat reservation data APIs -----

@require_GET
def api_seat_status(request):
    """JSON: total/available/reserved counts and reservation list for a date."""
    day = request.GET.get('date')
    if not day:
        day = date.today().isoformat()
    try:
        d = date.fromisoformat(day)
    except ValueError:
        d = date.today()

    seats = list(
        Seat.objects.filter(is_active=True).select_related('seat_type').order_by('row', 'number')
    )
    reserved_ids = set(
        SeatReservation.objects.filter(date=d).values_list('seat_id', flat=True)
    )
    total = len(seats)
    reserved = len(reserved_ids)
    available = total - reserved

    blocks = list(SeatBlock.objects.all().order_by('order', 'id'))
    block_cfgs = []
    zone_data = {}
    for idx, b in enumerate(blocks, start=1):
        block_cfgs.append(
            {
                'index': idx,
                'name': b.name,
                'row_start': b.row_start,
                'row_end': b.row_end,
                'col_start': b.col_start,
                'col_end': b.col_end,
                'color': getattr(b, 'color', '#a7f3d0') or '#a7f3d0',
            }
        )
        zone_data[idx] = {'seats': [], 'seat_ids': []}

    def seat_block(row_label: str, number_str: str):
        try:
            col = int(number_str)
        except (TypeError, ValueError):
            return None
        for cfg in block_cfgs:
            if cfg['row_start'] <= row_label <= cfg['row_end'] and cfg['col_start'] <= col <= cfg['col_end']:
                return cfg['index']
        return None
    for s in seats:
        block = seat_block(s.row, s.number)
        if block is None:
            continue
        seat_data = {
            'id': s.id,
            'label': s.label,
            'color': s.seat_type.color if s.seat_type else '#14b8a6',
            'reserved': s.id in reserved_ids,
        }
        zone_data[block]['seats'].append(seat_data)
        zone_data[block]['seat_ids'].append(s.id)

    zones = [zone_data[cfg['index']] for cfg in block_cfgs]

    reservations = SeatReservation.objects.filter(date=d).select_related('seat').order_by('seat__row', 'seat__number')
    reservation_list = [
        {'no': i + 1, 'name': r.guest_name, 'seat_info': r.seat.label, 'seat_id': r.seat_id}
        for i, r in enumerate(reservations)
    ]

    return JsonResponse({
        'date': d.isoformat(),
        'total': total,
        'available': available,
        'reserved': reserved,
        'reservations': reservation_list,
        'reserved_seat_ids': list(reserved_ids),
        'zones': zones,
        'blocks': block_cfgs,
    })


@require_GET
def api_seat_grid(request):
    """JSON: seat types and seat grid for the Select Seat panel."""
    seat_types = [
        {'id': st.id, 'name': st.name, 'color': st.color}
        for st in SeatType.objects.all().order_by('order', 'name')
    ]
    seats = Seat.objects.select_related('seat_type').order_by('row', 'number')
    by_row = {}
    for s in seats:
        by_row.setdefault(s.row, []).append({
            'id': s.id,
            'label': s.label,
            'number': s.number,
            'color': s.seat_type.color if s.seat_type else '#14b8a6',
            'is_active': s.is_active,
        })
    rows = sorted(by_row.keys())
    grid = [{'row': r, 'seats': by_row[r]} for r in rows]

    return JsonResponse({'seat_types': seat_types, 'grid': grid})


@require_POST
def api_seat_reserve(request):
    """Create a seat reservation. POST: seat_id, date, guest_name."""
    seat_id = request.POST.get('seat_id')
    day = request.POST.get('date')
    guest_name = request.POST.get('guest_name', '').strip()
    if not seat_id or not day or not guest_name:
        return JsonResponse({'ok': False, 'error': 'Missing seat_id, date, or guest_name'}, status=400)
    try:
        seat = get_object_or_404(Seat, pk=seat_id, is_active=True)
        d = date.fromisoformat(day)
    except (ValueError, TypeError):
        return JsonResponse({'ok': False, 'error': 'Invalid date'}, status=400)

    if SeatReservation.objects.filter(seat=seat, date=d).exists():
        return JsonResponse({'ok': False, 'error': 'This seat is already reserved for that date'}, status=400)

    SeatReservation.objects.create(seat=seat, date=d, guest_name=guest_name)
    return JsonResponse({'ok': True})


@require_POST
def api_seat_quick_reserve(request):
    """Create a reservation on the first available seat for a given date."""
    day = request.POST.get('date')
    guest_name = request.POST.get('guest_name', '').strip()
    if not guest_name:
        return JsonResponse({'ok': False, 'error': 'Missing guest_name'}, status=400)

    if not day:
        day = date.today().isoformat()
    try:
        d = date.fromisoformat(day)
    except (ValueError, TypeError):
        return JsonResponse({'ok': False, 'error': 'Invalid date'}, status=400)

    reserved_ids = SeatReservation.objects.filter(date=d).values_list('seat_id', flat=True)
    seat = (
        Seat.objects.filter(is_active=True)
        .exclude(id__in=reserved_ids)
        .order_by('row', 'number')
        .first()
    )
    if not seat:
        return JsonResponse({'ok': False, 'error': 'No available seats for this date'}, status=400)

    reservation = SeatReservation.objects.create(seat=seat, date=d, guest_name=guest_name)
    return JsonResponse(
        {
            'ok': True,
            'reservation_id': reservation.id,
            'seat_id': seat.id,
            'seat_label': seat.label,
            'date': d.isoformat(),
        }
    )


# ----- Meeting room data APIs -----

@require_GET
def api_room_schedule(request):
    """JSON: rooms and reservations for a date for the time grid."""
    day = request.GET.get('date')
    if not day:
        day = date.today().isoformat()
    try:
        d = date.fromisoformat(day)
    except ValueError:
        d = date.today()

    rooms = list(MeetingRoom.objects.all().order_by('order', 'name'))
    reservations = MeetingRoomReservation.objects.filter(
        date=d
    ).select_related('room').order_by('room', 'start_time')

    # Build per-room blocks for frontend
    by_room = {r.id: [] for r in rooms}
    for rev in reservations:
        by_room[rev.room_id].append({
            'id': rev.id,
            'guest_name': rev.guest_name,
            'title': rev.title,
            'start': rev.start_time.strftime('%H:%M'),
            'end': rev.end_time.strftime('%H:%M'),
        })

    room_list = [
        {'id': r.id, 'name': r.name, 'capacity': r.capacity, 'color': r.color, 'slots': by_room[r.id]}
        for r in rooms
    ]

    return JsonResponse({
        'date': d.isoformat(),
        'rooms': room_list,
    })


@require_POST
def api_room_reserve(request):
    """Create a meeting room reservation. POST: room_id, date, start_time, end_time, guest_name, title."""
    room_id = request.POST.get('room_id')
    day = request.POST.get('date')
    start_time_str = request.POST.get('start_time', '09:00')
    end_time_str = request.POST.get('end_time', '10:00')
    guest_name = request.POST.get('guest_name', '').strip()
    title = request.POST.get('title', '').strip()
    if not room_id or not day or not guest_name:
        return JsonResponse({'ok': False, 'error': 'Missing room_id, date, or guest_name'}, status=400)
    try:
        room = get_object_or_404(MeetingRoom, pk=room_id)
        d = date.fromisoformat(day)
        start_t = time.fromisoformat(start_time_str)
        end_t = time.fromisoformat(end_time_str)
    except (ValueError, TypeError):
        return JsonResponse({'ok': False, 'error': 'Invalid date or time'}, status=400)
    if end_t <= start_t:
        return JsonResponse({'ok': False, 'error': 'End time must be after start time'}, status=400)

    overlapping = MeetingRoomReservation.objects.filter(
        room=room, date=d
    ).filter(start_time__lt=end_t, end_time__gt=start_t)
    if overlapping.exists():
        return JsonResponse({'ok': False, 'error': 'This time slot is already booked'}, status=400)

    MeetingRoomReservation.objects.create(
        room=room, date=d, guest_name=guest_name, title=title,
        start_time=start_t, end_time=end_t
    )
    return JsonResponse({'ok': True})


# ----- Quick Start -----
