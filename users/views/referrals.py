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


@extend_schema(tags=["Account - Referrals"])
class ReferralStatsView(APIView):
    """
    GET /users/referrals/stats/
    Returns the user's referral code (creating one if it doesn't exist yet)
    together with referral summary statistics.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        responses={200: inline_serializer("ReferralStatsResponse", fields={
            "referral_code": serializers.CharField(),
            "total_referrals": serializers.IntegerField(),
            "total_bonus_earned": serializers.FloatField(),
            "bonus_paid_count": serializers.IntegerField(),
            "bonus_pending_count": serializers.IntegerField(),
        })}
    )
    def get(self, request):
        user = request.user

        # Auto-generate referral code if missing (e.g. legacy accounts)
        if not user.referral_code:
            user.referral_code = user._generate_referral_code()
            user.save(update_fields=['referral_code'])

        refs = Referral.objects.filter(referrer=user)
        agg = refs.aggregate(total=Sum('bonus_amount'))

        return Response({
            "referral_code": user.referral_code,
            "total_referrals": refs.count(),
            "total_bonus_earned": float(agg['total'] or 0),
            "bonus_paid_count": refs.filter(bonus_paid=True).count(),
            "bonus_pending_count": refs.filter(bonus_paid=False).count(),
        })
