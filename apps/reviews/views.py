from django.http import HttpResponse


def review_create_view(request, loan_id):
    return HttpResponse("Laisser un avis")
