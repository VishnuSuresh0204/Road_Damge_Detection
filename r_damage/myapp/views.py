import os

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.conf import settings
from django.db.models import Count
from django.utils import timezone

from .models import *
from .ml.yolo_detector import detect_road_damage


# -------------------------------------------------
# LOGIN CHECK
# -------------------------------------------------

def require_login(request, redirect_url="/login"):
    if "lid" not in request.session:
        messages.error(request, "Please login first")
        return redirect(redirect_url)
    return None


def require_admin(request, redirect_url="/login"):

    check = require_login(request, redirect_url)
    if check:
        return check

    if request.session.get("usertype") != "Admin":
        messages.error(request, "Admin access required")
        return redirect("/dashboard")

    return None

# -------------------------------------------------
# INDEX
# -------------------------------------------------

def index(request):
    logout(request)
    return render(request, "index.html")

# -------------------------------------------------
# LOGIN
# -------------------------------------------------

def login_view(request):

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user:

            login(request, user)
            request.session["lid"] = user.id
            request.session["usertype"] = user.usertype
            request.session["username"] = user.username

            if user.usertype == "Admin":
                return redirect("/admin_home")

            return redirect("/dashboard")

        messages.error(request, "Invalid username or password")
        return redirect("/login")

    return render(request, "login.html")


def signout(request):
    logout(request)
    request.session.flush()
    return redirect("/")

# -------------------------------------------------
# REGISTRATION
# -------------------------------------------------

def register_view(request):

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        if not username or not password:
            messages.error(request, "Username and password are required")
            return redirect("/register")

        if Login.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
            return redirect("/register")

        if password != confirm_password:
            messages.error(request, "Passwords do not match")
            return redirect("/register")

        login_obj = Login.objects.create_user(
            username=username,
            email=request.POST.get("email"),
            password=password,
            usertype="User",
            viewpassword=password
        )

        UserProfile.objects.create(
            user=login_obj,
            name=request.POST.get("name"),
            phone=request.POST.get("phone"),
            address=request.POST.get("address")
        )

        messages.success(request, "Registration successful. Please log in")
        return redirect("/login")

    return render(request, "register.html")

# -------------------------------------------------
# USER DASHBOARD & REPORTING
# -------------------------------------------------

def user_home(request):

    check = require_login(request)
    if check:
        return check

    try:
        user = Login.objects.get(id=request.session["lid"])
    except Login.DoesNotExist:
        request.session.flush()
        return redirect("/login")

    reports = RoadDamage.objects.filter(user=user)

    context = {
        "total_reports": reports.count(),
        "potholes": reports.filter(damage_type="Pothole").count(),
        "cracks": reports.filter(damage_type="Crack").count(),
        "surface_damage": reports.filter(damage_type="Surface Damage").count(),
        "high_severity": reports.filter(severity="High").count(),
        "medium_severity": reports.filter(severity="Medium").count(),
        "low_severity": reports.filter(severity="Low").count(),
        "completed": reports.filter(status="Completed").count(),
        "under_repair": reports.filter(status="Under Repair").count(),
        "pending": reports.exclude(status="Completed").count(),
        "recent_reports": reports[:5]
    }

    return render(request, "USER/home.html", context)


# def report_damage(request):

#     check = require_login(request)
#     if check:
#         return check

#     try:
#         user = Login.objects.get(id=request.session["lid"])
#     except Login.DoesNotExist:
#         request.session.flush()
#         return redirect("/login")

#     if request.method == "POST":

#         image = request.FILES.get("image")
#         description = request.POST.get("description")
#         location_name = request.POST.get("location_name")
#         latitude = request.POST.get("latitude") or None
#         longitude = request.POST.get("longitude") or None

#         if not image:
#             messages.error(request, "Please choose an image to upload")
#             return render(request, "USER/report_damage.html")

#         # Users only upload — no detection runs here. An admin runs
#         # detection separately via admin_run_detection() below.
#         report = RoadDamage.objects.create(
#             user=user,
#             image=image,
#             description=description,
#             location_name=location_name,
#             latitude=latitude,
#             longitude=longitude
#         )

#         messages.success(request, "Road damage report submitted. It will be reviewed shortly")
#         return redirect(f"/report_detail/{report.pk}")

#     return render(request, "USER/report_damage.html")


def report_detail(request, pk):

    check = require_login(request)
    if check:
        return check

    try:
        report = RoadDamage.objects.get(pk=pk)
    except RoadDamage.DoesNotExist:
        messages.error(request, "That report doesn't exist")
        return redirect("/dashboard")

    is_owner = report.user_id == request.session["lid"]
    is_admin = request.session.get("usertype") == "Admin"

    if not is_owner and not is_admin:
        messages.error(request, "You do not have permission to view this report")
        return redirect("/dashboard")

    return render(
        request,
        "USER/report_detail.html",
        {
            "report": report,
            "is_admin": is_admin
        }
    )


def my_reports(request):

    check = require_login(request)
    if check:
        return check

    try:
        user = Login.objects.get(id=request.session["lid"])
    except Login.DoesNotExist:
        request.session.flush()
        return redirect("/login")

    reports = RoadDamage.objects.filter(user=user)

    return render(request, "USER/my_reports.html", {"val": reports})

# -------------------------------------------------
# ADMIN
# -------------------------------------------------

def admin_home(request):

    check = require_admin(request)
    if check:
        return check

    reports = RoadDamage.objects.all()

    context = {
        "total_users": Login.objects.count(),
        "total_reports": reports.count(),
        "reported": reports.filter(status="Reported").count(),
        "verified": reports.filter(status="Verified").count(),
        "assigned": reports.filter(status="Assigned").count(),
        "under_repair": reports.filter(status="Under Repair").count(),
        "completed": reports.filter(status="Completed").count(),
        "rejected": reports.filter(status="Rejected").count(),
        "high_severity": reports.filter(severity="High").count(),
        "medium_severity": reports.filter(severity="Medium").count(),
        "low_severity": reports.filter(severity="Low").count(),
        "by_type": reports.values("damage_type").annotate(count=Count("id")),
        "recent_reports": reports[:10]
    }

    return render(request, "ADMIN/home.html", context)


def admin_view_reports(request):

    check = require_admin(request)
    if check:
        return check

    status_filter = request.GET.get("status")

    reports = RoadDamage.objects.all()

    if status_filter:
        reports = reports.filter(status=status_filter)

    return render(
        request,
        "ADMIN/view_reports.html",
        {
            "val": reports,
            "status_filter": status_filter
        }
    )



def admin_verify_report(request):

    check = require_admin(request)
    if check:
        return check

    pk = request.GET.get("id")

    try:
        report = RoadDamage.objects.get(pk=pk)
    except RoadDamage.DoesNotExist:
        messages.error(request, "That report doesn't exist")
        return redirect("/admin_view_reports")

    report.status = "Verified"
    report.save()

    messages.success(request, f"Report #{report.pk} verified")

    return redirect("/admin_view_reports")


def admin_reject_report(request):

    check = require_admin(request)
    if check:
        return check

    pk = request.GET.get("id")

    try:
        report = RoadDamage.objects.get(pk=pk)
    except RoadDamage.DoesNotExist:
        messages.error(request, "That report doesn't exist")
        return redirect("/admin_view_reports")

    report.status = "Rejected"
    report.save()

    messages.info(request, f"Report #{report.pk} rejected")

    return redirect("/admin_view_reports")


def admin_assign_repair(request):

    check = require_admin(request)
    if check:
        return check

    pk = request.GET.get("id")

    try:
        report = RoadDamage.objects.get(pk=pk)
    except RoadDamage.DoesNotExist:
        messages.error(request, "That report doesn't exist")
        return redirect("/admin_view_reports")

    if request.method == "POST":

        assigned_to = request.POST.get("assigned_to")
        repair_description = request.POST.get("repair_description")

        if not assigned_to:
            messages.error(request, "Please specify who the repair is assigned to")
            return render(request, "ADMIN/assign_repair.html", {"report": report})

        Repair.objects.create(
            damage=report,
            assigned_to=assigned_to,
            repair_description=repair_description,
            status="Assigned"
        )

        report.status = "Assigned"
        report.save()

        messages.success(request, f"Repair assigned for report #{report.pk}")

        return redirect("/admin_view_reports")

    return render(request, "ADMIN/assign_repair.html", {"report": report})


def admin_update_repair(request):

    check = require_admin(request)
    if check:
        return check

    pk = request.GET.get("id")

    try:
        repair = Repair.objects.get(pk=pk)
    except Repair.DoesNotExist:
        messages.error(request, "That repair record doesn't exist")
        return redirect("/admin_view_reports")

    if request.method == "POST":

        status = request.POST.get("status", repair.status)
        repair_description = request.POST.get("repair_description", repair.repair_description)

        repair.status = status
        repair.repair_description = repair_description

        if status == "Completed" and not repair.completed_date:
            repair.completed_date = timezone.now()

        repair.save()

        repair.damage.status = repair.status
        repair.damage.save()

        messages.success(request, f"Repair #{repair.pk} updated")

        return redirect("/admin_view_reports")

    return render(request, "ADMIN/update_repair.html", {"repair": repair})

def report_damage(request):

    check = require_login(request)
    if check:
        return check

    try:
        user = Login.objects.get(id=request.session["lid"])
    except Login.DoesNotExist:
        request.session.flush()
        return redirect("/login")

    if request.method == "POST":

        image = request.FILES.get("image")
        description = request.POST.get("description")
        location_name = request.POST.get("location_name")
        latitude = request.POST.get("latitude") or None
        longitude = request.POST.get("longitude") or None

        if not image:
            messages.error(request, "Please choose an image to upload")
            return render(request, "USER/report_damage.html")

        # First save the uploaded image
        report = RoadDamage.objects.create(
            user=user,
            image=image,
            description=description,
            location_name=location_name,
            latitude=latitude,
            longitude=longitude
        )

        try:
            # Full path of uploaded image
            image_path = report.image.path

            # Run YOLO detection
            detections, result_path = detect_road_damage(image_path)

            if detections:

                # Get detection with highest confidence
                best_detection = max(
                    detections,
                    key=lambda x: x["confidence"]
                )

                report.damage_type = best_detection["damage_type"]
                report.confidence = best_detection["confidence"] * 100

                # Calculate severity based on confidence
                confidence = report.confidence

                if confidence >= 80:
                    report.severity = "High"
                elif confidence >= 50:
                    report.severity = "Medium"
                else:
                    report.severity = "Low"

            else:
                report.damage_type = "no_damage"
                report.confidence = 0
                report.severity = "Low"

            # Save detected result image
            relative_result_path = os.path.relpath(
                result_path,
                settings.MEDIA_ROOT
            )

            report.result_image.name = relative_result_path.replace(
                "\\",
                "/"
            )

            report.save()

        except Exception as e:

            print("YOLO Detection Error:", e)

            messages.warning(
                request,
                "Report uploaded, but AI detection could not be completed."
            )

        messages.success(
            request,
            "Road damage report submitted and analyzed successfully"
        )

        return redirect(f"/report_details/{report.pk}/")

    return render(request, "USER/report_damage.html")