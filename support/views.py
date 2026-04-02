from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .models import SupportTicket, TicketMessage
from .serializers import SupportTicketSerializer, TicketMessageSerializer

class SupportTicketListCreateView(generics.ListCreateAPIView):
    serializer_class = SupportTicketSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return SupportTicket.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class SupportTicketDetailView(generics.RetrieveAPIView):
    serializer_class = SupportTicketSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return SupportTicket.objects.filter(user=self.request.user)

class TicketMessageCreateView(generics.CreateAPIView):
    serializer_class = TicketMessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, ticket_id):
        try:
            ticket = SupportTicket.objects.get(id=ticket_id, user=request.user)
        except SupportTicket.DoesNotExist:
            return Response({"error": "Ticket not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(ticket=ticket, sender=request.user)
        
        # Optionally update ticket status to 'in_progress' or similar
        return Response(serializer.data, status=status.HTTP_201_CREATED)
