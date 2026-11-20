from django.http import HttpResponse


def tool_list_view(request):
    return HttpResponse("Catalogue d'outils")


def my_tools_view(request):
    return HttpResponse("Mes outils")


def favoris_list_view(request):
    return HttpResponse("Mes favoris")
