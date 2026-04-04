from django.urls import path
from .views import SupportTicketListCreateView, SupportTicketDetailView, TicketMessageCreateView, SupportTicketCloseView

urlpatterns = [
    path('', SupportTicketListCreateView.as_view(), name='ticket-list-create'),
    path('<int:pk>/', SupportTicketDetailView.as_view(), name='ticket-detail'),
    path('<int:pk>/close/', SupportTicketCloseView.as_view(), name='ticket-close'),
    path('<int:ticket_id>/messages/', TicketMessageCreateView.as_view(), name='ticket-message-create'),
]
