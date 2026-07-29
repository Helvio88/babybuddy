# -*- coding: utf-8 -*-
from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("dashboard/", views.Dashboard.as_view(), name="dashboard"),
    path(
        "children/<str:slug>/dashboard/",
        views.ChildDashboard.as_view(),
        name="dashboard-child",
    ),
    # Dashboard NG — analytics insights page (live ORM data)
    path("dashboard-ng/", views.DashboardNG.as_view(), name="dashboard-ng"),
    path(
        "children/<str:slug>/dashboard-ng/",
        views.ChildDashboardNG.as_view(),
        name="dashboard-ng-child",
    ),
]
