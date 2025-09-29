from django.urls import path

from .views import (
    DashboardOverviewView,
    BarbershopAnalyticsView,
    BarberPerformanceView,
    RevenueAnalyticsView,
    ServicePopularityView,
    CustomerInsightsView,
    MyAnalyticsView,
)

urlpatterns = [
    # Analytics endpoints
    path("analytics/dashboard/", DashboardOverviewView.as_view(), name="dashboard-overview"),
    path("analytics/barbershop/<uuid:barbershop_id>/", BarbershopAnalyticsView.as_view(), name="barbershop-analytics"),
    path("analytics/barber/<uuid:barber_id>/", BarberPerformanceView.as_view(), name="barber-performance"),
    path("analytics/revenue/", RevenueAnalyticsView.as_view(), name="revenue-analytics"),
    path("analytics/services/", ServicePopularityView.as_view(), name="service-popularity"),
    path("analytics/customers/", CustomerInsightsView.as_view(), name="customer-insights"),
    path("analytics/my-analytics/", MyAnalyticsView.as_view(), name="my-analytics"),
]