from django.urls import path
from . import views

app_name = "reviews"

urlpatterns = [
    path("<int:loan_id>/create/", views.review_create_view, name="review_create"),
]
