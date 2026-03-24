from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.cache import cache_control
from datetime import date
from trains.models import Train, TrainRoute, Station
from bookings.models import Booking
from user.models import User
from django.core.mail import send_mail
from django.conf import settings
import random


def booking_page(request):
    if not request.session.get("username"):
        return redirect("login")

    return render(request, "booking.html")



@cache_control(no_cache=True, no_store=True, must_revalidate=True)
def book_train(request, train_id):

    if not request.session.get("username"):
        return redirect("login")

    train = get_object_or_404(Train, id=train_id)

    routes = TrainRoute.objects.filter(train=train).order_by("stop_order")

    if not routes.exists():
        return redirect("train_list")

    segments = 0
    total_price = None
    error = None

    selected_from_id = None
    selected_to_id = None

    if request.method == "POST":

        selected_from_id = request.POST.get("from_station")
        selected_to_id = request.POST.get("to_station")
        travel_date = request.POST.get("travel_date")
        passengers = int(request.POST.get("passengers"))

        from_route = routes.filter(station_id=selected_from_id).first()
        to_route = routes.filter(station_id=selected_to_id).first()

        # Validate route order
        if not from_route or not to_route or from_route.stop_order >= to_route.stop_order:
            error = "Invalid station selection"
        else:
            segments = to_route.stop_order - from_route.stop_order

            # Dynamic pricing using train.price
            total_price = segments * train.price * passengers

            # Prevent past booking
            if date.fromisoformat(travel_date) < date.today():
                error = "You cannot select a past date"

            # Check seat availability
            elif passengers > train.available_seats:
                error = "Not enough seats available"

            else:
                # Collect passenger details
                details = ""
                for i in range(1, passengers + 1):
                    name = request.POST.get(f"name_{i}")
                    age = request.POST.get(f"age_{i}")
                    gender = request.POST.get(f"gender_{i}")
                    details += f"{name}, {age}, {gender}\n"

                # Generate PNR
                pnr = "PNR" + str(random.randint(100000, 999999))

                booking = Booking.objects.create(
                    pnr=pnr,
                    username=request.session.get("username"),
                    train=train,
                    from_station=from_route.station,
                    to_station=to_route.station,
                    travel_date=travel_date,
                    passengers=passengers,
                    passenger_details=details,
                    total_price=total_price
                )

                # Reduce seats
                train.available_seats -= passengers
                train.save()

                # Send email
                user = User.objects.get(username=request.session.get("username"))

                message = f"""
🎟 TRAIN TICKET CONFIRMATION 🎟

PNR: {booking.pnr}

Train: {train.train_name} ({train.train_number})
From: {from_route.station.name}
To: {to_route.station.name}
Date: {travel_date}

Departure: {from_route.departure_time}
Arrival: {to_route.arrival_time}

Passengers:
{details}

Total Fare: ₹{total_price}

Thank you for booking with RailConnect 🚆
"""

                send_mail(
                    subject="Your Train Ticket Confirmation",
                    message=message,
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=[user.email],
                    fail_silently=False,
                )

                return redirect("booking_summary", booking_id=booking.id)

    return render(request, "bookings.html", {
        "train": train,
        "routes": routes,
        "error": error,
        "selected_from": selected_from_id,
        "selected_to": selected_to_id,
        "total_price": total_price,
    })
    
def booking_summary(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    # Get selected segment routes for departure & arrival time
    routes = TrainRoute.objects.filter(
        train=booking.train
    ).order_by("stop_order")

    from_route = routes.filter(station=booking.from_station).first()
    to_route = routes.filter(station=booking.to_station).first()

    departure = from_route.departure_time if from_route else None
    arrival = to_route.arrival_time if to_route else None

    context = {
        "booking": booking,
        "source": booking.from_station.name if booking.from_station else None,
        "destination": booking.to_station.name if booking.to_station else None,
        "departure": departure,
        "arrival": arrival,
    }

    return render(request, "booking_summary.html", context)


def cancel_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    train = booking.train
    train.available_seats += booking.passengers
    train.save()

    booking.delete()

    return redirect("my_bookings")

def my_bookings(request):

    if not request.session.get("username"):
        return redirect("login")

    username = request.session.get("username")

    bookings = Booking.objects.filter(
        username=username
    ).select_related("train", "from_station", "to_station").order_by("-id")

    return render(request, "my_bookings.html", {
        "bookings": bookings
    })
    
def view_ticket(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    return render(request, "ticket.html", {"booking": booking})


from django.http import HttpResponse
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.platypus import Table
from reportlab.lib.pagesizes import A4


def download_ticket(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Ticket_{booking.pnr}.pdf"'

    doc = SimpleDocTemplate(response, pagesize=A4)
    elements = []

    styles = getSampleStyleSheet()

    elements.append(Paragraph("<b>RailConnect Ticket</b>", styles['Title']))
    elements.append(Spacer(1, 0.3 * inch))

    data = [
        ["PNR", booking.pnr],
        ["Train", f"{booking.train.train_name} ({booking.train.train_number})"],
        ["Date", str(booking.travel_date)],
        ["Passengers", str(booking.passengers)],
        ["Total Fare", f"₹{booking.total_price}"],
    ]

    table = Table(data, colWidths=[2 * inch, 4 * inch])
    elements.append(table)

    doc.build(elements)
    return response