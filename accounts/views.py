from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, SetPasswordForm
from django.contrib.auth import login, logout, get_user_model
from django.contrib import messages
from django import forms
from django.urls import reverse
from django.core.mail import send_mail
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .models import PasswordResetCode

User = get_user_model()

ROLE_HIERARCHY = {
    'creator': 4,
    'admin': 3,
    'moder': 2,
    'helper': 1,
}

def get_role_level(user):
    return ROLE_HIERARCHY.get(getattr(user, 'role', 'helper'), 1)

def role_required(min_level):
    def decorator(view_func):
        def _wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('accounts:login')
            if get_role_level(request.user) < min_level:
                return HttpResponseForbidden('Недостаточно прав')
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator

class SignupForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Пользователь с таким email уже существует.")
        return email


def signup_view(request):
    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("/")
        messages.error(request, "Ошибка при регистрации. Проверьте данные.")
    else:
        form = SignupForm()
    return render(request, "accounts/signup.html", {"form": form})


def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect("/")
        messages.error(request, "Неверные данные для входа.")
    else:
        form = AuthenticationForm()
    return render(request, "accounts/login.html", {"form": form})


def logout_view(request):
    logout(request)
    return render(request, "accounts/logout.html")


def password_reset_request_view(request):
    if request.method == "POST":
        email = request.POST.get('email')
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            messages.error(request, "Пользователь с таким email не найден.")
            return redirect('accounts:password_reset')
        pr = PasswordResetCode.create_for_user(user)
        reset_link = request.build_absolute_uri(
            reverse('accounts:password_reset_verify') + f"?uid={user.pk}&code={pr.code}"
        )
        send_mail(
            subject="Сброс пароля — код подтверждения",
            message=f"Код для сброса пароля: {pr.code}\nИли перейди по ссылке: {reset_link}\nКод действителен 30 минут.",
            from_email=None,
            recipient_list=[user.email],
            fail_silently=False,
        )
        messages.success(request, "Код отправлен на email.")
        return redirect('accounts:password_reset')
    return render(request, "accounts/password_reset_request.html")


def password_reset_verify_view(request):
    uid = request.GET.get('uid') or request.POST.get('uid')
    code = request.GET.get('code') or request.POST.get('code')
    if request.method == "POST":
        uid = request.POST.get('uid')
        code = request.POST.get('code')
        user = get_object_or_404(User, pk=uid)
        pr = PasswordResetCode.objects.filter(user=user, code=code, used=False).order_by('-created_at').first()
        if not pr or pr.is_expired():
            messages.error(request, "Неверный или просроченный код.")
            return redirect('accounts:password_reset_verify')
        request.session['password_reset_user'] = user.pk
        request.session['password_reset_code'] = pr.code
        pr.mark_used()
        return redirect('accounts:password_reset_confirm')
    return render(request, "accounts/password_reset_verify.html", {"uid": uid, "code": code})


def password_reset_confirm_view(request):
    user_pk = request.session.get('password_reset_user')
    if not user_pk:
        messages.error(request, "Нет информации о сбросе пароля.")
        return redirect('accounts:password_reset')
    user = get_object_or_404(User, pk=user_pk)
    if request.method == "POST":
        form = SetPasswordForm(user, request.POST)
        if form.is_valid():
            form.save()
            request.session.pop('password_reset_user', None)
            request.session.pop('password_reset_code', None)
            messages.success(request, "Пароль успешно изменён.")
            return redirect('accounts:login')
    else:
        form = SetPasswordForm(user)
    return render(request, "accounts/password_reset_confirm.html", {"form": form})


@role_required(2)
def participants_view(request):
    users = User.objects.all().order_by('username')
    return render(request, 'participants.html', {'users': users})


@role_required(2)
@require_POST
def participant_action_view(request, user_id, action):
    target = get_object_or_404(User, pk=user_id)
    if get_role_level(request.user) <= get_role_level(target) and request.user != target:
        messages.error(request, 'Нельзя выполнять действие на пользователе с равной или высшей ролью.')
        return redirect('accounts:participants')

    if action == 'delete':
        target.delete()
        messages.success(request, f'Пользователь {target.username} удалён.')
    elif action == 'ban':
        target.is_active = False
        target.save()
        messages.success(request, f'Пользователь {target.username} забанен.')
    elif action == 'unban':
        target.is_active = True
        target.save()
        messages.success(request, f'Пользователь {target.username} разбанен.')
    else:
        messages.error(request, 'Неизвестное действие.')
    return redirect('accounts:participants')


@role_required(4)
@require_POST
def change_role_view(request, user_id):
    target = get_object_or_404(User, pk=user_id)
    new_role = request.POST.get('role')
    if new_role not in ROLE_HIERARCHY:
        messages.error(request, 'Неверная роль.')
        return redirect('accounts:participants')

    if get_role_level(request.user) <= get_role_level(target) and request.user != target:
        messages.error(request, 'Нельзя изменить роль у пользователя с равной или высшей ролью.')
        return redirect('accounts:participants')

    target.role = new_role
    target.save()
    messages.success(request, f'Роль пользователя {target.username} изменена на {new_role}.')
    return redirect('accounts:participants')
