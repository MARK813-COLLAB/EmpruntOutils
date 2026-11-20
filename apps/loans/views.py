from django.http import HttpResponse


def loan_list_view(request):
    return HttpResponse("Mes prêts")


def loan_create_view(request, tool_id):
    return HttpResponse("Demande d'emprunt")
