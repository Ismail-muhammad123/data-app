from rest_framework import generics, permissions, status
from rest_framework.response import Response
from support.models import SupportTicket, TicketMessage
from support.serializers import SupportTicketSerializer, TicketMessageSerializer
from notifications.utils import NotificationService
from django.contrib.auth import get_user_model
User = get_user_model()

class SupportTicketListCreateView(generics.ListCreateAPIView):
    serializer_class = SupportTicketSerializer; permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self): return SupportTicket.objects.filter(user=self.request.user).order_by('-created_at')
    def perform_create(self, serializer): 
        ticket = serializer.save(user=self.request.user)
        # Notify admins
        admins = User.objects.filter(is_staff=True, fcm_token__isnull=False)
        for admin in admins:
            NotificationService.send_push(
                user=admin,
                title="New Support Ticket",
                body=f"User {ticket.user.phone_number} created ticket: {ticket.subject}",
                data={"ticket_id": str(ticket.id), "type": "admin_new_support"}
            )

class SupportTicketDetailView(generics.RetrieveAPIView):
    serializer_class = SupportTicketSerializer; permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self): return SupportTicket.objects.filter(user=self.request.user)

class TicketMessageCreateView(generics.CreateAPIView):
    serializer_class = TicketMessageSerializer; permission_classes = [permissions.IsAuthenticated]
    def post(self, request, ticket_id):
        ticket = generics.get_object_or_404(SupportTicket, id=ticket_id, user=request.user)
        serializer = self.get_serializer(data=request.data); serializer.is_valid(raise_exception=True)
        msg = serializer.save(ticket=ticket, sender=request.user)
        
        # Notify admins
        admins = User.objects.filter(is_staff=True, fcm_token__isnull=False)
        for admin in admins:
            NotificationService.send_push(
                user=admin,
                title="New Message on Ticket",
                body=f"User replied on #{ticket.id}: {msg.message[:50]}...",
                data={"ticket_id": str(ticket.id), "type": "admin_support_reply"}
            )

        return Response(serializer.data, status=status.HTTP_201_CREATED)

class SupportTicketCloseView(generics.UpdateAPIView):
    queryset = SupportTicket.objects.all(); serializer_class = SupportTicketSerializer; permission_classes = [permissions.IsAuthenticated]
    def post(self, request, pk):
        ticket = self.get_object()
        if ticket.user != request.user: return Response({"error": "Unauthorized"}, status=403)
        ticket.status = 'closed'; ticket.save()
        return Response({"status": "Ticket closed successfully."})
