from django.urls import path
from Apps.Chart.views import (KlineDataView, TradeView, TimeUntilNextCandlestickView, get_next_candlestick_time)
from Apps.Account.views import (
    UserLoginView,
    UserRegisterCreateAPIview,
    UserViewsets,
    GroupViewSet,
    GroupViewSet,
    PermissionViewSet,
    User_Me,
    VerifyEmailAPIView,
    ResendVerificationEmailAPIView,
    ChangePasswordAPIview,
    ResetPasswordAPIView,
    Send_Email_Rest_Password,
    GenerateOTPView,
    ValidateOTPView,
    ValidateOTP_UserLoginView,
    )
from .views import LIstApiAPIview
from rest_framework.routers import DefaultRouter
from Apps.Trading.views import (Trading, WalletViewSet)


app_name = "api"
router = DefaultRouter()

# router.register(r"get-user", UserDetailViews, basename="get_user")
router.register(r"user", UserViewsets, basename="user")
router.register(r"group", GroupViewSet, basename="group")
router.register(r"permission", PermissionViewSet, basename="permission")
router.register(r"wallet", WalletViewSet, basename="wallet")
# router.register(r'wallets', WalletViewSet, basename="wallet")


urlpatterns = [
    path("", LIstApiAPIview.as_view(), name="list_api_view"),
    path('klines/', KlineDataView.as_view(), name='kline-data'),
    path('trade/', TradeView.as_view(), name='trade'),
    path("auth-me/", User_Me.as_view(), name="auth-me"),
    path('user-login/', UserLoginView.as_view(), name='user_login'),
    path('time_until_next_candlestick/', TimeUntilNextCandlestickView.as_view(), name='time_until_next_candlestick'),
    path('user-register/', UserRegisterCreateAPIview.as_view(), name='user_register'),
    path('trading/', Trading.as_view(), name='trading'),
    path("verify-email/", VerifyEmailAPIView.as_view(), name="verify-email"),
    path("resend-verify-email/", ResendVerificationEmailAPIView.as_view(), name="resend-verify-email"),
    path("get_next_candlestick_time/", get_next_candlestick_time.as_view(), name="get_next_candlestick_time"),
    path("change-password/", ChangePasswordAPIview.as_view(), name="change-password"),
    path("send-reset-password/", Send_Email_Rest_Password.as_view(), name="send-reset-password"),
    path("reset-password/<str:encoded_pk>/<str:token>/", ResetPasswordAPIView.as_view(), name="reset-password"),
    path("generate-otp/", GenerateOTPView.as_view(), name="generate-otp"),
    path("validate-otp/", ValidateOTPView.as_view(), name="validate-otp"),
    path("validate-user-login-otp/", ValidateOTP_UserLoginView.as_view(), name="validate-user-login-otp"),

]


urlpatterns += router.urls