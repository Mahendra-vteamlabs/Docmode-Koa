# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
import boto
import boto.s3
import sys
from boto.s3.key import Key
import boto.s3.connection
import sys
from datetime import date
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import (
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseForbidden,
    HttpResponseRedirect,
)
from django.template.context_processors import csrf
from django.views.decorators.csrf import ensure_csrf_cookie
from lms.djangoapps.userprofile_extrainfo.models import (
    education,
    awards,
    research_papers,
    media_featured,
    clinic_hospital_address,
    experience,
)
from lms.djangoapps.userprofile_extrainfo.forms import education_form, award_form
from edxmako.shortcuts import render_to_response
from django.core.files.storage import FileSystemStorage
from django.core.exceptions import ObjectDoesNotExist

AUDIT_LOG = logging.getLogger("audit")
log = logging.getLogger(__name__)

AWS_ACCESS_KEY_ID = settings.AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY = settings.AWS_SECRET_ACCESS_KEY
BUCKET_NAME = settings.AWS_STORAGE_BUCKET_NAME


@login_required
@ensure_csrf_cookie
def education_add(request):
    usr = request.user.id
    username = request.user.username
    if request.method == "POST":
        if "edu_add" in request.POST:
            year = request.POST.get("year", "")
            description = request.POST.get("description", "")
            institution_name = request.POST.get("institution_name", "")

            bucket_name = BUCKET_NAME + "/" + username + "-one/"
            conn = boto.connect_s3(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)

            # bucket = conn.create_bucket(bucket_name,location=boto.s3.connection.Location.DEFAULT)
            bucket = conn.get_bucket(BUCKET_NAME)
            # bucket = BUCKET_NAME
            imagedate = date.today()
            imagedate = imagedate.strftime("%d_%m_%Y")
            # testfile = upload_file.name
            if request.FILES:
                for myfile in request.FILES.getlist("certificate_path"):
                    fs = FileSystemStorage()
                    filename = fs.save(myfile.name, myfile)
                    uploaded_file_url = fs.url(filename)
                    # log.info('myfile %s', filename)

                    k = Key(bucket)
                    k.key = username + "/education/" + imagedate + "_" + myfile.name
                    k.set_contents_from_filename(
                        settings.MEDIA_ROOT + "/" + myfile.name
                    )
                    k.make_public()
                    imageurl = (
                        "https://s3-ap-southeast-1.amazonaws.com/docmode-org-uploads/"
                        + username
                        + "/education/"
                        + imagedate
                        + "_"
                        + myfile.name
                    )
                    # log.info('imageurl %s', imageurl)
                education_new = education(
                    user=usr,
                    year=year,
                    description=description,
                    institution_name=institution_name,
                    certificate_path=imageurl,
                )
            else:
                education_new = education(
                    user=usr,
                    year=year,
                    description=description,
                    institution_name=institution_name,
                )
            education_new.save()

            msg = "Education details added successfully."
            context = {"errors": msg}
            return HttpResponseRedirect("/u/" + username)
        elif "edu_edit" in request.POST:
            year = request.POST.get("year", "")
            description = request.POST.get("description", "")
            institution_name = request.POST.get("institution_name", "")
            eduid = request.POST.get("edu_edit_number", "")
            bucket_name = BUCKET_NAME + "/" + username + "-one/"

            conn = boto.connect_s3(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)

            # bucket = conn.create_bucket(bucket_name,location=boto.s3.connection.Location.DEFAULT)
            bucket = conn.get_bucket(BUCKET_NAME)
            # bucket = BUCKET_NAME
            imagedate = date.today()
            imagedate = imagedate.strftime("%d_%m_%Y")
            # testfile = upload_file.name

            if request.FILES:
                edu_img = education.objects.get(user=usr, id=eduid)
                img_path = edu_img.certificate_path.split("education")
                splitted_img_path = img_path[1].split("/")
                # log.info('myaddedfile %s', splitted_img_path[1])

                b = Key(bucket)
                b.key = username + "/education/" + splitted_img_path[1]
                bucket.delete_key(b)

                for myfile in request.FILES.getlist("certificate_path"):
                    fs = FileSystemStorage()
                    filename = fs.save(myfile.name, myfile)
                    uploaded_file_url = fs.url(filename)

                    k = Key(bucket)
                    k.key = username + "/education/" + imagedate + "_" + myfile.name
                    k.set_contents_from_filename(
                        settings.MEDIA_ROOT + "/" + myfile.name
                    )
                    k.make_public()
                    imageurl = (
                        "https://s3-ap-southeast-1.amazonaws.com/docmode-org-uploads/"
                        + username
                        + "/education/"
                        + imagedate
                        + "_"
                        + myfile.name
                    )
                    # log.info('editedimageurl %s', imageurl)
                education_new = education.objects.filter(user=usr, id=eduid).update(
                    year=year,
                    description=description,
                    institution_name=institution_name,
                    certificate_path=imageurl,
                )
            else:
                education_new = education.objects.filter(user=usr, id=eduid).update(
                    year=year,
                    description=description,
                    institution_name=institution_name,
                )
            msg = "Education details edited successfully."
            context = {"errors": msg}
            return HttpResponseRedirect("/u/" + username)
        else:
            eduid = request.POST.get("edu_number", "")
            conn = boto.connect_s3(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)

            # bucket = conn.create_bucket(bucket_name,location=boto.s3.connection.Location.DEFAULT)
            bucket = conn.get_bucket(BUCKET_NAME)
            # bucket = BUCKET_NAME
            imagedate = date.today()
            imagedate = imagedate.strftime("%d_%m_%Y")
            # testfile = upload_file.name

            edu_img = education.objects.get(user=usr, id=eduid)
            if edu_img.certificate_path:
                img_path = edu_img.certificate_path.split("education")
                splitted_img_path = img_path[1].split("/")
                # log.info('myaddedfile %s', splitted_img_path[1])

                b = Key(bucket)
                b.key = username + "/education/" + splitted_img_path[1]
                bucket.delete_key(b)
            education_new = education.objects.filter(user=usr, id=eduid).delete()
            msg = "Education deleted successfully."
            context = {"errors": msg}
            return HttpResponseRedirect("/u/" + username)
    else:
        msg = "Education details could not be added/edited"
        context = {
            "errors": msg,
        }
        render_to_response("learner_profile/learner_profile.html", context)


@login_required
@ensure_csrf_cookie
def award_add(request):
    usr = request.user.id
    username = request.user.username
    if request.method == "POST":
        if "award_add" in request.POST:
            year = request.POST.get("award_year", "")
            title = request.POST.get("award_title", "")

            bucket_name = BUCKET_NAME + "/" + username + "-one/"
            conn = boto.connect_s3(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)

            # bucket = conn.create_bucket(bucket_name,location=boto.s3.connection.Location.DEFAULT)
            bucket = conn.get_bucket(BUCKET_NAME)
            # bucket = BUCKET_NAME
            imagedate = date.today()
            imagedate = imagedate.strftime("%d_%m_%Y")
            # testfile = upload_file.name
            if request.FILES:
                for myfile in request.FILES.getlist("award_path"):
                    fs = FileSystemStorage()
                    filename = fs.save(myfile.name, myfile)
                    uploaded_file_url = fs.url(filename)
                    # log.info('myfile %s', filename)

                    k = Key(bucket)
                    k.key = username + "/award/" + imagedate + "_" + myfile.name
                    k.set_contents_from_filename(
                        settings.MEDIA_ROOT + "/" + myfile.name
                    )
                    k.make_public()
                    imageurl = (
                        "https://s3-ap-southeast-1.amazonaws.com/docmode-org-uploads/"
                        + username
                        + "/award/"
                        + imagedate
                        + "_"
                        + myfile.name
                    )
                    # log.info('imageurl %s', imageurl)
            else:
                imageurl = "not uploaded"
            award_new = awards(
                user=usr, year=year, title=title, award_image_path=imageurl
            )
            award_new.save()

            msg = "Award details added successfully."
            context = {"errors": msg}
            return HttpResponseRedirect("/u/" + username)
        elif "award_edit" in request.POST:
            year = request.POST.get("edit_award_year", "")
            title = request.POST.get("edit_award_title", "")
            awardid = request.POST.get("award_edit_number", "")
            bucket_name = BUCKET_NAME + "/" + username + "-one/"

            conn = boto.connect_s3(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)

            # bucket = conn.create_bucket(bucket_name,location=boto.s3.connection.Location.DEFAULT)
            bucket = conn.get_bucket(BUCKET_NAME)
            # bucket = BUCKET_NAME
            imagedate = date.today()
            imagedate = imagedate.strftime("%d_%m_%Y")
            # testfile = upload_file.name

            if request.FILES:
                award_img = awards.objects.get(user=usr, id=awardid)
                img_path = award_img.award_image_path.split(username)
                splitted_img_path = img_path[1].split("/")
                # log.info('myaddedfile %s', splitted_img_path[1])

                b = Key(bucket)
                b.key = username + "/award/" + splitted_img_path[1]
                bucket.delete_key(b)

                for myfile in request.FILES.getlist("edit_award_path"):
                    fs = FileSystemStorage()
                    filename = fs.save(myfile.name, myfile)
                    uploaded_file_url = fs.url(filename)

                    k = Key(bucket)
                    k.key = username + "/award/" + imagedate + "_" + myfile.name
                    k.set_contents_from_filename(
                        settings.MEDIA_ROOT + "/" + myfile.name
                    )
                    k.make_public()
                    imageurl = (
                        "https://s3-ap-southeast-1.amazonaws.com/docmode-org-uploads/"
                        + username
                        + "/award/"
                        + imagedate
                        + "_"
                        + myfile.name
                    )
                    # log.info('editedimageurl %s', imageurl)
                award_edit = awards.objects.filter(user=usr, id=awardid).update(
                    year=year, title=title, award_image_path=imageurl
                )
            else:
                award_edit = awards.objects.filter(user=usr, id=awardid).update(
                    year=year, title=title
                )
            msg = "Award details edited successfully."
            context = {"errors": msg}
            return HttpResponseRedirect("/u/" + username)
        else:
            awardid = request.POST.get("award_number", "")
            conn = boto.connect_s3(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)

            # bucket = conn.create_bucket(bucket_name,location=boto.s3.connection.Location.DEFAULT)
            bucket = conn.get_bucket(BUCKET_NAME)
            # bucket = BUCKET_NAME
            imagedate = date.today()
            imagedate = imagedate.strftime("%d_%m_%Y")
            # testfile = upload_file.name

            award_img = awards.objects.get(user=usr, id=awardid)
            if award_img.award_image_path != "not uploaded":
                img_path = award_img.award_image_path.split(username)
                splitted_img_path = img_path[1].split("/")
                # log.info('myaddedfile %s', splitted_img_path[1])

                b = Key(bucket)
                b.key = username + "/award/" + splitted_img_path[1]
                bucket.delete_key(b)
            award_del = awards.objects.filter(user=usr, id=awardid).delete()
            msg = "Award deleted successfully."
            context = {"errors": msg}
            return HttpResponseRedirect("/u/" + username)
    else:
        msg = "Award details could not be added/edited"
        context = {
            "errors": msg,
        }
        render_to_response("learner_profile/learner_profile.html", context)


@login_required
@ensure_csrf_cookie
def research_papers_add(request):
    usr = request.user.id
    username = request.user.username
    if request.method == "POST":
        if "research_add" in request.POST:
            description = request.POST.get("research_description", "")
            title = request.POST.get("research_title", "")
            extarnal_link = request.POST.get("research_link", "")
            bucket_name = BUCKET_NAME + "/" + username + "-one/"
            conn = boto.connect_s3(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)

            # bucket = conn.create_bucket(bucket_name,location=boto.s3.connection.Location.DEFAULT)
            bucket = conn.get_bucket(BUCKET_NAME)
            # bucket = BUCKET_NAME
            imagedate = date.today()
            imagedate = imagedate.strftime("%d_%m_%Y")
            # testfile = upload_file.name
            if request.FILES:
                for myfile in request.FILES.getlist("research_pdf_path"):
                    fs = FileSystemStorage()
                    filename = fs.save(myfile.name, myfile)
                    uploaded_file_url = fs.url(filename)
                    # log.info('myfile %s', filename)

                    k = Key(bucket)
                    k.key = (
                        username + "/research_papers/" + imagedate + "_" + myfile.name
                    )
                    k.set_contents_from_filename(
                        settings.MEDIA_ROOT + "/" + myfile.name
                    )
                    k.make_public()
                    imageurl = (
                        "https://s3-ap-southeast-1.amazonaws.com/docmode-org-uploads/"
                        + username
                        + "/research_papers/"
                        + imagedate
                        + "_"
                        + myfile.name
                    )
                    # log.info('imageurl %s', imageurl)
            else:
                imageurl = "not uploaded"
            research_papers_add = research_papers(
                user=usr,
                title=title,
                description=description,
                pdf_path=imageurl,
                extarnal_link=extarnal_link,
            )
            research_papers_add.save()

            msg = "Research Papers details added successfully."
            context = {"errors": msg}
            return HttpResponseRedirect("/u/" + username)
        elif "research_papers_edit" in request.POST:
            title = request.POST.get("edit_research_title", "")
            description = request.POST.get("edit_research_description", "")
            extarnal_link = request.POST.get("edit_research_link", "")
            researchid = request.POST.get("edit_research_number", "")
            bucket_name = BUCKET_NAME + "/" + username + "-one/"

            conn = boto.connect_s3(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)

            # bucket = conn.create_bucket(bucket_name,location=boto.s3.connection.Location.DEFAULT)
            bucket = conn.get_bucket(BUCKET_NAME)
            # bucket = BUCKET_NAME
            imagedate = date.today()
            imagedate = imagedate.strftime("%d_%m_%Y")
            # testfile = upload_file.name

            if request.FILES:
                research_img = research_papers.objects.get(user=usr, id=researchid)
                img_path = research_img.pdf_path.split("research_papers")
                splitted_img_path = img_path[1].split("/")
                # log.info('myaddedfile %s', splitted_img_path[1])

                b = Key(bucket)
                b.key = username + "/research_papers/" + splitted_img_path[1]
                bucket.delete_key(b)

                for myfile in request.FILES.getlist("edit_research_pdf_path"):
                    fs = FileSystemStorage()
                    filename = fs.save(myfile.name, myfile)
                    uploaded_file_url = fs.url(filename)

                    k = Key(bucket)
                    k.key = (
                        username + "/research_papers/" + imagedate + "_" + myfile.name
                    )
                    k.set_contents_from_filename(
                        settings.MEDIA_ROOT + "/" + myfile.name
                    )
                    k.make_public()
                    imageurl = (
                        "https://s3-ap-southeast-1.amazonaws.com/docmode-org-uploads/"
                        + username
                        + "/research_papers/"
                        + imagedate
                        + "_"
                        + myfile.name
                    )
                    # log.info('editedimageurl %s', imageurl)
                research_new = research_papers.objects.filter(
                    user=usr, id=researchid
                ).update(
                    title=title,
                    description=description,
                    pdf_path=imageurl,
                    extarnal_link=extarnal_link,
                )
            else:
                research_new = research_papers.objects.filter(
                    user=usr, id=researchid
                ).update(
                    title=title, description=description, extarnal_link=extarnal_link
                )
            msg = "Research paper details edited successfully."
            context = {"errors": msg}
            return HttpResponseRedirect("/u/" + username)
        else:
            researchid = request.POST.get("research_number", "")
            conn = boto.connect_s3(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)

            # bucket = conn.create_bucket(bucket_name,location=boto.s3.connection.Location.DEFAULT)
            bucket = conn.get_bucket(BUCKET_NAME)
            # bucket = BUCKET_NAME
            imagedate = date.today()
            imagedate = imagedate.strftime("%d_%m_%Y")
            # testfile = upload_file.name

            research_img = research_papers.objects.get(user=usr, id=researchid)
            if research_img.pdf_path != "not uploaded":
                img_path = research_img.pdf_path.split("research_papers")

                splitted_img_path = img_path[1].split("/")
                # log.info('myaddedfile %s', splitted_img_path[1])

                b = Key(bucket)
                b.key = username + "/research_papers/" + splitted_img_path[1]
                bucket.delete_key(b)
            research_new = research_papers.objects.filter(
                user=usr, id=researchid
            ).delete()
            msg = "Research deleted successfully."
            context = {"errors": msg}
            return HttpResponseRedirect("/u/" + username)
    else:
        msg = "Research details could not be added/edited"
        context = {
            "errors": msg,
        }
        render_to_response("learner_profile/learner_profile.html", context)


@login_required
@ensure_csrf_cookie
def featured_media_add(request):
    usr = request.user.id
    username = request.user.username
    if request.method == "POST":
        if "featured_add" in request.POST:
            media_name = request.POST.get("featured_medianame", "")
            media_link = request.POST.get("featured_medialink", "")
            title = request.POST.get("featured_title", "")

            bucket_name = BUCKET_NAME + "/" + username + "-one/"
            conn = boto.connect_s3(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)

            # bucket = conn.create_bucket(bucket_name,location=boto.s3.connection.Location.DEFAULT)
            bucket = conn.get_bucket(BUCKET_NAME)
            # bucket = BUCKET_NAME
            imagedate = date.today()
            imagedate = imagedate.strftime("%d_%m_%Y")
            # testfile = upload_file.name
            if request.FILES:
                for myfile in request.FILES.getlist("featured_img"):
                    fs = FileSystemStorage()
                    filename = fs.save(myfile.name, myfile)
                    uploaded_file_url = fs.url(filename)
                    # log.info('myfile %s', filename)

                    k = Key(bucket)
                    k.key = username + "/featured/" + imagedate + "_" + myfile.name
                    k.set_contents_from_filename(
                        settings.MEDIA_ROOT + "/" + myfile.name
                    )
                    k.make_public()
                    imageurl = (
                        "https://s3-ap-southeast-1.amazonaws.com/docmode-org-uploads/"
                        + username
                        + "/featured/"
                        + imagedate
                        + "_"
                        + myfile.name
                    )
                    # log.info('imageurl %s', imageurl)
            else:
                imageurl = "not uploaded"
            featured_new = media_featured(
                user=usr,
                title=title,
                media_name=media_name,
                media_link=media_link,
                img=imageurl,
            )
            featured_new.save()

            msg = "featured details added successfully."
            context = {"errors": msg}
            return HttpResponseRedirect("/u/" + username)
        elif "featured_edit" in request.POST:
            media_name = request.POST.get("edit_featured_medianame", "")
            media_link = request.POST.get("edit_featured_medialink", "")
            title = request.POST.get("edit_featured_title", "")
            featuredid = request.POST.get("edit_featured_number", "")
            bucket_name = BUCKET_NAME + "/" + username + "-one/"

            conn = boto.connect_s3(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)

            # bucket = conn.create_bucket(bucket_name,location=boto.s3.connection.Location.DEFAULT)
            bucket = conn.get_bucket(BUCKET_NAME)
            # bucket = BUCKET_NAME
            imagedate = date.today()
            imagedate = imagedate.strftime("%d_%m_%Y")
            # testfile = upload_file.name

            if request.FILES:
                featured_img = media_featured.objects.get(user=usr, id=featuredid)
                img_path = featured_img.img.split("featured")
                splitted_img_path = img_path[1].split("/")
                # log.info('myaddedfile %s', splitted_img_path[1])

                b = Key(bucket)
                b.key = username + "/featured/" + splitted_img_path[1]
                bucket.delete_key(b)

                for myfile in request.FILES.getlist("edit_featured_img"):
                    fs = FileSystemStorage()
                    filename = fs.save(myfile.name, myfile)
                    uploaded_file_url = fs.url(filename)

                    k = Key(bucket)
                    k.key = username + "/featured/" + imagedate + "_" + myfile.name
                    k.set_contents_from_filename(
                        settings.MEDIA_ROOT + "/" + myfile.name
                    )
                    k.make_public()
                    imageurl = (
                        "https://s3-ap-southeast-1.amazonaws.com/docmode-org-uploads/"
                        + username
                        + "/featured/"
                        + imagedate
                        + "_"
                        + myfile.name
                    )
                    # log.info('editedimageurl %s', imageurl)
                education_new = media_featured.objects.filter(
                    user=usr, id=featuredid
                ).update(
                    title=title,
                    media_name=media_name,
                    media_link=media_link,
                    img=imageurl,
                )
            else:
                education_new = media_featured.objects.filter(
                    user=usr, id=featuredid
                ).update(title=title, media_name=media_name, media_link=media_link)
            msg = "Education details edited successfully."
            context = {"errors": msg}
            return HttpResponseRedirect("/u/" + username)
        else:
            featuredid = request.POST.get("featured_number", "")
            conn = boto.connect_s3(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)

            # bucket = conn.create_bucket(bucket_name,location=boto.s3.connection.Location.DEFAULT)
            bucket = conn.get_bucket(BUCKET_NAME)
            # bucket = BUCKET_NAME
            imagedate = date.today()
            imagedate = imagedate.strftime("%d_%m_%Y")
            # testfile = upload_file.name

            featured_img = media_featured.objects.get(user=usr, id=eduid)
            if featured_img.img != "not uploaded":
                img_path = featured_img.img.split("featured")
                splitted_img_path = img_path[1].split("/")
                # log.info('myaddedfile %s', splitted_img_path[1])

                b = Key(bucket)
                b.key = username + "/featured/" + splitted_img_path[1]
                bucket.delete_key(b)
            education_new = media_featured.objects.filter(
                user=usr, id=featuredid
            ).delete()
            msg = "Featured deleted successfully."
            context = {"errors": msg}
            return HttpResponseRedirect("/u/" + username)
    else:
        msg = "Featured details could not be added/edited"
        context = {
            "errors": msg,
        }
        render_to_response("learner_profile/learner_profile.html", context)


@login_required
@ensure_csrf_cookie
def clinic_hospital_address_add(request):
    usr = request.user.id
    username = request.user.username
    if request.method == "POST":
        if "clinic_hospital_add" in request.POST:
            clinic_hospital_name = request.POST.get("clinic_hospital_name", "")
            address_line1 = request.POST.get("clinic_hospital_address_line1", "")
            address_line2 = request.POST.get("clinic_hospital_address_line2", "")
            address_line3 = request.POST.get("clinic_hospital_address_line3", "")
            phone_number = request.POST.get("clinic_hospital_phone", "")
            website = request.POST.get("clinic_hospital_website", "")
            timings = request.POST.get("clinic_hospital_timings", "")

            clinic_hospital_contact = clinic_hospital_address(
                user=usr,
                clinic_hospital_name=clinic_hospital_name,
                address_line1=address_line1,
                address_line2=address_line2,
                address_line3=address_line3,
                phone_number=phone_number,
                website=website,
                timings=timings,
            )
            clinic_hospital_contact.save()

            msg = "Clinic/Hospital details added successfully."
            context = {"errors": msg}
            return HttpResponseRedirect("/u/" + username)
        elif "clinic_hospital_edit" in request.POST:
            clinic_hospital_name = request.POST.get("edit_clinic_hospital_name", "")
            address_line1 = request.POST.get("edit_clinic_hospital_address_line1", "")
            address_line2 = request.POST.get("edit_clinic_hospital_address_line2", "")
            address_line3 = request.POST.get("edit_clinic_hospital_address_line3", "")
            phone_number = request.POST.get("edit_clinic_hospital_phone", "")
            website = request.POST.get("edit_clinic_hospital_website", "")
            timings = request.POST.get("edit_clinic_hospital_timings", "")
            clinic_hospital_id = request.POST.get("clinic_hospital_number", "")

            clinic_hospital_contact = clinic_hospital_address.objects.filter(
                user=usr, id=clinic_hospital_id
            ).update(
                clinic_hospital_name=clinic_hospital_name,
                address_line1=address_line1,
                address_line2=address_line2,
                address_line3=address_line3,
                phone_number=phone_number,
                website=website,
                timings=timings,
            )
            msg = "Clinic/Hospital details edited successfully."
            context = {"errors": msg}
            return HttpResponseRedirect("/u/" + username)
        else:
            clinic_hospital_id = request.POST.get("del_clinic_hospital_number", "")
            clinic_hospital_contact = clinic_hospital_address.objects.filter(
                user=usr, id=clinic_hospital_id
            ).delete()
            msg = "Clinic/Hospital deleted successfully."
            context = {"errors": msg}
            return HttpResponseRedirect("/u/" + username)
    else:
        msg = "Clinic/Hospital details could not be added/edited"
        context = {
            "errors": msg,
        }
        render_to_response("learner_profile/learner_profile.html", context)


@login_required
@ensure_csrf_cookie
def healthcare_awareness_videos_add(request):
    usr = request.user.id
    username = request.user.username
    if request.method == "POST":
        if "clinic_hospital_add" in request.POST:
            video_url = request.POST.get("video_url", "")
            awareness_video = healthcare_awareness_videos(
                user=usr, video_url=video_url, active=1
            )
            awareness_video.save()

            msg = "Video added successfully."
            context = {"errors": msg}
            return HttpResponseRedirect("/u/" + username)
        elif "healthcare_awareness_videos_edit" in request.POST:
            video_url = request.POST.get("edit_video_url", "")
            awareness_video_id = request.POST.get("awareness_video_number", "")

            awareness_video = healthcare_awareness_videos.objects.filter(
                user=usr, id=awareness_video_id
            ).update(video_url=video_url, active=1)
            msg = "Video url edited successfully."
            context = {"errors": msg}
            return HttpResponseRedirect("/u/" + username)
        else:
            awareness_video_id = request.POST.get("del_awareness_video_id", "")
            awareness_video = healthcare_awareness_videos.objects.filter(
                user=usr, id=awareness_video_id
            ).delete()
            msg = "Video deleted successfully."
            context = {"errors": msg}
            return HttpResponseRedirect("/u/" + username)
    else:
        msg = "Video url could not be added/edited"
        context = {
            "errors": msg,
        }
        render_to_response("learner_profile/learner_profile.html", context)


@login_required
@ensure_csrf_cookie
def experience_add(request):
    usr = request.user.id
    username = request.user.username
    if request.method == "POST":
        if "exp_add" in request.POST:
            year = request.POST.get("year", "")
            description = request.POST.get("description", "")
            institution_name = request.POST.get("institution_name", "")

            experience_new = experience(
                user=usr,
                year=year,
                description=description,
                institution_name=institution_name,
            )
            experience_new.save()

            msg = "Experience details added successfully."
            context = {"errors": msg}
            return HttpResponseRedirect("/u/" + username)
        elif "exp_edit" in request.POST:
            year = request.POST.get("year", "")
            description = request.POST.get("description", "")
            institution_name = request.POST.get("institution_name", "")
            expid = request.POST.get("exp_edit_number", "")

            experience_new = experience.objects.filter(user=usr, id=expid).update(
                year=year, description=description, institution_name=institution_name
            )
            msg = "Experience details edited successfully."
            context = {"errors": msg}
            return HttpResponseRedirect("/u/" + username)
        else:
            expid = request.POST.get("exp_number", "")
            experience_new = experience.objects.filter(user=usr, id=expid).delete()
            msg = "Experience deleted successfully."
            context = {"errors": msg}
            return HttpResponseRedirect("/u/" + username)
    else:
        msg = "Experience details could not be added/edited"
        context = {
            "errors": msg,
        }
        render_to_response("learner_profile/learner_profile.html", context)
