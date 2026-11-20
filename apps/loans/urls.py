from django.urls import path
from . import views

app_name = "loans"

urlpatterns = [
    path("", views.loan_list_view, name="loan_list"),
    path("<int:tool_id>/borrow/", views.loan_create_view, name="loan_create"),
    path("<int:pk>/accept/", views.loan_accept_view, name="loan_accept"),
    path("<int:pk>/refuse/", views.loan_refuse_view, name="loan_refuse"),
    path("<int:pk>/start/", views.loan_start_view, name="loan_start"),
    path("<int:pk>/return/", views.loan_return_view, name="loan_return"),
    path("<int:pk>/extend/", views.loan_prolongation_view, name="loan_extend"),
    path("<int:pk>/extend/<str:action>/", views.loan_prolongation_validate_view, name="loan_extend_validate"),
]
