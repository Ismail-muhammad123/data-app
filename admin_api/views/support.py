from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema_view, extend_schema
from support.models import SupportTicket, TicketMessage
from admin_api.serializers import AdminSupportTicketSerializer

@extend_schema_view(
    list=extend_schema(tags=["Admin Support"]),
    retrieve=extend_schema(tags=["Admin Support"]),
    partial_update=extend_schema(tags=["Admin Support"]),
)
class AdminSupportTicketViewSet(viewsets.ModelViewSet):
    queryset = SupportTicket.objects.all().order_by('-created_at')
    serializer_class = AdminSupportTicketSerializer
    permission_classes = [IsAuthenticated] 

    @action(detail=True, methods=['post'], url_path='reply')
    def reply(self, request, pk=None):
        ticket = self.get_object()
        message = request.data.get('message')
        TicketMessage.objects.create(
            ticket=ticket,
            sender=request.user,
            message=message,
            is_admin=True
        )
        if ticket.status == 'open':
            ticket.status = 'in_progress'
            ticket.save()
        return Response({"status": "Reply sent"})

    @action(detail=True, methods=['post'], url_path='close')
    def close(self, request, pk=None):
        ticket = self.get_object()
        ticket.status = 'closed'
        ticket.save()
        return Response({"status": "Ticket closed"})
