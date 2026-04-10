from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiExample
from support.models import SupportTicket, TicketMessage
from admin_api.permissions import CanManageUsers
from admin_api.serializers import (
    AdminSupportTicketSerializer, AdminSupportReplyRequestSerializer, 
    AdminStatusResponseSerializer
)
from admin_api.utils import log_admin_action
from notifications.utils import NotificationService

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
        responses={200: AdminStatusResponseSerializer},
        examples=[
            OpenApiExample(
                'Reply to Support Ticket',
                description='Example of an admin replying to a support ticket.',
                value={
                    "message": "We have received your request and our team is looking into it. Please hold on.",
                },
                request_only=True
            ),
            OpenApiExample(
                'Reply Success Response',
                description='Successful reply to a ticket.',
                value={
                    "status": "SUCCESS",
                    "message": "Reply sent successfully."
                },
                response_only=True
            )
        ]
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

        # Log admin action
        log_admin_action(
            user=request.user,
            action_type="REPLY_SUPPORT",
            description=f"Replied to support ticket #{ticket.id}",
            target=ticket
        )

        # Notify user (FCM)
        NotificationService.send_push(
            user=ticket.user,
            title=f"Support Update: {ticket.subject}",
            body=f"An admin has replied to your ticket: {serializer.validated_data['message'][:50]}...",
            data={"ticket_id": str(ticket.id), "type": "support_reply"}
        )

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

        # Log admin action
        log_admin_action(
            user=request.user,
            action_type="CLOSE_SUPPORT",
            description=f"Closed support ticket #{ticket.id}",
            target=ticket
        )
        
        # Notify user (FCM)
        NotificationService.send_push(
            user=ticket.user,
            title=f"Ticket Closed: {ticket.subject}",
            body="Your support ticket has been marked as closed.",
            data={"ticket_id": str(ticket.id), "type": "support_closed"}
        )

        return Response({"status": "SUCCESS", "message": "Ticket closed successfully."})
