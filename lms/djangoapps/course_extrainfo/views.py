from django.shortcuts import render
from .models import course_extrainfo
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count

# Create your views here.
def course_ctype(speczId):
    from django.core.exceptions import ObjectDoesNotExist

    speczname = ""
    ctype = ""
    try:
        getDetails = course_extrainfo.objects.get(course_id=speczId)
        speczname = getDetails.course_type
    except ObjectDoesNotExist:
        getDetails = None

    if speczname == "1":
        ctype = "course"
    else:
        ctype = "courseware"
    return ctype


def course_ctype_number(speczId):
    from django.core.exceptions import ObjectDoesNotExist

    speczname = ""
    ctype = ""
    try:
        getDetails = course_extrainfo.objects.get(course_id=speczId)
        speczname = getDetails.course_type
    except ObjectDoesNotExist:
        getDetails = None
    return speczname


def category_courses_count(category_id):
    getDetails = (
        course_extrainfo.objects.filter(category=category_id, course_type=1)
        .values("category")
        .annotate(ccount=Count("category"))
    )
    return getDetails


def category_lectures_count(category_id):
    getDetails = (
        course_extrainfo.objects.filter(category=category_id, course_type=2)
        .values("category")
        .annotate(ccount=Count("category"))
    )
    return getDetails


def category_casestudies_count(category_id):
    getDetails = (
        course_extrainfo.objects.filter(category=category_id, course_type=3)
        .values("category")
        .annotate(ccount=Count("category"))
    )
    return getDetails


def course_new_url(courseid):
    try:
        geturl = course_extrainfo.objects.get(course_id=courseid)
        url = geturl.course_seo_url
    except ObjectDoesNotExist:
        url = None
    return url
