from admin_api.permissions import CanManageUsers
from admin_api.serializers import AdminSupportTicketSerializer, AdminSupportReplyRequestSerializer, AdminStatusResponseSerializer

@extend_schema_view(
    list=extend_schema(tags=["Admin Support"], summary="List all support tickets"),
    retrieve=extend_schema(tags=["Admin Support"], summary="Get ticket details with messages"),
    partial_update=extend_schema(tags=["Admin Support"], summary="Update ticket status or category"),
)
class AdminSupportTicketViewSet(viewsets.ModelViewSet):
    """
    Manage user support tickets. Allows admins to list, retrieve, update, 
    and reply to tickets.
    """
    queryset = SupportTicket.objects.all().select_related('user').prefetch_related('messages').order_by('-created_at')
    serializer_class = AdminSupportTicketSerializer
    permission_classes = [CanManageUsers] 

    @extend_schema(
        tags=["Admin Support"],
        summary="Reply to a ticket",
        request=AdminSupportReplyRequestSerializer,
        responses={200: AdminStatusResponseSerializer}
    )
    @action(detail=True, methods=['post'], url_path='reply')
    def reply(self, request, pk=None):
        ticket = self.get_object()
        serializer = AdminSupportReplyRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        TicketMessage.objects.create(
            ticket=ticket,
            sender=request.user,
            message=serializer.validated_data['message'],
            is_admin=True
        )
        if ticket.status == 'open':
            ticket.status = 'in_progress'
            ticket.save()
        return Response({"status": "SUCCESS", "message": "Reply sent successfully."})

    @extend_schema(
        tags=["Admin Support"],
        summary="Close a ticket",
        responses={200: AdminStatusResponseSerializer}
    )
    @action(detail=True, methods=['post'], url_path='close')
    def close(self, request, pk=None):
        ticket = self.get_object()
        ticket.status = 'closed'
        ticket.save()
        return Response({"status": "SUCCESS", "message": "Ticket closed successfully."})
