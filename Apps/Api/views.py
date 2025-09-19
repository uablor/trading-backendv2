from rest_framework.views import APIView
from rest_framework.reverse import reverse
from rest_framework.response import Response

class LIstApiAPIview(APIView):

    def get(self, request, *args, **kwargs):
        data = {
            "auth": {
              
                "user-register": reverse("api:user_register", request=request, format=None),
                "user-login": reverse("api:user_login", request=request, format=None),
                "validate-user-login-otp": reverse("api:validate-user-login-otp", request=request, format=None),
                # "get_user": reverse("api:get_user-list", request=request, format=None),
               
                # "wallet": reverse("api:wallet", request=request, format=None),
                "trading": reverse("api:trading", request=request, format=None),
                "auth-me": reverse("api:auth-me", request=request, format=None),
                "custom password":{
                "change password": reverse("api:change-password", request=request),
                "send reset password": reverse("api:send-reset-password", request=request),
                "reset password": reverse("api:reset-password", kwargs={"encoded_pk": "<encoded_pk>", "token": "<token>"}, request=request, format=None),
                },
            },
            "account" :{
                 "user": reverse("api:user-list", request=request, format=None),
                 "group": reverse("api:group-list", request=request, format=None),
                 "permission": reverse("api:permission-list", request=request, format=None),
            },
            "wallet" :{
                 "wallet": reverse("api:wallet-list", request=request, format=None),
            },
            "next" :{
                 "get_next_candlestick_time": reverse("api:get_next_candlestick_time", request=request, format=None),
            },
        }
        return Response(data)
