from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.db.models import Count, Sum, Q
from django.utils import timezone
import json
from django.views.decorators.csrf import csrf_exempt

from user.models import User
from trains.models import Train, Station, TrainRoute
from bookings.models import Booking


# =========================
# SIMPLE ADMIN CHECK
# =========================
def is_admin(request):
    return bool(request.session.get('username'))


# =========================
# DASHBOARD
# =========================
def admin_dashboard(request):
    if not is_admin(request):
        return redirect('login')

    today = timezone.now().date()
    recent_bookings = Booking.objects.select_related(
        'train', 'from_station', 'to_station'
    ).order_by('-id')[:8]

    context = {
        'total_users': User.objects.count(),
        'total_trains': Train.objects.count(),
        'today_bookings': Booking.objects.filter(travel_date=today).count(),
        'total_revenue': Booking.objects.aggregate(total=Sum('total_price'))['total'] or 0,
        'recent_bookings': recent_bookings,
    }

    return render(request, 'adminpanel/dashboard.html', context)


# =========================
# TRAIN MANAGEMENT
# =========================
def train_list_admin(request):
    if not is_admin(request):
        return redirect('login')

    query = request.GET.get('q', '')
    trains = Train.objects.all()

    if query:
        trains = trains.filter(
            Q(train_name__icontains=query) | Q(train_number__icontains=query)
        )

    # Annotate each train with route count so we can warn in UI
    trains = trains.prefetch_related('routes')

    return render(request, 'adminpanel/trains.html', {
        'trains': trains,
        'query': query,
    })


def train_create(request):
    if not is_admin(request):
        return redirect('login')

    if request.method == "POST":
        train_number = request.POST.get("train_number")
        train_name = request.POST.get("train_name")
        total_seats = int(request.POST.get("total_seats"))
        price = float(request.POST.get("price"))

        if Train.objects.filter(train_number=train_number).exists():
            return render(request, "adminpanel/train_form.html", {
                "error": f"Train number {train_number} already exists."
            })

        Train.objects.create(
            train_number=train_number,
            train_name=train_name,
            total_seats=total_seats,
            available_seats=total_seats,
            price=price
        )
        return redirect("adminpanel:train_list")

    return render(request, "adminpanel/train_form.html")


def train_edit(request, train_id):
    if not is_admin(request):
        return redirect('login')

    train = get_object_or_404(Train, id=train_id)

    if request.method == "POST":
        train.train_number = request.POST.get("train_number")
        train.train_name = request.POST.get("train_name")
        new_total = int(request.POST.get("total_seats"))
        train.price = float(request.POST.get("price"))

        # Adjust available seats proportionally
        diff = new_total - train.total_seats
        train.total_seats = new_total
        train.available_seats = max(0, train.available_seats + diff)

        train.save()
        return redirect("adminpanel:train_list")

    return render(request, "adminpanel/train_edit.html", {"train": train})


def train_delete(request, train_id):
    if not is_admin(request):
        return redirect('login')
    train = get_object_or_404(Train, id=train_id)
    train.delete()
    return redirect("adminpanel:train_list")


# =========================
# STATION MANAGEMENT
# =========================
def station_list(request):
    if not is_admin(request):
        return redirect('login')

    query = request.GET.get('q', '')
    stations = Station.objects.all()

    if query:
        stations = stations.filter(
            Q(name__icontains=query) | Q(code__icontains=query)
        )

    return render(request, 'adminpanel/stations.html', {
        'stations': stations,
        'query': query,
    })


def station_create(request):
    if not is_admin(request):
        return redirect('login')

    if request.method == "POST":
        code = request.POST.get("code", "").upper().strip()
        name = request.POST.get("name", "").strip()

        if Station.objects.filter(code=code).exists():
            # Pass error back to stations page
            stations = Station.objects.all()
            return render(request, 'adminpanel/stations.html', {
                'stations': stations,
                'query': '',
                'station_error': f"Station code '{code}' already exists.",
            })

        Station.objects.create(code=code, name=name)
        return redirect('adminpanel:station_list')

    return redirect('adminpanel:station_list')


def station_delete(request, pk):
    if not is_admin(request):
        return redirect('login')
    station = get_object_or_404(Station, pk=pk)
    station.delete()
    return redirect('adminpanel:station_list')


# =========================
# ROUTE MANAGEMENT
# =========================
def manage_routes(request, train_id):
    if not is_admin(request):
        return redirect('login')

    train = get_object_or_404(Train, id=train_id)
    routes = TrainRoute.objects.filter(train=train).order_by('stop_order')
    stations = Station.objects.all()

    return render(request, 'adminpanel/manage_routes.html', {
        'train': train,
        'routes': routes,
        'stations': stations,
    })


@csrf_exempt
def add_route_station(request, train_id):
    if request.method == "POST":
        train = get_object_or_404(Train, id=train_id)
        data = json.loads(request.body)

        station = get_object_or_404(Station, id=data["station_id"])

        # Check if station already in this route
        if TrainRoute.objects.filter(train=train, station=station).exists():
            return JsonResponse({"success": False, "error": "Station already in route."})

        last_route = TrainRoute.objects.filter(train=train).order_by('-stop_order').first()
        next_order = 1 if not last_route else last_route.stop_order + 1

        TrainRoute.objects.create(
            train=train,
            station=station,
            stop_order=next_order,
            arrival_time=data.get("arrival_time") or None,
            departure_time=data.get("departure_time") or None,
        )

        return JsonResponse({"success": True})

    return JsonResponse({"success": False})


@csrf_exempt
def delete_route_station(request, train_id, route_id):
    if request.method == "DELETE":
        route = get_object_or_404(TrainRoute, id=route_id, train_id=train_id)
        route.delete()
        return JsonResponse({"success": True})
    return JsonResponse({"success": False})


# =========================
# BOOKING ADMIN
# =========================
def booking_list_admin(request):
    if not is_admin(request):
        return redirect('login')

    query = request.GET.get('q', '')
    bookings = Booking.objects.select_related(
        'train', 'from_station', 'to_station'
    ).order_by('-id')

    if query:
        bookings = bookings.filter(
            Q(pnr__icontains=query) | Q(username__icontains=query)
        )

    return render(request, 'adminpanel/bookings.html', {
        'bookings': bookings,
        'query': query,
    })


def booking_delete(request, pk):
    if not is_admin(request):
        return redirect('login')

    booking = get_object_or_404(Booking, pk=pk)

    # Restore seats when admin deletes a booking
    train = booking.train
    train.available_seats += booking.passengers
    train.save()

    booking.delete()
    return redirect('adminpanel:booking_list')


# =========================
# USER MANAGEMENT
# =========================
def user_list(request):
    if not is_admin(request):
        return redirect('login')

    query = request.GET.get('q', '')
    users = User.objects.all()

    if query:
        users = users.filter(
            Q(username__icontains=query) | Q(email__icontains=query)
        )

    # Since Booking uses username CharField (not FK to User),
    # we count manually to avoid ORM annotation errors
    user_data = []
    for user in users:
        booking_count = Booking.objects.filter(username=user.username).count()
        user_data.append({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'booking_count': booking_count,
        })

    return render(request, 'adminpanel/users.html', {
        'users': user_data,
        'query': query,
    })


# =========================
# REPORTS
# =========================
def reports(request):
    if not is_admin(request):
        return redirect('login')

    total_bookings = Booking.objects.count()
    total_revenue = Booking.objects.aggregate(total=Sum('total_price'))['total'] or 0

    # Group by train (since there's no source/destination field on Train model)
    top_routes = (
        Booking.objects
        .values('train__train_name', 'train__train_number')
        .annotate(count=Count('id'), revenue=Sum('total_price'))
        .order_by('-count')[:10]
    )

    return render(request, 'adminpanel/reports.html', {
        'total_bookings': total_bookings,
        'total_revenue': total_revenue,
        'top_routes': top_routes,
    })