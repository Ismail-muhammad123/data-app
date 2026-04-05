from rest_framework import generics, permissions, serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Sum
from drf_spectacular.utils import extend_schema, inline_serializer
from users.models import Referral
from users.serializers import ReferralSerializer

@extend_schema(tags=["Account - Referrals"])
class ReferralListView(generics.ListAPIView):
    serializer_class = ReferralSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Referral.objects.filter(referrer=self.request.user)

class ReferralStatsView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    @extend_schema(tags=["Account - Referrals"], responses={200: inline_serializer("ReferralStatsResponse", fields={"referral_code": serializers.CharField(), "total_referrals": serializers.IntegerField(), "total_bonus_earned": serializers.FloatField()})})
    def get(self, request):
        refs = Referral.objects.filter(referrer=request.user)
        return Response({"referral_code": request.user.referral_code, "total_referrals": refs.count(), "total_bonus_earned": float(refs.aggregate(total=Sum('bonus_amount'))['total'] or 0)})
