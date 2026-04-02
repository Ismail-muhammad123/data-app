from django.urls import path
from .views import SupportTicketListCreateView, SupportTicketDetailView, TicketMessageCreateView

urlpatterns = [
    path('', SupportTicketListCreateView.as_view(), name='ticket-list-create'),
    path('<int:pk>/', SupportTicketDetailView.as_view(), name='ticket-detail'),
    path('<int:ticket_id>/messages/', TicketMessageCreateView.as_view(), name='ticket-message-create'),
]
