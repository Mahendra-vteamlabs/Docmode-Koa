import logging
from django.views.decorators.csrf import csrf_exempt
from edxmako.shortcuts import render_to_response
from django.http import JsonResponse

log = logging.getLogger(__name__)


@csrf_exempt
def generate_pdf(request):
    file_url = request.GET.get("file", "")
    file_url = file_url.replace(" ", "+")
    context = {"file_url": file_url}
    return render_to_response("pdf_viewer_mobile.html", context)
