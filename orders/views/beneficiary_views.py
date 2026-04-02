from rest_framework import generics, permissions
from drf_spectacular.utils import extend_schema
from orders.models import PurchaseBeneficiary
from orders.serializers import PurchaseBeneficiarySerializer


@extend_schema(tags=["Orders - Beneficiaries"])
class PurchaseBeneficiaryListCreateView(generics.ListCreateAPIView):
    """List and create saved purchase beneficiaries (e.g. saved meter numbers, smartcard IDs)."""
    serializer_class = PurchaseBeneficiarySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = PurchaseBeneficiary.objects.filter(user=self.request.user)
        service_type = self.request.query_params.get('type')
        if service_type:
            qs = qs.filter(service_type=service_type)
        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


@extend_schema(tags=["Orders - Beneficiaries"])
class PurchaseBeneficiaryDeleteView(generics.DestroyAPIView):
    """Delete a saved purchase beneficiary."""
    serializer_class = PurchaseBeneficiarySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return PurchaseBeneficiary.objects.filter(user=self.request.user)
