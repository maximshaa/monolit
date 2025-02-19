from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils.translation import gettext as _

from .models import UserProfile, Question


# Форма регистрации нового пользователя с дополнительными полями для профиля
class UserRegisterForm(UserCreationForm):
    # Обязательное поле для email
    email = forms.EmailField(required=True)
    # Обязательный аватар
    avatar = forms.ImageField(label=_("Аватар"), required=True)
    # Поле для описания (не обязательно)
    bio = forms.CharField(label=_("Био"),
                          widget=forms.Textarea,
                          required=False)

    class Meta:
        model = User
        # Поля, отображаемые в форме регистрации
        fields = ['username', 'email', 'password1', 'password2', 'avatar',
                  'bio']

    def save(self, commit=True):
        # Сохраняем данные формы через базовую реализацию UserCreationForm
        user = super().save(commit)
        # Получаем дополнительные поля из очищенных данных
        avatar = self.cleaned_data.get('avatar')
        bio = self.cleaned_data.get('bio', '')
        # Создаём профиль пользователя, связывая его с созданным пользователем
        UserProfile.objects.create(user=user, avatar=avatar, bio=bio)
        return user


# Форма редактирования данных профиля (аватар и био)
class UserProfileEditForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['avatar', 'bio']


# Форма редактирования данных пользователя (имя, email, имя и фамилия)
class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']


# Форма создания/редактирования вопроса с вариантами ответов
class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['question_text', 'short_description', 'description', 'image',
                  'expiration_date']
        # Виджет для выбора даты и времени,
        # использующий input типа datetime-local
        widgets = {
            'expiration_date': forms.DateTimeInput(
                attrs={'type': 'datetime-local'}),
        }
