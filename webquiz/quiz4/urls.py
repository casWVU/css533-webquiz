from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView
from .views import LoginOrRegisterView, view_user_logs, view_all_logs
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('login/', LoginOrRegisterView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path("", views.index, name="index"),
    path('set_parameters/', views.set_parameters_view, name='set_parameters'),
    path('start_quiz/', views.start_quiz, name='start_quiz'),
    path('quiz_question/', views.quiz_question, name='quiz_question'),
    path('check_answer/', views.check_answer, name='check_answer'),
    path('quiz_results/', views.quiz_results, name='quiz_results'),
    path('logs/user/', view_user_logs, name='user_logs'),
    path('logs/all/', view_all_logs, name='all_logs'),
#     path('question_manager/', views.question_manager, name='question_manager'),
#     path('edit_question/<int:question_id>/', views.edit_question, name='edit_question'),
#     path('add_question/', views.add_question, name='add_question'),
#     path('delete_question/<int:question_id>/', views.delete_question, name='delete_question'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
