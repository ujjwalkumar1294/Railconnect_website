from django.shortcuts import render
from .models import Train, TrainRoute, Station


def train_list(request):
    from_station = request.GET.get("from", "").strip()
    to_station = request.GET.get("to", "").strip()

    trains_data = []
    search_error = None

    trains = Train.objects.all()

    # If user is searching, validate stations exist first
    if from_station and to_station:
        from_station_obj = Station.objects.filter(name__icontains=from_station).first()
        to_station_obj = Station.objects.filter(name__icontains=to_station).first()

        if not from_station_obj:
            search_error = f"Station '{from_station}' not found."
        elif not to_station_obj:
            search_error = f"Station '{to_station}' not found."
        elif from_station_obj == to_station_obj:
            search_error = "Source and destination cannot be the same."

        if search_error:
            return render(request, "train_list.html", {
                "trains_data": [],
                "from_query": from_station,
                "to_query": to_station,
                "search_error": search_error,
            })

    for train in trains:
        routes = TrainRoute.objects.filter(train=train).order_by("stop_order")

        # If train has no routes yet, still show it (no specific from/to)
        if not routes.exists():
            if from_station and to_station:
                # Can't match a specific route on a routeless train — skip in search
                continue
            # Show routeless train in the full listing
            trains_data.append({
                "train": train,
                "departure": None,
                "arrival": None,
                "display_from": "Route not configured",
                "display_to": "Route not configured",
                "price": train.price,
                "available_seats": train.available_seats,
                "stops": [],
                "no_route": True,
            })
            continue

        first_route = routes.first()
        last_route = routes.last()

        departure = first_route.departure_time
        arrival = last_route.arrival_time
        display_from = first_route.station.name
        display_to = last_route.station.name

        # If user searched specific stations
        if from_station and to_station:
            from_route = routes.filter(station=from_station_obj).first()
            to_route = routes.filter(station=to_station_obj).first()

            if not from_route or not to_route:
                continue  # This train doesn't serve both stations

            if from_route.stop_order >= to_route.stop_order:
                continue  # Wrong direction

            departure = from_route.departure_time
            arrival = to_route.arrival_time
            display_from = from_station_obj.name
            display_to = to_station_obj.name

        trains_data.append({
            "train": train,
            "departure": departure,
            "arrival": arrival,
            "display_from": display_from,
            "display_to": display_to,
            "price": train.price,
            "available_seats": train.available_seats,
            "stops": routes,
            "no_route": False,
        })

    return render(request, "train_list.html", {
        "trains_data": trains_data,
        "from_query": from_station,
        "to_query": to_station,
        "search_error": search_error,
        "total_found": len(trains_data),
    })