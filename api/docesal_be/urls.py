from . import views
from django.urls import path


urlpatterns = [
    path("", views.getRoutes, name="getRoutes"),
    path("products/", views.ProductList.as_view(), name="product-list"),
    path("product/<int:pk>/", views.ProductDetail.as_view(), name="product-detail"),
    path(
        "users/login/", views.MyTokenObtainPairView.as_view(), name="token_obtain_pair"
    ),
    path("users/profile/", views.getUserProfile, name="getUserProfile"),
    path("users/", views.getUsers, name="getUsers"),
    path("users/register/", views.registerUser, name="registerUser"),
    path(
        "activate/<uidb64>/<token>/",
        views.ActivateAccountView.as_view(),
        name="activate",
    ),
    path(
        "users/token/verify/",
        views.TokenVerificationView.as_view(),
        name="token_verify",
    ),
    path("users/token/refresh/", views.refresh_token, name="token_refresh"),
    path(
        "users/refresh-token/", views.TokenRefreshView.as_view(), name="refresh_token"
    ),
]
