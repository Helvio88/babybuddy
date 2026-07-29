# -*- coding: utf-8 -*-
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic.base import TemplateView
from django.views.generic.detail import DetailView

from babybuddy.mixins import LoginRequiredMixin, PermissionRequiredMixin
from core.models import Child


class Dashboard(LoginRequiredMixin, TemplateView):
    # TODO: Use .card-deck in this template once BS4 is finalized.
    template_name = "dashboard/dashboard.html"

    # Show the overall dashboard or a child dashboard if one Child instance.
    def get(self, request, *args, **kwargs):
        children = Child.objects.count()
        if children == 0:
            return HttpResponseRedirect(reverse("babybuddy:welcome"))
        elif children == 1:
            return HttpResponseRedirect(
                reverse("dashboard:dashboard-child", args={Child.objects.first().slug})
            )
        return super(Dashboard, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(Dashboard, self).get_context_data(**kwargs)
        context["objects"] = Child.objects.all().order_by(
            "last_name", "first_name", "id"
        )
        return context


class ChildDashboard(PermissionRequiredMixin, DetailView):
    model = Child
    permission_required = ("core.view_child",)
    template_name = "dashboard/child.html"


class DashboardNG(LoginRequiredMixin, TemplateView):
    """
    Insights dashboard (NG) entry point — live DB data, separate from classic dashboard.
    """

    template_name = "dashboard/dashboard_ng.html"

    def get(self, request, *args, **kwargs):
        children = Child.objects.count()
        if children == 0:
            return HttpResponseRedirect(reverse("babybuddy:welcome"))
        elif children == 1:
            return HttpResponseRedirect(
                reverse(
                    "dashboard:dashboard-ng-child",
                    args=[Child.objects.first().slug],
                )
                + self._range_query(request)
            )
        return super(DashboardNG, self).get(request, *args, **kwargs)

    @staticmethod
    def _range_query(request):
        range_key = request.GET.get("range")
        if range_key:
            return f"?range={range_key}"
        return ""

    def get_context_data(self, **kwargs):
        context = super(DashboardNG, self).get_context_data(**kwargs)
        context["objects"] = Child.objects.all().order_by(
            "last_name", "first_name", "id"
        )
        context["range_key"] = self.request.GET.get("range", "14d")
        return context


class ChildDashboardNG(PermissionRequiredMixin, DetailView):
    """
    Per-child insights dashboard with live analytics charts.
    """

    model = Child
    permission_required = ("core.view_child",)
    template_name = "dashboard/dashboard_ng_child.html"
    context_object_name = "object"

    def get_context_data(self, **kwargs):
        from dashboard import analytics_ng, graphs_ng

        context = super(ChildDashboardNG, self).get_context_data(**kwargs)
        range_key = analytics_ng.parse_range(self.request.GET.get("range"))
        ng = analytics_ng.build_dashboard_context(self.object, range_key)
        context.update(ng)
        context.update(graphs_ng.build_all_charts(ng))
        return context
