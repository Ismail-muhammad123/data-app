from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import SummaryDashboard

class SummaryView(APIView):
    """
    Endpoint for system-wide dashboard statistics and financial analytics.
    Allows for date-range filtering via 'start' and 'end' query parameters.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        start = request.query_params.get("start")
        end = request.query_params.get("end")
        data = SummaryDashboard.summary(start=start, end=end)
        return Response(data)
