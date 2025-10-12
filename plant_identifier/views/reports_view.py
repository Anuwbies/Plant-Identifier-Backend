import csv
import io
from datetime import timedelta
from django.http import JsonResponse, HttpResponse
from django.utils.timezone import now
from plant_identifier.models import PlantHistory
from django.contrib.admin.views.decorators import staff_member_required


@staff_member_required
def generate_report(request):
    # Report period (last 30 days)
    end_date = now()
    start_date = end_date - timedelta(days=30)

    # Filter entries from last 30 days
    photos_qs = PlantHistory.objects.filter(identified_at__range=[start_date, end_date])

    # Metrics
    total_photos = photos_qs.count()
    active_users = photos_qs.values("user").distinct().count()
    plant_species_identified = photos_qs.values("scientific_name").distinct().count()

    # Success rate (user-confirmed correct) — only if you have this field
    confirmed_correct = photos_qs.filter(confidence__gte=0.8).count()
    success_rate = round((confirmed_correct / total_photos * 100), 2) if total_photos > 0 else 0

    # AI Confidence breakdown
    high_conf = photos_qs.filter(confidence__gte=0.8).count()
    medium_conf = photos_qs.filter(confidence__gte=0.5, confidence__lt=0.8).count()
    low_conf = photos_qs.filter(confidence__lt=0.5).count()

    # Recent photos (limit 10)
    recent_photos = list(
        photos_qs.order_by("-identified_at")[:10].values(
            "id", "image_url", "scientific_name", "confidence", "identified_at"
        )
    )

    # Report metadata
    metadata = {
        "report_period": f"{start_date.strftime('%b %d, %Y')} - {end_date.strftime('%b %d, %Y')}",
        "generated": end_date.strftime("%b %d, %Y %H:%M"),
    }

    # Build report data
    report_data = {
        "metadata": metadata,
        "summary": {
            "total_photos": total_photos,
            "active_users": active_users,
            "plant_species_identified": plant_species_identified,
            "success_rate": f"{success_rate}%",
        },
        "confidence_levels": {
            "high": high_conf,
            "medium": medium_conf,
            "low": low_conf,
        },
        "recent_photos": recent_photos,
    }

    # Export CSV if requested
    if request.GET.get("format") == "csv":
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(["Metric", "Value"])
        writer.writerow(["Total Photos", total_photos])
        writer.writerow(["Active Users", active_users])
        writer.writerow(["Plant Species Identified", plant_species_identified])
        writer.writerow(["Success Rate (%)", success_rate])
        writer.writerow([])
        writer.writerow(["Confidence Level", "Count"])
        writer.writerow(["High (≥80%)", high_conf])
        writer.writerow(["Medium (50–79%)", medium_conf])
        writer.writerow(["Low (<50%)", low_conf])
        response = HttpResponse(buffer.getvalue(), content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="report_{end_date.strftime("%Y%m%d")}.csv"'
        return response

    # Return JSON by default
    return JsonResponse(report_data, safe=False)
