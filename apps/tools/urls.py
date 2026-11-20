from django.urls import path
from . import views

app_name = "tools"

urlpatterns = [
    path("", views.tool_list_view, name="tool_list"),
    path("my-tools/", views.my_tools_view, name="my_tools"),
    path("favoris/", views.favoris_list_view, name="favoris_list"),
]
