from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class Station(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)

    def __str__(self):
        return f"{self.name} ({self.code})"


class Train(models.Model):
    train_number = models.CharField(max_length=20, unique=True)
    train_name = models.CharField(max_length=100)
    total_seats = models.IntegerField()
    available_seats = models.IntegerField(default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        if not self.pk:  # Only when creating new train
            self.available_seats = self.total_seats
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.train_name} ({self.train_number})"


class TrainRoute(models.Model):
    train = models.ForeignKey(Train, on_delete=models.CASCADE, related_name="routes")
    station = models.ForeignKey(Station, on_delete=models.CASCADE)
    arrival_time = models.TimeField()
    departure_time = models.TimeField()
    stop_order = models.IntegerField()

    class Meta:
        ordering = ["stop_order"]
        unique_together = ("train", "stop_order")

    def __str__(self):
        return f"{self.train.train_name} - {self.station.name}"


class TrainSegment(models.Model):
    train = models.ForeignKey(Train, on_delete=models.CASCADE, related_name="segments")
    start_station = models.ForeignKey(Station, on_delete=models.CASCADE, related_name="segment_start")
    end_station = models.ForeignKey(Station, on_delete=models.CASCADE, related_name="segment_end")
    segment_order = models.IntegerField()

    class Meta:
        ordering = ["segment_order"]

    def __str__(self):
        return f"{self.start_station} → {self.end_station}"


class SeatAvailability(models.Model):
    segment = models.ForeignKey(TrainSegment, on_delete=models.CASCADE, related_name="seat_records")
    travel_date = models.DateField()
    available_seats = models.IntegerField()

    class Meta:
        unique_together = ("segment", "travel_date")

    def __str__(self):
        return f"{self.segment} - {self.travel_date}"
    
@receiver(post_save, sender=TrainRoute)
def create_segments(sender, instance, **kwargs):
    train = instance.train
    routes = TrainRoute.objects.filter(train=train).order_by("stop_order")

    TrainSegment.objects.filter(train=train).delete()

    for i in range(len(routes) - 1):
        TrainSegment.objects.create(
            train=train,
            start_station=routes[i].station,
            end_station=routes[i + 1].station,
            segment_order=i + 1,
        )