from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from authentication.models import UserProfile
from authentication.permissions import CookieJWTAuthentication
from authentication.serializers import UserProfileSerializer
from .serializers import ProfileUpdateSerializer

class ProfileView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieJWTAuthentication]

    def get(self, request):
        try:
            profile = request.user.profile
            serializer = UserProfileSerializer(profile)
            return Response(serializer.data)
        except UserProfile.DoesNotExist:
            return Response({'detail': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request):
        try:
            profile = request.user.profile
            serializer = ProfileUpdateSerializer(profile, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                # Return full profile using the GET serializer format
                return Response(UserProfileSerializer(profile).data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except UserProfile.DoesNotExist:
            return Response({'detail': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)
