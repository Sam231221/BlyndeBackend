from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response

from django.contrib.auth.models import User
from Mbase.serializers import UserSerializer, UserSerializerWithToken

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

from django.contrib.auth.hashers import make_password
from rest_framework import status


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    #this function returns actual response to frontend.
    '''
    refresh and access are returned under hood(Hover the pointer over TokenObtainPairSerializer and click on it for more details. )
        data["refresh"] = str(refresh)
        data["access"] = str(refresh.access_token)
    '''
    def validate(self, attrs):
        data = super().validate(attrs)
        print('\ntoken data:', data)
        serializer = UserSerializerWithToken(self.user).data
        print('\nserializer:', serializer)
        '''
        serializer: {'id': 1, '_id': 1, 'username': 'Sam', 'email': 'samirshahi9882@gmail.com', 'name': 'samirshahi9882@gmail.com', 'isAdmin': True, 
        'token': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNjY0Nzg0MDEyLCJpYXQiOjE2NjIxOTIwMTIsImp0aSI6IjFhYzRhNjFjYTgwMzQwNGE4ZmUwNDIzZTM4YTEyNDY1IiwidXNlcl9pZCI6MX0.dnV2PalNENdhO8Iw3_RE2A4Ipq4gTRBELzfyXNuRMf8'}    
            
            '''

        for key, value in serializer.items():
            data[key] = value
        print('data:', data)
        return data


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


@api_view(['POST'])
def registerUser(request):
    #data is generally dictionary.
    data = request.data
    print(data)
    try:
        user = User.objects.create(
            first_name=data['name'],
            username=data['email'],
            email=data['email'],
            #make_password() is a function that hashes password.
            password=make_password(data['password'])
        )
        print('user:', user)
        serializer = UserSerializerWithToken(user, many=False)
        
        #serializer.data is  a json 
        return Response(serializer.data)
    except:
        message = {'detail': 'User with this email already exists'}
        return Response(message, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def updateUserProfile(request):
    user = request.user
    #UserSerializerWithToken is used so only authenticated and owner can update it.
    serializer = UserSerializerWithToken(user, many=False)

    data = request.data
    user.first_name = data['name']
    user.username = data['email']
    user.email = data['email']

    if not data['password']:
        user.password = make_password(data['password'])

    user.save()

    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getUserProfile(request):
    user = request.user
    print('user:',user)
    serializer = UserSerializer(user, many=False)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def getUsers(request):
    users = User.objects.all()
    serializer = UserSerializer(users, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def getUserById(request, pk):
    user = User.objects.get(id=pk)
    serializer = UserSerializer(user, many=False)
    return Response(serializer.data)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def updateUser(request, pk):
    user = User.objects.get(id=pk)

    data = request.data

    user.first_name = data['name']
    user.username = data['email']
    user.email = data['email']
    user.is_staff = data['isAdmin']

    user.save()

    serializer = UserSerializer(user, many=False)

    return Response(serializer.data)


@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def deleteUser(request, pk):
    userForDeletion = User.objects.get(id=pk)
    userForDeletion.delete()
    return Response('User was deleted')
