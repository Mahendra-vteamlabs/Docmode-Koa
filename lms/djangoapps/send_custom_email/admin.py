from config_models.admin import ConfigurationModelAdmin
from django.contrib import admin

from .forms import  CustomEmailTemplateForm
from .models import Custom_email, CustomEmailTemplate, custom_mail_to_users

class CustomemailAdmin(admin.ModelAdmin):
    """Admin for course email."""
    list_display = ['course_id']

class CustomEmailTemplateAdmin(admin.ModelAdmin):
    """Admin for course email templates."""
    form = CustomEmailTemplateForm
    fieldsets = (
        (None, {
            # make the HTML template display above the plain template:
            'fields': ('html_template', 'plain_template', 'name'),
            'description': '''
Enter template to be used by course staff when sending emails to enrolled students.

The HTML template is for HTML email, and may contain HTML markup.  The plain template is
for plaintext email.  Both templates should contain the string '{{message_body}}' (with
two curly braces on each side), to indicate where the email text is to be inserted.

Other tags that may be used (surrounded by one curly brace on each side):
{platform_name}        : the name of the platform
{course_title}         : the name of the course
{course_root}          : the URL path to the root of the course
{course_language}      : the course language. The default is None.
{course_url}           : the course's full URL
{email}                : the user's email address
{account_settings_url} : URL at which users can change account preferences
{email_settings_url}   : URL at which users can change course email preferences
{course_image_url}     : URL for the course's course image.
    Will return a broken link if course doesn't have a course image set.

Note that there is currently NO validation on tags, so be careful. Typos or use of
unsupported tags will cause email sending to fail.
'''
        }),
    )
    # Turn off the action bar (we have no bulk actions)
    actions = None

    list_display = ['name']

    def has_add_permission(self, request):
        """Enable the ability to add new templates, as we want to be able to define multiple templates."""
        return True

    def has_delete_permission(self, request, obj=None):
        """
        Disables the ability to remove existing templates, as we'd like to make sure we don't have dangling references.
        """
        return False


class Custom_mail_to_usersAdmin(admin.ModelAdmin):
    list_display = ['user_email','course_id']
    search = ['user_email']

admin.site.register(Custom_email, CustomemailAdmin)
admin.site.register(CustomEmailTemplate, CustomEmailTemplateAdmin)
admin.site.register(custom_mail_to_users, Custom_mail_to_usersAdmin)