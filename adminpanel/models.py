


from django.db import models
from trains.models import Train
from user.models import User


class Booking(models.Model):
    """
    Enhanced Booking model for admin panel compatibility.
    Keeps compatibility with existing booking system.
    """
    STATUS_CHOICES = [
        ('confirmed', 'Confirmed'),
        ('pending', 'Pending'),
        ('cancelled', 'Cancelled'),
    ]

    
    username = models.CharField(max_length=50)
    train = models.ForeignKey(Train, on_delete=models.CASCADE, related_name='admin_bookings')
    travel_date = models.DateField(null=True, blank=True)
    passengers = models.IntegerField(default=1)
    passenger_details = models.TextField(null=True, blank=True)
    pnr = models.CharField(max_length=10, unique=True, null=True, blank=True)
    total_price = models.IntegerField(default=0)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='confirmed')
    booked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'adminpanel_booking'  

    def save(self, *args, **kwargs):
        if not self.pnr:
            import random
            self.pnr = 'PNR' + str(random.randint(100000, 999999))
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.pnr} - {self.username} on {self.train.train_name}"

    @property
    def seats_booked(self):
        """Alias for admin panel compatibility"""
        return self.passengers

    @property
    def total_amount(self):
        """Alias for admin panel compatibility"""
        return self.total_price

    @property
    def journey_date(self):
        """Alias for admin panel compatibility"""
        return self.travel_date