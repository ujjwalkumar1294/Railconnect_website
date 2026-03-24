from django.db import models

# Create your models here.

from django.db import models
import random

class Booking(models.Model):

    username = models.CharField(max_length=50)

    # Train relation
    train = models.ForeignKey(
        "trains.Train",
        on_delete=models.CASCADE,
        related_name="bookings"
    )

    # Journey Segment
    from_station = models.ForeignKey(
        "trains.Station",
        on_delete=models.CASCADE,
        related_name="bookings_from",
        null=True,
        blank=True
    )

    to_station = models.ForeignKey(
        "trains.Station",
        on_delete=models.CASCADE,
        related_name="bookings_to",
        null=True,
        blank=True
    )

    travel_date = models.DateField(null=True, blank=True)

    passengers = models.IntegerField(default=1)

    passenger_details = models.TextField(null=True, blank=True)

    # ✅ NEW FIELD — Seat Numbers (Comma separated)
    seat_numbers = models.TextField(
        null=True,
        blank=True,
        help_text="Comma separated seat numbers"
    )

    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    pnr = models.CharField(
        max_length=12,
        unique=True,
        null=True,
        blank=True
    )

    status = models.CharField(
        max_length=20,
        default="CONFIRMED"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.pnr:
            self.pnr = "PNR" + str(random.randint(100000, 999999))
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.pnr} - {self.train.train_name}"
 