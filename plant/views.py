from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.utils.decorators import method_decorator
from django.views import View
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from .models import PlantSpecies, PlantIdentification, UserPlantCollection
from django.db import models
from django.conf import settings
import json
import os
from datetime import datetime, timedelta
from django.utils import timezone
import random
from django.db.models import Count, Q, Avg
from .models import Plant, FlaggedCase

@csrf_exempt
@require_http_methods(["GET"])
def get_analytics(request):
    """
    Main analytics endpoint returning complete analytics data
    Query params: time_range (today/week/month), search
    """
    time_range = request.GET.get('time_range', 'week')
    search = request.GET.get('search', '')

    now = timezone.now()
    if time_range == 'today':
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif time_range == 'month':
        start_date = now - timedelta(days=30)
    else:  # week
        start_date = now - timedelta(days=7)

    identifications = PlantIdentification.objects.filter(
    created_at__gte=start_date
    ).values('created_at__date').annotate(
        identifications=Count('id'),
        uniqueUsers=Count('user_id', distinct=True)
    ).order_by('created_at__date')

    time_series = [
        {
            'date': item['created_at__date'].strftime('%Y-%m-%d'),
            'identifications': item['identifications'],
            'uniqueUsers': item['uniqueUsers']
        }
        for item in identifications
    ]

    # Top searched plants based on PlantIdentification
    top_plants = PlantIdentification.objects.filter(
        created_at__gte=start_date
    ).values('predicted_name').annotate(
        searchCount=Count('predicted_name'),
        successRate=Avg('confidence_score')
    ).order_by('-searchCount')[:10]

    top_searched = [
        {
            'id': str(hash(plant['predicted_name'])),
            'name': plant['predicted_name'],
            'scientificName': plant['predicted_name'],
            'searchCount': plant['searchCount'],
            'successRate': round(plant['successRate'], 1) if plant['successRate'] else 0,
            'thumbnail': '/placeholder.svg?height=50&width=50'
        }
        for plant in top_plants
    ]

    if search:
        top_searched = [
            plant for plant in top_searched
            if search.lower() in plant['name'].lower() or 
               search.lower() in plant['scientificName'].lower()
        ]

    flagged = FlaggedCase.objects.filter(is_resolved=False)[:20]

    flagged_cases = [
        {
            'id': str(case.id),
            'plantName': case.plant_name,
            'imageUrl': case.image_url,
            'reason': case.get_reason_display(),
            'confidence': case.confidence,
            'submittedBy': case.submitted_by,
            'submittedAt': case.submitted_at.isoformat()
        }
        for case in flagged
    ]

    total_identifications = PlantIdentification.objects.filter(
    created_at__gte=start_date
    ).count()

    total_unique_users = PlantIdentification.objects.filter(
    created_at__gte=start_date
    ).values('user_id').distinct().count()

    average_success_rate = PlantIdentification.objects.filter(
    created_at__gte=start_date,
        is_correct=True
    ).aggregate(avg=Avg('confidence_score'))['avg'] or 0

    return JsonResponse({
        'timeSeries': time_series,
        'topSearched': top_searched,
        'flaggedCases': flagged_cases,
        'totalIdentifications': total_identifications,
        'totalUniqueUsers': total_unique_users,
        'averageSuccessRate': round(average_success_rate, 1)
    })


@csrf_exempt
@require_http_methods(["GET"])
def get_time_series(request):
    """Get time series data only"""
    time_range = request.GET.get('time_range', 'week')

    now = timezone.now()
    if time_range == 'today':
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif time_range == 'month':
        start_date = now - timedelta(days=30)
    else:
        start_date = now - timedelta(days=7)

    identifications = PlantIdentification.objects.filter(
    created_at__gte=start_date
    ).values('created_at__date').annotate(
        identifications=Count('id'),
        uniqueUsers=Count('user_id', distinct=True)
    ).order_by('created_at__date')

    time_series = [
        {
            'date': item['created_at__date'].strftime('%Y-%m-%d'),
            'identifications': item['identifications'],
            'uniqueUsers': item['uniqueUsers']
        }
        for item in identifications
    ]

    return JsonResponse({'timeSeries': time_series})


@csrf_exempt
@require_http_methods(["GET"])
def get_top_searched(request):
    """Get top searched plants"""
    search = request.GET.get('search', '')
    time_range = request.GET.get('time_range', 'week')

    now = timezone.now()
    if time_range == 'today':
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif time_range == 'month':
        start_date = now - timedelta(days=30)
    else:
        start_date = now - timedelta(days=7)

    identifications = PlantIdentification.objects.filter(
        created_at__gte=start_date
    )
    if search:
        identifications = identifications.filter(
            Q(predicted_name__icontains=search)
        )

    top_plants = identifications.values('predicted_name').annotate(
        searchCount=Count('predicted_name'),
        successRate=Avg('confidence_score')
    ).order_by('-searchCount')[:10]

    top_searched = [
        {
            'id': str(hash(plant['predicted_name'])),
            'name': plant['predicted_name'],
            'scientificName': plant['predicted_name'],
            'searchCount': plant['searchCount'],
            'successRate': round(plant['successRate'], 1) if plant['successRate'] else 0,
            'thumbnail': '/placeholder.svg?height=50&width=50'
        }
        for plant in top_plants
    ]

    return JsonResponse({'topSearched': top_searched})


@csrf_exempt
@require_http_methods(["GET"])
def get_flagged_cases(request):
    """Get flagged cases requiring review"""
    flagged = FlaggedCase.objects.filter(is_resolved=False).order_by('-submitted_at')[:20]

    flagged_cases = [
        {
            'id': str(case.id),
            'plantName': case.plant_name,
            'imageUrl': case.image_url,
            'reason': case.get_reason_display(),
            'confidence': case.confidence,
            'submittedBy': case.submitted_by,
            'submittedAt': case.submitted_at.isoformat()
        }
        for case in flagged
    ]

    return JsonResponse({'flaggedCases': flagged_cases})


@csrf_exempt
@require_http_methods(["GET"])
def get_summary(request):
    """Get summary statistics only"""
    time_range = request.GET.get('time_range', 'week')

    now = timezone.now()
    if time_range == 'today':
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif time_range == 'month':
        start_date = now - timedelta(days=30)
    else:
        start_date = now - timedelta(days=7)

    total_identifications = PlantIdentification.objects.filter(
    created_at__gte=start_date
    ).count()

    total_unique_users = PlantIdentification.objects.filter(
    created_at__gte=start_date
    ).values('user_id').distinct().count()

    average_success_rate = PlantIdentification.objects.filter(
    created_at__gte=start_date,
        is_correct=True
    ).aggregate(avg=Avg('confidence_score'))['avg'] or 0

    return JsonResponse({
        'totalIdentifications': total_identifications,
        'totalUniqueUsers': total_unique_users,
        'averageSuccessRate': round(average_success_rate, 1)
    })


# Plant CRUD operations
@csrf_exempt
@require_http_methods(["GET", "POST"])
def plant_list_create(request):
    """List all plants or create a new plant"""
    if request.method == "GET":
        search = request.GET.get('search', '')
        tag = request.GET.get('tag', '')
        sort = request.GET.get('sort', 'name')

        plants_query = Plant.objects.all()

        if search:
            plants_query = plants_query.filter(
                Q(name__icontains=search) | Q(scientific_name__icontains=search)
            )

        if tag:
            plants_query = plants_query.filter(tags__contains=[tag])

        # Sort
        if sort == 'name':
            plants_query = plants_query.order_by('name')
        elif sort == 'date':
            plants_query = plants_query.order_by('-date_added')

        plants = [
            {
                'id': str(plant.id),
                'name': plant.name,
                'scientificName': plant.scientific_name,
                'description': plant.description,
                'thumbnail': plant.thumbnail or '/placeholder.svg?height=100&width=100',
                'tags': plant.tags,
                'dateAdded': plant.date_added.strftime('%Y-%m-%d')
            }
            for plant in plants_query
        ]

        return JsonResponse({'plants': plants})

    elif request.method == "POST":
        try:
            data = json.loads(request.body)

            plant = Plant.objects.create(
                name=data.get('name'),
                scientific_name=data.get('scientificName', ''),
                description=data.get('description', ''),
                thumbnail=data.get('thumbnail', ''),
                tags=data.get('tags', [])
            )

            return JsonResponse({
                'id': str(plant.id),
                'name': plant.name,
                'scientificName': plant.scientific_name,
                'description': plant.description,
                'thumbnail': plant.thumbnail,
                'tags': plant.tags,
                'dateAdded': plant.date_added.strftime('%Y-%m-%d')
            }, status=201)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["GET", "PUT", "DELETE"])
def plant_detail(request, plant_id):
    """Retrieve, update or delete a plant"""
    try:
        plant = Plant.objects.get(id=plant_id)
    except Plant.DoesNotExist:
        return JsonResponse({'error': 'Plant not found'}, status=404)

    if request.method == "GET":
        return JsonResponse({
            'id': str(plant.id),
            'name': plant.name,
            'scientificName': plant.scientific_name,
            'description': plant.description,
            'thumbnail': plant.thumbnail,
            'tags': plant.tags,
            'dateAdded': plant.date_added.strftime('%Y-%m-%d')
        })

    elif request.method == "PUT":
        try:
            data = json.loads(request.body)

            plant.name = data.get('name', plant.name)
            plant.scientific_name = data.get('scientificName', plant.scientific_name)
            plant.description = data.get('description', plant.description)
            plant.thumbnail = data.get('thumbnail', plant.thumbnail)
            plant.tags = data.get('tags', plant.tags)
            plant.save()

            return JsonResponse({
                'id': str(plant.id),
                'name': plant.name,
                'scientificName': plant.scientific_name,
                'description': plant.description,
                'thumbnail': plant.thumbnail,
                'tags': plant.tags,
                'dateAdded': plant.date_added.strftime('%Y-%m-%d')
            })
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    elif request.method == "DELETE":
        plant.delete()
        return JsonResponse({'message': 'Plant deleted successfully'}, status=200)


@csrf_exempt
@require_http_methods(["GET"])
def get_available_tags(request):
    """Get all unique tags from all plants"""
    plants = Plant.objects.all()

    all_tags = set()
    for plant in plants:
        all_tags.update(plant.tags)

    sorted_tags = sorted(list(all_tags))

    return JsonResponse({'tags': sorted_tags})