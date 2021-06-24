import datetime
import logging
from celery.task import task
from django.conf import settings
from django.shortcuts import redirect
from django.contrib.auth.models import User
from django.urls import NoReverseMatch, reverse
from django.views.decorators.csrf import csrf_exempt
from django.http import (
    Http404,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseForbidden,
)
from edxmako.shortcuts import render_to_response
from rest_framework.views import APIView
from django.http import JsonResponse
from lms.djangoapps.course_extrainfo.models import course_extrainfo
from openedx.core.lib.api.permissions import ApiKeyHeaderPermissionIsAuthenticated
from openedx.core.lib.api.view_utils import DeveloperErrorViewMixin, view_auth_classes
from openedx.core.djangoapps.custom_programs.models import (
    CustomCourseOverview,
    ProgramAdd,
    ProgramEnrollment,
    ProgramOrder,
    ProgramCoupon,
    CouponRadeemedDetails,
    ProgramCouponRemainUsage,
)
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.custom_programs.tasks import program_course_enrollment
from student.models import CourseEnrollment

log = logging.getLogger("edx.courseware")


def get_program_details(request, program_id):
    from openedx.core.djangoapps.custom_programs.models import (
        CustomCourseOverview,
        ProgramAdd,
    )

    program_obj = ProgramAdd.objects.get(id=program_id)
    context = {
        "id": program_obj.id,
        "name": program_obj.name,
        "price": program_obj.price,
    }
    return render_to_response("program_details.html", context)


@view_auth_classes(is_authenticated=False)
class ProgramCuponCheck(DeveloperErrorViewMixin, APIView):
    @csrf_exempt
    def post(self, request, **kwargs):
        today_date = datetime.datetime.now()
        data = {}
        if "coupon_code" and "program_id" and "order_id" in request.POST:
            coupon_code = request.POST.get("coupon_code")
            program_id = request.POST.get("program_id")
            order_id = request.POST.get("order_id")
            if not coupon_code:
                data["errormessage"] = "coupon code can not be blank"
                return JsonResponse(data={"status": "false", "data": data}, status=200)
            if not program_id:
                data["errormessage"] = "something wrong in cart"
                return JsonResponse(data={"status": "false", "data": data}, status=200)
            if not order_id:
                data["errormessage"] = "something wrong in cart"
                return JsonResponse(data={"status": "false", "data": data}, status=200)

            coupon_obj = ProgramCoupon.objects.filter(
                program__id=program_id, coupon_code=coupon_code
            )
            if coupon_obj:
                coupon_obj = coupon_obj[0]
                if not ProgramCoupon.objects.filter(
                    program__id=program_id,
                    activation_date__lte=today_date,
                    coupon_code=coupon_code,
                ):
                    data["errormessage"] = "Copon code activation date not started"
                    return JsonResponse(
                        data={"status": "false", "data": data}, status=200
                    )
                if not ProgramCoupon.objects.filter(
                    program__id=program_id,
                    expiration_date__gte=today_date,
                    coupon_code=coupon_code,
                ):
                    data["errormessage"] = "Copon code expired"
                    return JsonResponse(
                        data={"status": "false", "data": data}, status=200
                    )
                if not coupon_obj.is_active:
                    data["errormessage"] = "Copon code not active"
                    return JsonResponse(
                        data={"status": "false", "data": data}, status=200
                    )
                coupon_remain_obj = ProgramCouponRemainUsage.objects.filter(
                    program_coupon=coupon_obj
                )
                if coupon_remain_obj:
                    coupon_remain_obj = coupon_remain_obj[0]
                    if not coupon_remain_obj.remaining_usage > 0:
                        data[
                            "errormessage"
                        ] = "Copon code not have remain number of usage "
                        return JsonResponse(
                            data={"status": "false", "data": data}, status=200
                        )
                else:
                    data["errormessage"] = "Copon code not have remain number of usage "
                    return JsonResponse(
                        data={"status": "false", "data": data}, status=200
                    )

                discount_price = (
                    (
                        coupon_obj.program.price
                        - (
                            (coupon_obj.program.price * coupon_obj.discout_percentage)
                            / 100
                        )
                    )
                    * 70
                    * 100
                )
                data["successmessage"] = "Coupon apply Successfully"
                data["latest_price"] = discount_price
                data["discount_price"] = (
                    ((coupon_obj.program.price * coupon_obj.discout_percentage) / 100)
                    * 70
                    * 100
                )
                programorder = ProgramOrder.objects.get(id=order_id)
                (
                    coupon_radeemed_obj,
                    created,
                ) = CouponRadeemedDetails.objects.get_or_create(
                    order=programorder,
                    program=coupon_obj.program,
                    coupon=coupon_obj,
                    user=request.user,
                )
                if coupon_radeemed_obj:
                    if not created and coupon_radeemed_obj.status == "redeemed":
                        data[
                            "errormessage"
                        ] = "alreay exist a order with applied this code"
                        return JsonResponse(
                            data={"status": "false", "data": data}, status=200
                        )
                    coupon_radeemed_obj.status = "applied"
                    coupon_radeemed_obj.save()
                    data["successmessage"] = "Coupon Successfuly applied"
                    return JsonResponse(
                        data={"status": "success", "data": data}, status=200
                    )

                    # return redirect(reverse("custom_cart"))
                # coupon_radeemed_obj,created = CouponRadeemedDetails.objects.get_or_create(order=programorder,program__id=program_id,coupon__coupon_code=coupon_code,user=request.user)
                # context = {}
                # context['successmessage'] = "Coupon apply Successfully"
                # context['latest_price'] = discount_price
                # context['discount_price'] = ((coupon_obj.program.price*coupon_obj.discout_percentage)/100)*70*100
                # context['program'] = coupon_obj.program
                # programorder = ProgramOrder.objects.get(id=order_id)
                # context['programorder'] = programorder
                # return render_to_response("programs/cart.html",context)
                # request.session['latest_price'] = discount_price
                # request.session['discount_price'] = ((coupon_obj.program.price*coupon_obj.discout_percentage)/100)*70*100
                else:
                    data["errormessage"] = "Coupon code not valid"
                    return JsonResponse(
                        data={"status": "false", "data": data}, status=200
                    )
            else:
                data["errormessage"] = "Coupon code not valid"
                return JsonResponse(data={"status": "false", "data": data}, status=200)
        else:
            data["errormessage"] = "required fielsd missing"
            return JsonResponse(data={"status": "false", "data": data}, status=200)


@view_auth_classes(is_authenticated=False)
class ProgramCustomList(DeveloperErrorViewMixin, APIView):
    def get(self, request, **kwargs):
        context = {}
        programs_list = ProgramAdd.objects.all()
        program_details_list = []
        context["total_programs"] = len(programs_list)
        for program in programs_list:
            program_details_dict = {}
            program_details_dict["id"] = program.id
            program_details_dict["name"] = program.name
            program_details_dict["program_image"] = program.program_image.url
            program_details_dict["price"] = program.price
            program_details_dict["currency"] = program.currency
            program_details_dict["start_date"] = program.start_date.strftime(
                "%Y-%m-%dT%H:%M:%S.%fZ"
            )
            program_details_dict["end_date"] = program.end_date.strftime(
                "%Y-%m-%dT%H:%M:%S.%fZ"
            )
            program_details_dict[
                "enrollment_start_date"
            ] = program.enrollment_start_date.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            program_details_dict[
                "enrollment_end_date"
            ] = program.enrollment_end_date.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            program_details_dict["short_description"] = program.short_description
            program_details_dict["total_courses"] = program.courses.count()
            program_details_list.append(program_details_dict)
        context["programs"] = program_details_list
        response = JsonResponse(context, status=200)
        return response


@view_auth_classes(is_authenticated=False)
class ProgramCustomDetail(DeveloperErrorViewMixin, APIView):
    def get(self, request, **kwargs):
        context = {}
        program_id = request.GET.get("program_id")
        user_id = request.GET.get("user_id")
        if not program_id:
            context["developer_message"] = "Any Program not found"
            response = JsonResponse(context, status=200)
        program = ProgramAdd.objects.get(id=program_id)
        context["is_enrolled"] = False
        if user_id and program_id:
            user = User.objects.get(id=user_id)
            program_enroll = ProgramEnrollment.objects.filter(
                user=user, program=program
            )
            if program_enroll:
                context["is_enrolled"] = True
        context["id"] = program.id
        context["name"] = program.name
        context["program_image"] = program.program_image.url
        context["price"] = program.price
        context["currency"] = program.currency
        context["start_date"] = program.start_date.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        context["end_date"] = program.end_date.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        context["enrollment_start_date"] = program.enrollment_start_date.strftime(
            "%Y-%m-%dT%H:%M:%S.%fZ"
        )
        context["enrollment_end_date"] = program.enrollment_end_date.strftime(
            "%Y-%m-%dT%H:%M:%S.%fZ"
        )
        context["short_description"] = program.short_description
        context["efforts"] = program.efforts
        context["redirect_url"] = settings.LMS_ROOT_URL + "/cart"
        course_list = program.courses.values()
        course_details_list = []
        for course in course_list:
            course_details_dict = {}
            course_overview = CourseOverview.objects.get(id=course["course_id"])
            course_extra_info = course_extrainfo.objects.get(
                course_id=course["course_id"]
            )
            course_details_dict["id"] = str(course_overview.id)
            course_details_dict["name"] = course_overview.display_name_with_default
            course_details_dict["short_description"] = course_overview.short_description
            course_details_dict["image"] = course_overview.course_image_url
            course_details_dict["wp_url"] = course_extra_info.course_seo_url
            course_details_list.append(course_details_dict)
        context["courses_details"] = course_details_list
        response = JsonResponse(context, status=200)
        return response


# def Custom_program_payment(self, request):


@view_auth_classes(is_authenticated=False)
class Custom_program_payment(DeveloperErrorViewMixin, APIView):
    def get(self, request, **kwargs):
        context = {}
        program_id = request.GET.get("program_id")
        user = request.user
        order_id = request.GET.get("order_id")
        payer_id = request.GET.get("razorpay_payment_id")

        if "developer_message" in request.session:
            del request.session["developer_message"]
        if order_id:
            order_length = len(str(order_id))
            if order_length == 1:
                payment_id = "DOCMODE-" + str(10000) + str(order_id)
            elif order_length == 2:
                payment_id = "DOCMODE-" + str(1000) + str(order_id)
            elif order_length == 3:
                payment_id = "DOCMODE-" + str(100) + str(order_id)
            elif order_length == 4:
                payment_id = "DOCMODE-" + str(10) + str(order_id)
            elif order_length == 5:
                payment_id = "DOCMODE-" + str(1) + str(order_id)
            else:
                payment_id = "DOCMODE" + str(order_id)
            order_obj = ProgramOrder.objects.get(id=order_id)
            order_obj.payment_id = payment_id
            if "order_price" in request.GET:
                order_obj.price = request.GET.get("order_price")
                order_obj.discount_price = request.GET.get("coupon_value")
            order_obj.payment_reference = payer_id
            order_obj.status = "paid"
            order_obj.save()
        else:
            request.session["developer_message"] = "Order Not Found"
            return redirect(reverse("order_receipt"))
        if not program_id:
            request.session["developer_message"] = "Any program not found"
            return redirect(reverse("order_receipt"))
        program = ProgramAdd.objects.get(id=program_id)
        course_list = program.courses.values()
        course_list_task = []
        for course in course_list:
            course_list_task.append(str(course["course_id"]))
        program_course_enrollment.delay(course_list=course_list_task, user_id=user.id)
        # for course in course_list:
        #     log.info("courses for loop start")
        #     if not CourseEnrollment.is_enrolled(user, course["course_id"]) :
        #         log.info("course enrollment function will be call")
        #         CourseEnrollment.enroll(user=user, course_key=course["course_id"])
        program_obj, created = ProgramEnrollment.objects.get_or_create(
            user=user, program=program
        )
        if not created:
            request.session["developer_message"] = "Already Enrolled"
            return redirect(reverse("order_receipt"))
            # return render_to_response("programs/receipt.html",context)
        if "order_id" in request.session:
            del request.session["order_id"]
        request.session["order_id"] = order_id

        if "coupon_name" in request.GET:
            coupon_name = request.GET.get("coupon_name")
            coupon_details = ProgramCoupon.objects.get(
                coupon_code=coupon_name, program=program
            )

            program_coupon_remainusage = ProgramCouponRemainUsage.objects.get(
                program_coupon__coupon_code=coupon_name
            )
            if program_coupon_remainusage.remaining_usage > 0:
                program_coupon_remainusage.remaining_usage = (
                    program_coupon_remainusage.remaining_usage - 1
                )
                program_coupon_remainusage.save()
                coupon_reedem_update = CouponRadeemedDetails.objects.get(
                    order=order_obj, coupon=coupon_details, user=user, status="applied"
                )
                coupon_reedem_update.status = "redeemed"
                coupon_reedem_update.save()
            else:
                coupon_reedem_update = CouponRadeemedDetails.objects.get(
                    order=order_obj, coupon=coupon_details, user=user, status="applied"
                )
                coupon_reedem_update.status = "failed"
                coupon_reedem_update.save()
                order_obj.status = "refund"
                order_obj.save()

        log.info("program sessions ---> %s", request.session["order_id"])
        return redirect(reverse("order_receipt"))
        # return render_to_response("programs/receipt.html",context)


@view_auth_classes(is_authenticated=False)
class ProgramCuponRemove(DeveloperErrorViewMixin, APIView):
    def post(self, request, **kwargs):
        today_date = datetime.datetime.now()
        data = {}
        if "coupon_code" and "program_id" and "order_id" in request.POST:
            coupon_code = request.POST.get("coupon_code")
            program_id = request.POST.get("program_id")
            order_id = request.POST.get("order_id")
            if not coupon_code:
                data["errormessage"] = "coupon code can not be blank"
                return JsonResponse(data={"status": "false", "data": data}, status=200)
            if not program_id:
                data["errormessage"] = "something wrong in cart"
                return JsonResponse(data={"status": "false", "data": data}, status=200)
            if not order_id:
                data["errormessage"] = "something wrong in cart"
                return JsonResponse(data={"status": "false", "data": data}, status=200)

            coupon_obj = ProgramCoupon.objects.filter(
                program__id=program_id, coupon_code=coupon_code
            )
            if coupon_obj:
                coupon_obj = coupon_obj[0]
                programorder = ProgramOrder.objects.get(id=order_id)
                coupon_radeemed_obj = CouponRadeemedDetails.objects.get(
                    order=programorder,
                    program=coupon_obj.program,
                    coupon=coupon_obj,
                    user=request.user,
                )
                if coupon_radeemed_obj:
                    coupon_radeemed_obj.status = "initial"
                    coupon_radeemed_obj.save()
                    data["successmessage"] = "Coupon Successfuly applied"
                    return JsonResponse(
                        data={"status": "success", "data": data}, status=200
                    )
                else:
                    data["errormessage"] = "Coupon code not valid"
                    return JsonResponse(
                        data={"status": "false", "data": data}, status=200
                    )
            else:
                data["errormessage"] = "Coupon code not valid"
                return JsonResponse(data={"status": "false", "data": data}, status=200)
        else:
            data["errormessage"] = "required field missing"
            return JsonResponse(data={"status": "false", "data": data}, status=200)
