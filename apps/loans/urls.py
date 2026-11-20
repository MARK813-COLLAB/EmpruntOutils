from django.urls import path
from . import views

app_name = "loans"

urlpatterns = [
    path("", views.loan_list_view, name="loan_list"),
    path("<int:tool_id>/borrow/", views.loan_create_view, name="loan_create"),
]
