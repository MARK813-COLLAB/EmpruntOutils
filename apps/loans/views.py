from django.http import HttpResponse


def loan_list_view(request):
    return HttpResponse("Mes prêts")
