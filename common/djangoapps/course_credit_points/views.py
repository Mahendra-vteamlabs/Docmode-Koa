from __future__ import unicode_literals
from django.http import JsonResponse
from django.shortcuts import render
from edxmako.shortcuts import render_to_response
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.csrf import csrf_exempt

from django import forms
from lms.djangoapps.reg_form.models import medical_councils
from lms.djangoapps.course_extrainfo.models import course_extrainfo


def get_credit_points(request, course_key_string):
    data = {}
    context = {}
    try:
        course_extra_info, created = course_extrainfo.objects.get_or_create(
            course_id=course_key_string
        )
        if request.method == "GET":
            if created:
                medical_councils_list = medical_councils.objects.all()
                context["credit_point"] = ""
                context["credit_code"] = ""
                context["council_name"] = ""
                context["course_id"] = course_key_string
                context["medical_councils_list"] = medical_councils_list
                return render_to_response("course_credit_content.html", context)
            else:
                medical_councils_list = medical_councils.objects.all()
                context["credit_point"] = course_extra_info.credit_point
                context["credit_code"] = course_extra_info.credit_code
                context["council_name"] = course_extra_info.credit_given_by
                context["course_id"] = course_key_string
                context["medical_councils_list"] = medical_councils_list
                return render_to_response("course_credit_content.html", context)
        if request.method == "POST":
            credit_point = request.POST.get("dsh_credit_point")
            credit_code = request.POST.get("dsh_credit_code")
            credit_given_by = request.POST.get("dsh_credit_given")
            course_extra_info.credit_point = credit_point
            course_extra_info.credit_code = credit_code
            course_extra_info.credit_given_by = credit_given_by
            course_extra_info.save()
            data["errormessage"] = "course extra info record not exist with course"
            return JsonResponse(status=201, data={"success": "new", "data": data})
    except:
        # return render_to_response('course_credit_content.html', context=context)
        data["errormessage"] = "course extra info record not exist with course"
        return JsonResponse(data={"success": "false", "data": data}, status=200)
