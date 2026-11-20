from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("apps.accounts.urls", namespace="accounts")),
    path("tools/", include("apps.tools.urls", namespace="tools")),
    path("loans/", include("apps.loans.urls", namespace="loans")),
    path("reviews/", include("apps.reviews.urls", namespace="reviews")),
    path("dashboard/", include("apps.dashboard.urls", namespace="dashboard")),
    path("", RedirectView.as_view(pattern_name="tools:tool_list", permanent=False), name="home"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
