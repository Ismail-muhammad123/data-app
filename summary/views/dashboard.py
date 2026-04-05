from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from summary.models import SummaryDashboard

class SummaryView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        start, end = request.query_params.get("start"), request.query_params.get("end")
        return Response(SummaryDashboard.summary(start=start, end=end))
