from rest_framework import generics, permissions, status
from rest_framework.response import Response
from support.models import SupportTicket, TicketMessage
from support.serializers import SupportTicketSerializer, TicketMessageSerializer

class SupportTicketListCreateView(generics.ListCreateAPIView):
    serializer_class = SupportTicketSerializer; permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self): return SupportTicket.objects.filter(user=self.request.user).order_by('-created_at')
    def perform_create(self, serializer): serializer.save(user=self.request.user)

class SupportTicketDetailView(generics.RetrieveAPIView):
    serializer_class = SupportTicketSerializer; permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self): return SupportTicket.objects.filter(user=self.request.user)

class TicketMessageCreateView(generics.CreateAPIView):
    serializer_class = TicketMessageSerializer; permission_classes = [permissions.IsAuthenticated]
    def post(self, request, ticket_id):
        ticket = generics.get_object_or_404(SupportTicket, id=ticket_id, user=request.user)
        serializer = self.get_serializer(data=request.data); serializer.is_valid(raise_exception=True)
        serializer.save(ticket=ticket, sender=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class SupportTicketCloseView(generics.UpdateAPIView):
    queryset = SupportTicket.objects.all(); serializer_class = SupportTicketSerializer; permission_classes = [permissions.IsAuthenticated]
    def post(self, request, pk):
        ticket = self.get_object()
        if ticket.user != request.user: return Response({"error": "Unauthorized"}, status=403)
        ticket.status = 'closed'; ticket.save()
        return Response({"status": "Ticket closed successfully."})
