from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.template import loader
from django.forms import inlineformset_factory
from django.urls import reverse
from django.views import generic
from django.utils import timezone

from .models import Question, Choice, Vote
from .forms import (UserRegisterForm, UserEditForm, UserProfileEditForm,
                    QuestionForm)


# Представление для главной страницы со списком вопросов
class IndexView(generic.ListView):
    template_name = 'polls/index.html'
    context_object_name = 'latest_question_list'

    def get_queryset(self):
        qs = Question.objects.order_by('-pub_date')
        # Если пользователь не администратор,
        # показываем только активные вопросы
        if not (self.request.user.is_staff or self.request.user.is_superuser):
            qs = qs.filter(expiration_date__gte=timezone.now())
        return qs


# Представление для детального просмотра вопроса
class DetailView(generic.DetailView):
    model = Question
    template_name = 'polls/detail.html'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        # Если срок действия вопроса истёк и пользователь
        # не администратор, выдаем 404
        if self.object.expiration_date < timezone.now() and not request.user.is_staff:
            raise Http404("Вопрос недоступен")
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)


# Представление для отображения результатов голосования
class ResultsView(generic.DetailView):
    model = Question
    template_name = 'polls/results.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        question = self.get_object()
        choices = question.choice_set.all()
        total_votes = sum(choice.votes for choice in choices)
        # Вычисляем процент голосов для каждого варианта
        percentages = {}
        for choice in choices:
            if total_votes > 0:
                percentages[choice.id] = round((choice.votes / total_votes) * 100, 2)
            else:
                percentages[choice.id] = 0
        context['percentages'] = percentages
        context['total_votes'] = total_votes
        return context


# Функция голосования, доступна только авторизованным пользователям
@login_required
def vote(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    if request.method == 'POST':
        # Проверяем, голосовал ли уже пользователь по данному вопросу
        if Vote.objects.filter(user=request.user, question=question).exists():
            return render(request, 'polls/detail.html', {
                'question': question,
                'error_message': 'Вы уже голосовали по этому вопросу.'
            })
        try:
            # Получаем выбранный вариант ответа
            selected_choice = question.choice_set.get(pk=request.POST['choice'])
        except (KeyError, Choice.DoesNotExist):
            # Если вариант не выбран или не существует, выводим сообщение об ошибке
            return render(request, 'polls/detail.html', {
                'question': question,
                'error_message': 'Вы не сделали выбор.'
            })
        else:
            # Создаем запись голосования и увеличиваем счетчик голосов выбранного варианта
            Vote.objects.create(user=request.user, question=question, choice=selected_choice)
            selected_choice.votes += 1
            selected_choice.save()
            return HttpResponseRedirect(reverse('polls:results', args=(question.id,)))
    else:
        return HttpResponseRedirect(reverse('polls:detail', args=(question.id,)))


# Функция регистрации нового пользователя
def register(request):
    if request.method == 'POST':
        # Обработка данных формы регистрации, включая загрузку файлов
        form = UserRegisterForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()  # Создание пользователя и профиля
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            # Аутентификация и автоматический вход после регистрации
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            return redirect('polls:index')
    else:
        form = UserRegisterForm()
    return render(request, 'polls/register.html', {'form': form})


# Функция для отображения профиля текущего пользователя
@login_required
def profile(request):
    return render(request, 'polls/profile.html', {
        'user': request.user,
        'profile': request.user.userprofile
    })


# Функция редактирования профиля (данных пользователя и профиля)
@login_required
def edit_profile(request):
    if request.method == 'POST':
        user_form = UserEditForm(request.POST, instance=request.user)
        profile_form = UserProfileEditForm(request.POST, request.FILES, instance=request.user.userprofile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()       # Сохранение изменений в модели User
            profile_form.save()    # Сохранение изменений в модели UserProfile
            return redirect('polls:profile')
    else:
        user_form = UserEditForm(instance=request.user)
        profile_form = UserProfileEditForm(instance=request.user.userprofile)
    return render(request, 'polls/edit_profile.html', {
        'user_form': user_form,
        'profile_form': profile_form
    })


# Функция удаления профиля; удаляется сам пользователь
@login_required
def delete_profile(request):
    if request.method == 'POST':
        request.user.delete()  # Удаление пользователя (и связанного профиля)
        return redirect('polls:index')
    return render(request, 'polls/delete_profile.html')


# Функция создания вопроса с вариантами ответов с использованием inline formset
@login_required
def create_question(request):
    # Создаем formset для модели Choice, связанных с моделью Question
    ChoiceFormSet = inlineformset_factory(
        Question,
        Choice,
        fields=('choice_text',),
        extra=5,         # Количество дополнительных пустых форм
        can_delete=True  # Разрешаем удаление вариантов
    )

    if request.method == 'POST':
        form = QuestionForm(request.POST, request.FILES)
        if form.is_valid():
            # Сохраняем вопрос без сохранения в БД,
            # чтобы добавить дату публикации
            question = form.save(commit=False)
            question.pub_date = timezone.now()  # Устанавливаем текущую дату
            question.save()  # Сохраняем вопрос
            # Привязываем formset к созданному вопросу
            formset = ChoiceFormSet(request.POST, instance=question)
            if formset.is_valid():
                formset.save()  # Сохраняем варианты ответов
                return redirect('polls:index')
        else:
            # Если данные формы не валидны, создаем formset с переданными данными
            formset = ChoiceFormSet(request.POST, instance=Question())
    else:
        form = QuestionForm()
        # Для GET-запроса создаем пустой formset
        formset = ChoiceFormSet(instance=Question())
    return render(request, 'polls/create_question.html', {'form': form, 'formset': formset})
