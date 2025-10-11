from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("signup/", views.signup_view, name="signup"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    path("password-reset/", views.password_reset_request_view, name="password_reset"),
    path("password-reset/verify/", views.password_reset_verify_view, name="password_reset_verify"),
    path("password-reset/confirm/", views.password_reset_confirm_view, name="password_reset_confirm"),
]

urlpatterns += [
    path('participants/', views.participants_view, name='participants'),
    path('participants/action/<int:user_id>/<str:action>/', views.participant_action_view, name='participant_action'),
    path('participants/change-role/<int:user_id>/', views.change_role_view, name='change_role'),
]
