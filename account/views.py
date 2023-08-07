from django.shortcuts import render

# Create your views here.
import random

from app.tasks import send_confirmation_email_task
from django.contrib.auth import get_user_model
from django.urls.conf import path
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.viewsets import GenericViewSet,ModelViewSet
from rest_framework.mixins import ListModelMixin,CreateModelMixin
from rest_framework.response import Response
from account import serializers
from account.send_mail import send_confirmation_email
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

User = get_user_model()


class UserViewSet(ListModelMixin, GenericViewSet,CreateModelMixin):
    queryset = User.objects.all()
    serializer_class = serializers.UserSerializer
    permission_classes = (AllowAny, )
    @action(['GET'],detail=False)
    def listing(request, *args, **kwargs):

        serializer = serializers.UserListSerializers # Instantiate the serializer class
        data = User.objects.all()
        serialized_data = serializer(data, many=True).data  # Serialize the data

        return Response(serialized_data, status=200)

    @action(['POST'], detail=False)
    def register(self, request, *args, **kwargs):
        serializer = serializers.RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        if user:
            try:
                send_confirmation_email_task.delay(user.email, user.activation_code)
            except:
                return Response({'msg': 'Registered, but troubles with email!', 'data': serializer.data}, status=200)
        return Response(serializer.data, status=201)


    @action(['GET'], detail=False, url_path='activate/(?P<uuid>[0-9A-Fa-f-]+)')
    def activate(self, request, uuid):
        try:
            user = User.objects.get(activation_code=uuid)
        except User.DoesNotExist:
            return Response({'msg': 'Invalid link or link expired!'}, status=400)
        user.is_active = True
        user.activation_code = ''
        user.save()
        return Response({'msg': 'Successfully activated!'}, status=200)


class LoginView(TokenObtainPairView):
    permission_classes = (AllowAny, )


class RefreshView(TokenRefreshView):
    permission_classes = (AllowAny, )
