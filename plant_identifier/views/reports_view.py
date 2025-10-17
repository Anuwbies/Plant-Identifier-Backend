import csv
import io
from datetime import timedelta
from django.http import JsonResponse, HttpResponse
from django.utils.timezone import now
from plant_identifier.models import PlantHistory
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Count, Avg, Q
from django.contrib.auth.models import User


@csrf_exempt
@require_http_methods(["GET"])
def generate_report(request):
    """Generate comprehensive plant identification reports"""
    
    # Get query parameters
    period = request.GET.get('period', '30')  # days
    report_type = request.GET.get('type', 'summary')  # summary, detailed, trends
    export_format = request.GET.get('format', 'json')  # json, csv
    
    try:
        days = int(period)
    except ValueError:
        days = 30
    
    # Date range
    end_date = now()
    start_date = end_date - timedelta(days=days)
    
    # Filter entries
    photos_qs = PlantHistory.objects.filter(identified_at__range=[start_date, end_date])
    
    # Core Metrics
    total_photos = photos_qs.count()
    active_users = photos_qs.values("user").distinct().count()
    plant_species_identified = photos_qs.values("scientific_name").distinct().count()
    
    # Success rate (based on confidence)
    confirmed_correct = photos_qs.filter(confidence__gte=0.8).count()
    success_rate = round((confirmed_correct / total_photos * 100), 2) if total_photos > 0 else 0
    
    # AI Confidence breakdown
    high_conf = photos_qs.filter(confidence__gte=0.8).count()
    medium_conf = photos_qs.filter(confidence__gte=0.5, confidence__lt=0.8).count()
    low_conf = photos_qs.filter(confidence__lt=0.5).count()
    
    # Average confidence
    avg_confidence = photos_qs.aggregate(avg=Avg('confidence'))['avg'] or 0
    
    # Top identified species
    top_species = list(
        photos_qs.values('scientific_name', 'common_name')
        .annotate(count=Count('id'))
        .order_by('-count')[:10]
    )
    
    # Daily breakdown
    daily_data = []
    for i in range(days):
        day = start_date + timedelta(days=i)
        day_end = day + timedelta(days=1)
        day_count = photos_qs.filter(identified_at__range=[day, day_end]).count()
        daily_data.append({
            'date': day.strftime('%Y-%m-%d'),
            'identifications': day_count
        })
    
    # User activity
    top_users = list(
        photos_qs.values('user__username', 'user__email')
        .annotate(count=Count('id'))
        .order_by('-count')[:10]
    )
    
    # Recent photos
    recent_photos = list(
        photos_qs.order_by("-identified_at")[:20].values(
            "id", "image_url", "scientific_name", "common_name", 
            "confidence", "identified_at", "user__username"
        )
    )
    
    # Build report data
    report_data = {
        "metadata": {
            "report_period": f"{start_date.strftime('%b %d, %Y')} - {end_date.strftime('%b %d, %Y')}",
            "generated": end_date.strftime("%b %d, %Y %H:%M"),
            "period_days": days,
            "report_type": report_type
        },
        "summary": {
            "total_identifications": total_photos,
            "active_users": active_users,
            "plant_species_identified": plant_species_identified,
            "success_rate": success_rate,
            "average_confidence": round(avg_confidence * 100, 2) if avg_confidence else 0
        },
        "confidence_breakdown": {
            "high": high_conf,
            "medium": medium_conf,
            "low": low_conf
        },
        "top_species": top_species,
        "daily_trend": daily_data,
        "top_users": top_users,
        "recent_identifications": recent_photos
    }
    
    # Export CSV if requested
    if export_format == "csv":
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        
        # Summary section
        writer.writerow(["Plant Identification Report"])
        writer.writerow(["Period:", report_data['metadata']['report_period']])
        writer.writerow(["Generated:", report_data['metadata']['generated']])
        writer.writerow([])
        
        writer.writerow(["Summary Metrics"])
        writer.writerow(["Metric", "Value"])
        writer.writerow(["Total Identifications", total_photos])
        writer.writerow(["Active Users", active_users])
        writer.writerow(["Plant Species Identified", plant_species_identified])
        writer.writerow(["Success Rate (%)", success_rate])
        writer.writerow(["Average Confidence (%)", report_data['summary']['average_confidence']])
        writer.writerow([])
        
        writer.writerow(["Confidence Breakdown"])
        writer.writerow(["Level", "Count"])
        writer.writerow(["High (≥80%)", high_conf])
        writer.writerow(["Medium (50–79%)", medium_conf])
        writer.writerow(["Low (<50%)", low_conf])
        writer.writerow([])
        
        writer.writerow(["Top Species Identified"])
        writer.writerow(["Scientific Name", "Common Name", "Count"])
        for species in top_species:
            writer.writerow([
                species.get('scientific_name', 'N/A'),
                species.get('common_name', 'N/A'),
                species['count']
            ])
        
        response = HttpResponse(buffer.getvalue(), content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="plant_report_{end_date.strftime("%Y%m%d")}.csv"'
        return response
    
    # Return JSON by default
    return JsonResponse(report_data, safe=False)
