# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from django.conf import settings
from .models import (
    education,
    awards,
    research_papers,
    media_featured,
    clinic_hospital_address,
)


# class TinyMCEWidget(TinyMCE):
#     def use_required_attribute(self, *args):
#         return False


class education_form(forms.ModelForm):
    year = forms.IntegerField(
        label="Year",
        required=True,
        error_messages={
            "required": "Year is required.",
        },
    )

    description = forms.CharField(
        label="Description",
        required=True,
        error_messages={
            "required": "Description is required",
        },
    )

    institution_name = forms.CharField(
        label="Institution Name",
        required=True,
        error_messages={
            "required": "Institution name is required.",
        },
    )

    certificate_path = forms.CharField(
        label="Certificate Image",
        required=True,
        error_messages={
            "required": "Year is required.",
        },
    )

    def clean(self):
        year = self.cleaned_data["year"]
        description = self.cleaned_data["description"]
        institution_name = self.cleaned_data["institution_name"]

    class Meta:
        model = education
        fields = ("year", "description", "institution_name", "certificate_path")


class award_form(forms.ModelForm):
    year = forms.IntegerField(
        label="Year",
        required=True,
        error_messages={
            "required": "Year is required.",
        },
    )

    title = forms.CharField(
        label="Title",
        required=True,
        error_messages={
            "required": "Title is required.",
        },
    )

    award_image_path = forms.CharField(
        label="Certificate Image",
        required=True,
        error_messages={
            "required": "Certificate image is required.",
        },
    )

    def clean(self):
        year = self.cleaned_data["year"]
        title = self.cleaned_data["title"]
        award_image_path = self.cleaned_data["award_image_path"]

    class Meta:
        model = awards
        fields = ("year", "title", "award_image_path")


class research_paper_form(forms.ModelForm):

    title = forms.CharField(
        label="Title",
        required=True,
        error_messages={
            "required": "Title is required.",
        },
    )

    description = forms.CharField(
        label="Description",
        required=True,
        error_messages={
            "required": "Description is required.",
        },
    )

    pdf_path = forms.CharField(
        label="Certificate Image",
        required=True,
        error_messages={
            "required": "Certificate image is required.",
        },
    )

    external_link = forms.CharField(
        label="External Url",
    )

    def clean(self):

        title = self.cleaned_data["title"]
        description = self.cleaned_data["description"]
        pdf_path = self.cleaned_data["pdf_path"]
        extarnal_link = self.cleaned_data["extarnal_link "]

    class Meta:
        model = research_papers
        fields = ("title", "description", "pdf_path", "extarnal_link")
