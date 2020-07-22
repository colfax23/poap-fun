import json
from datetime import datetime

from django.contrib.auth import authenticate
from django.contrib.auth.models import Group
from django_filters import rest_framework as filters
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.parsers import FileUploadParser
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework_jwt.authentication import JSONWebTokenAuthentication
from rest_framework_jwt.serializers import JSONWebTokenSerializer
from rest_framework_jwt.settings import api_settings
from rest_framework_jwt.views import JSONWebTokenAPIView, APIView

from core.filters import UserFilter, ParticipantFilter, RaffleFilter, ResultsTableFilter
from core.models import User, Raffle, Event, Prize, Participant, ResultsTable
from .permissions import RaffleTokenPermission, PrizeRaffleTokenPermission
from .serializers import UserSerializer, GroupSerializer, RaffleSerializer, TextEditorImageSerializer, EventSerializer, \
    PrizeSerializer, ParticipantSerializer, MultiParticipantSerializer, ResultsTableSerializer


class CustomObtainJSONWebToken(JSONWebTokenAPIView):
    serializer_class = JSONWebTokenSerializer

    def post(self, request, *args, **kwargs):
        data = request.data

        if not data.get('username', None):
            return Response({'error': 'username required'}, status=status.HTTP_400_BAD_REQUEST)

        # Allow email login as well as normal username flow
        if data['username'] and '@' in data['username']:
            if not User.objects.filter(username=data['username']).exists():
                user = User.objects.filter(email=data['username']).first()
                if user: data['username'] = user.username

        # Get serializer from received data
        serializer = self.get_serializer(data=data)

        # Check user validation
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Check authentication process validation
        user = serializer.object.get('user') or request.user
        token = serializer.object.get('token')

        user_authenticated = authenticate(username=user.username, password=data['password'])
        if not user_authenticated:
            return Response({'error': 'Authentication failed'}, status=status.HTTP_400_BAD_REQUEST)

        # Calculate jwt response token
        jwt_response_payload_handler = api_settings.JWT_RESPONSE_PAYLOAD_HANDLER
        response_token = jwt_response_payload_handler(token, user, request)

        # Serialize authenticated user (with custom serializer) and add token info to response
        user_serializer = UserSerializer(user_authenticated).data
        user_serializer['token'] = response_token['token']
        response = Response(user_serializer)

        # Set expiration in cookie (if needed)
        if api_settings.JWT_AUTH_COOKIE:
            expiration = (datetime.utcnow() + api_settings.JWT_EXPIRATION_DELTA)
            response.set_cookie(api_settings.JWT_AUTH_COOKIE, token, expires=expiration, httponly=True)

        # Return authenticated user
        return response


class UserViewSet(viewsets.ModelViewSet):
    authentication_classes = [JSONWebTokenAuthentication]
    serializer_class = UserSerializer
    filter_backends = (filters.DjangoFilterBackend, OrderingFilter)
    filter_class = UserFilter
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_permissions(self):
        permission_classes = [IsAuthenticated]
        if self.action == 'create':
            permission_classes = [AllowAny]

        return [permission() for permission in permission_classes]

    def get_queryset(self):
        queryset = User.objects.filter(is_active=True, id=self.request.user.id)
        # Filter superusers from listings
        if not self.request.user.is_superuser:
            queryset = queryset.exclude(is_superuser=True)
        return queryset

    # Custom DELETE call to deactivate instead of delete db object (attribute 'is_active' is required)
    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()


class GroupViewSet(viewsets.ModelViewSet):
    authentication_classes = [JSONWebTokenAuthentication]
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', ]
    queryset = Group.objects.all()
    serializer_class = GroupSerializer


class EventViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [AllowAny]
    http_method_names = ['get', ]
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    lookup_field = 'id'


class PrizeViewSet(viewsets.ModelViewSet):
    queryset = Prize.objects.all()
    serializer_class = PrizeSerializer
    lookup_field = 'id'
    http_method_names = ['get', ]

    def get_permissions(self):
        restricted_actions = ['update', 'partial_update', 'destroy']

        if self.action in restricted_actions:
            permission_classes = [PrizeRaffleTokenPermission]
        else:
            permission_classes = [AllowAny]
        return [permission() for permission in permission_classes]


class RaffleViewSet(viewsets.ModelViewSet):
    queryset = Raffle.objects.all()
    serializer_class = RaffleSerializer
    lookup_field = 'id'
    filter_backends = (filters.DjangoFilterBackend, OrderingFilter)
    ordering_fields = ['name', 'description', 'contact', 'draw_datetime', 'end_datetime']
    http_method_names = ['get', 'post', 'patch', 'put']
    filter_class = RaffleFilter

    def list(self, request, **kwargs):
        events = request.query_params.get('events_participated_in', None)
        if not events:
            return super(RaffleViewSet, self).list(request, **kwargs)

        raffles = Raffle.get_valid_raffles_for_event_set(json.loads(events))
        serializer = RaffleSerializer(raffles, many=True)
        return Response({"results": serializer.data})

    def get_permissions(self):
        restricted_actions = ['update', 'partial_update', 'destroy']

        if self.action in restricted_actions:
            permission_classes = [RaffleTokenPermission]
        else:
            permission_classes = [AllowAny]
        return [permission() for permission in permission_classes]


class ParticipantViewSet(viewsets.ModelViewSet):
    permission_classes = [AllowAny]
    queryset = Participant.objects.all()
    serializer_class = ParticipantSerializer
    filter_backends = (filters.DjangoFilterBackend, )
    filter_class = ParticipantFilter
    http_method_names = ['get', 'post', ]

    @action(detail=False, methods=['Post'])
    def signup_address(self, request):
        signature = request.data.get("signature", None)
        message = request.data.get("message", None)

        if not message and not signature:
            return Response(
                ("you must provide a message containing the raffle id and"
                 " the address, along with a signature for the message"),
                status=status.HTTP_400_BAD_REQUEST
            )

        if not message:
            return Response(
                "you must provide a message containing the raffle id and address",
                status=status.HTTP_400_BAD_REQUEST
            )

        if not signature:
            return Response(
                "Missing signature for message",
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = MultiParticipantSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(status=status.HTTP_201_CREATED)

    def create(self, request):
            return Response(
                ("Method not implemented"),
                status=status.HTTP_400_BAD_REQUEST
            )


class ResultsViewSet(viewsets.ModelViewSet):
    permission_classes = [AllowAny]
    queryset = ResultsTable.objects.all()
    serializer_class = ResultsTableSerializer
    lookup_field = 'id'
    filter_backends = (filters.DjangoFilterBackend, OrderingFilter)
    filter_class = ResultsTableFilter
    http_method_names = ['get', ]


class TextEditorImageView(APIView):
    permission_classes = [AllowAny]

    parser_class = (FileUploadParser,)

    def post(self, request):
        image_serializer = TextEditorImageSerializer(data=request.data)
        if image_serializer.is_valid():
            image_serializer.save()
            # TODO - Review HTTP Scheme
            host = request.META.get('HTTP_HOST', 'api.localhost')
            response_data = ({"location": "https://" + host + image_serializer.data.get("file")})
            return Response(response_data, status=status.HTTP_201_CREATED)
        else:
            return Response(image_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
