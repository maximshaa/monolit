import datetime

from django.db import models
from django.utils import timezone
from django.conf import settings


# Модель вопроса (пост с опросом)
class Question(models.Model):
    # Заголовок вопроса
    question_text = models.CharField(max_length=200)
    # Краткое описание для главной страницы
    short_description = models.CharField(max_length=255)
    # Полное описание вопроса
    description = models.TextField(default='')
    # Изображение (не обязательно
    image = models.ImageField(upload_to='question_image/', blank=True,
                              null=True)
    # Дата публикации
    pub_date = models.DateTimeField('date published')
    # Дата, до которой вопрос доступен
    expiration_date = models.DateTimeField('expiration date')

    def is_active(self):
        """Проверяет, что вопрос всё ещё активен (не истёк)"""
        return timezone.now() <= self.expiration_date

    def was_published_recently(self):
        """Проверяет, что вопрос опубликован недавно (за последние 24 часа)"""
        return self.pub_date >= timezone.now() - datetime.timedelta(days=1)

    def __str__(self):
        return self.question_text


# Модель варианта ответа для вопроса
class Choice(models.Model):
    # Связь с вопросом
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    # Текст варианта ответа
    choice_text = models.CharField(max_length=200)
    # Количество голосов за этот вариант
    votes = models.IntegerField(default=0)

    def __str__(self):
        return self.choice_text


# Модель голосования пользователя по вопросу
class Vote(models.Model):
    # Пользователь, оставивший голос
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    # Вопрос, по которому голосуют
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    # Выбранный вариант ответа
    choice = models.ForeignKey(Choice, on_delete=models.CASCADE)

    class Meta:
        # Гарантируем, что один пользователь может голосовать
        # только один раз по каждому вопросу
        unique_together = ('user', 'question')

    def __str__(self):
        return ''.join([f"{self.user.username} - ",
                        f"{self.question.question_text} - ",
                        f"{self.choice.choice_text}"])


# Модель профиля пользователя для хранения дополнительных данных
class UserProfile(models.Model):
    # Связь с встроенной моделью User
    user = models.OneToOneField(settings.AUTH_USER_MODEL,
                                on_delete=models.CASCADE)
    # Обязательный аватар
    avatar = models.ImageField(upload_to='avatars/')
    # Дополнительная информация о пользователе
    bio = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.user.username
