from django.shortcuts import render , redirect
import random
from django.core.mail import send_mail
from django.conf import settings
from .models import *

# Create your views here.
def landing(request):
    return render(request, "landing.html")

def register(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")

        if User.objects.filter(username=username).exists():
            return render(request, "register.html", {
                "error": "Username already exists"
            })

        user = User(
            username=username,
            email=email,
            password=password
        )
        user.save()

        return redirect("login")

    return render(request, "register.html")


def login(request):

    if request.method == "POST":

        # ===== OTP VERIFICATION STEP =====
        if request.POST.get("otp"):

            entered_otp = request.POST.get("otp")
            username = request.session.get("temp_user")

            if not username:
                return redirect("login")

            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                return redirect("login")

            if user.otp == entered_otp:
                request.session["username"] = user.username
                request.session.pop("temp_user", None)

                user.otp = None
                user.save()

                return redirect("landing")

            else:
                return render(request, "login.html", {
                    "otp_required": True,
                    "error": "Invalid OTP"
                })

        # ===== FIRST LOGIN STEP =====
        username = request.POST.get("username")
        password = request.POST.get("password")

        try:
            user = User.objects.get(username=username, password=password)

            import random
            otp = str(random.randint(100000, 999999))

            user.otp = otp
            user.save()

            send_mail(
                "Your Login OTP",
                f"Your OTP is {otp}",
                settings.EMAIL_HOST_USER,
                [user.email],
                fail_silently=False,
            )

            request.session["temp_user"] = user.username

            return render(request, "login.html", {
                "otp_required": True
            })

        except User.DoesNotExist:
            return render(request, "login.html", {
                "error": "Invalid credentials"
            })

    # Default GET request
    return render(request, "login.html", {
        "otp_required": False
    })




def logout(request):
    request.session.flush()
    return redirect("landing")
