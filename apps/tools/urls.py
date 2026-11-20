from django.urls import path
from . import views

app_name = "tools"

urlpatterns = [
    path("", views.tool_list_view, name="tool_list"),
    path("create/", views.tool_create_view, name="tool_create"),
    path("<int:pk>/", views.tool_detail_view, name="tool_detail"),
    path("<int:pk>/edit/", views.tool_update_view, name="tool_update"),
    path("<int:pk>/delete/", views.tool_delete_view, name="tool_delete"),
    path("my-tools/", views.my_tools_view, name="my_tools"),
    path("favoris/", views.favoris_list_view, name="favoris_list"),
    path("<int:pk>/favori/", views.toggle_favori_view, name="toggle_favori"),
]
