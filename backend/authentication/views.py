from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from .serializers import UserRegistrationSerializer, UserLoginSerializer, SafeUserSerializer
from .models import UserProfile
from .permissions import CookieJWTAuthentication

class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            safe_user = {
                'id': user.id,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
                'phone': user.profile.phone
            }
            return Response(safe_user, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            identifier = serializer.validated_data['identifier']
            password = serializer.validated_data['password']
            
            user = None
            if '@' in identifier:
                try:
                    user_obj = User.objects.get(email=identifier)
                    user = authenticate(username=user_obj.username, password=password)
                except User.DoesNotExist:
                    pass
            else:
                user = authenticate(username=identifier, password=password)

            if user is not None:
                refresh = RefreshToken.for_user(user)
                safe_user = {
                    'id': user.id,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'email': user.email,
                    'phone': user.profile.phone
                }
                response = Response(safe_user, status=status.HTTP_200_OK)
                response.set_cookie(
                    'access_token',
                    str(refresh.access_token),
                    httponly=True,
                    samesite='Lax',
                    max_age=900,
                    path='/'
                )
                response.set_cookie(
                    'refresh_token',
                    str(refresh),
                    httponly=True,
                    samesite='Lax',
                    max_age=604800,
                    path='/api/auth/refresh/'
                )
                return response
            
            return Response({'detail': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieJWTAuthentication]

    def post(self, request):
        try:
            refresh_token = request.COOKIES.get('refresh_token')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            response = Response({'detail': 'Successfully logged out.'}, status=status.HTTP_200_OK)
            response.delete_cookie('access_token', path='/')
            response.delete_cookie('refresh_token', path='/api/auth/refresh/')
            return response
        except Exception:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class TokenRefreshView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.COOKIES.get('refresh_token')
        if not refresh_token:
            return Response({'detail': 'Refresh token missing'}, status=status.HTTP_401_UNAUTHORIZED)
            
        try:
            refresh = RefreshToken(refresh_token)
            access_token = str(refresh.access_token)
            
            response = Response({'detail': 'Token refreshed successfully'})
            response.set_cookie(
                'access_token',
                access_token,
                httponly=True,
                samesite='Lax',
                max_age=900,
                path='/'
            )
            # Depending on ROTATE_REFRESH_TOKENS, simplejwt might auto-blacklist and we should issue a new refresh token.
            # However, simpler to just rotate it manually if needed, but since we rely on cookie:
            response.set_cookie(
                'refresh_token',
                str(refresh),
                httponly=True,
                samesite='Lax',
                max_age=604800,
                path='/api/auth/refresh/'
            )
            return response
        except Exception:
            response = Response({'detail': 'Invalid refresh token'}, status=status.HTTP_401_UNAUTHORIZED)
            response.delete_cookie('access_token', path='/')
            response.delete_cookie('refresh_token', path='/api/auth/refresh/')
            return response


class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieJWTAuthentication]

    def get(self, request):
        if request.user.is_authenticated:
            user = request.user
            return Response({
                'authenticated': True,
                'user': {
                    'id': user.id,
                    'firstName': user.first_name,
                    'lastName': user.last_name,
                    'email': user.email,
                    'phone': user.profile.phone
                }
            })
        return Response({'authenticated': False}, status=status.HTTP_401_UNAUTHORIZED)

    def handle_exception(self, exc):
        return Response({'authenticated': False}, status=status.HTTP_401_UNAUTHORIZED)
