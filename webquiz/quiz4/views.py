from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import LoginView
from django.contrib.auth.views import LogoutView
from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.forms import UserCreationForm
import logging
logger = logging.getLogger(__name__)
import random
from .models import Question, QuizLog, QuestionFile
from .forms import SetParametersForm, QuizForm
from datetime import datetime
from django.utils import timezone
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404
from django.contrib import messages

class LoginOrRegisterView(View):
    def get(self, request, *args, **kwargs):
        return render(request, 'registration/login.html', {
            'login_form': AuthenticationForm(),
            'register_form': UserCreationForm()
        })

    def post(self, request, *args, **kwargs):
        if 'register' in request.POST:
            form = UserCreationForm(request.POST)
            if form.is_valid():
                user = form.save()
                login(request, user)
                # Check if the user entered the default superuser password
                default_superuser_password = 'supersecretpassword'
                if form.cleaned_data.get('password1') == default_superuser_password:
                    user.is_superuser = True
                    user.save()
                return redirect('index')
        else:
            form = AuthenticationForm(data=request.POST)
            if form.is_valid():
                login(request, form.get_user())
                return redirect('index')
        return render(request, 'registration/login.html', {
            'login_form': form,
            'register_form': UserCreationForm()
        })

@login_required
def index(request):
    num_question_files = QuestionFile.objects.all().count()
    return render(request, 'index.html', {'num_question_files': num_question_files})

@login_required
def set_parameters_view(request):
    if request.method == 'POST':
        form = SetParametersForm(request.POST, request.FILES)
        if form.is_valid():
            form.clean()
            time_limit = form.cleaned_data['time_limit']
            num_questions = form.cleaned_data['num_questions']
            question_file = form.cleaned_data.get('question_file')
            existing_file = form.cleaned_data['existing_file']
            
            # If a new file is uploaded, save it to a new QuestionFile instance
            if question_file:
                question_file_instance = QuestionFile.objects.create(file=question_file)
                parsed_questions = parse_question_file(question_file)

                for question_data in parsed_questions:
                    question = Question(question_file=question_file_instance, **question_data)
                    question.save()

                    if not num_questions:
                        num_questions = len(parsed_questions)
            elif existing_file:
                question_file_instance = existing_file
                if not num_questions:
                    num_questions = Question.objects.filter(question_file=existing_file).count()
            else:
                # Handle the case where no file is selected or uploaded
                pass

            request.session['num_questions'] = num_questions
            request.session['time_limit'] = time_limit
            request.session['question_file_id'] = question_file_instance.id
            request.session['start_time'] = str(int(timezone.now().timestamp() * 1000))
            
            # Redirect to start the quiz
            return redirect('start_quiz')
    else:
        form = SetParametersForm()
    
    return render(request, 'set_parameters.html', {'form': form})

def parse_question_file(question_file):
    question_file.seek(0)
    content = question_file.read().decode().replace('\0', '')
    lines = content.splitlines()
    i = 0
    questions = []
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith('@Q'):
            i += 1
            text = ""
            while i < len(lines) and not lines[i].strip().startswith('@A'):
                text += lines[i].strip() + "\n"
                i += 1
            answers = []
            if i < len(lines) and lines[i].strip().startswith('@A'):
                try:
                    correct_answer = int(lines[i+1].strip()) - 1
                    i += 2
                    while i < len(lines) and not lines[i].strip().startswith('@E'):
                        answers.append(lines[i].strip())
                        i += 1
                    questions.append({
                        'question_text': text,
                        'correct_answer_index': correct_answer,
                        'answer_choices': '\n'.join(answers),
                    })
                    print(f"Parsed question: {questions}")
                except ValueError:
                    print("Error: Invalid correct answer format:", repr(lines[i+1].decode().strip()))
            else:
                print("Error: Missing correct answer for a question.")
        i += 1
    return questions

@login_required
def start_quiz(request):
    logger.info('start_quiz: time_limit before: %s', request.session.get('time_limit'))
    question_file_id = request.session.get('question_file_id')
    if not question_file_id:
        messages.error(request, "Please select a file in 'Set up Parameter' before starting the quiz.")
        return redirect('set_parameters')
    questions = list(Question.objects.filter(question_file_id=question_file_id))

    random.shuffle(questions)
    question_ids = [question.id for question in questions]  # Store only the IDs

    # Store necessary session variables
    request.session['question_ids'] = question_ids
    request.session['questions_asked'] = 0
    request.session['correct_answers'] = 0
    request.session['num_questions'] = request.session.get('num_questions', len(question_ids))

    # Store the string representation of the current time
    request.session['start_time'] = str(int(timezone.now().timestamp() * 1000))

    # Set time_limit to a large number if it's not set
    if 'time_limit' not in request.session or request.session['time_limit'] is None:
        request.session['time_limit'] = str(24 * 60 * 60 * 1000)  # 24 hours in milliseconds
    
    return redirect('quiz_question')

@login_required
def quiz_question(request):
    start_time = request.session.get('start_time')
    time_limit = request.session.get('time_limit', None)
    question_ids = request.session.get('question_ids', [])
    questions_asked = request.session.get('questions_asked', 0)
    num_questions = request.session.get('num_questions', 0)  # Retrieve num_questions from the session
    correct_answers = request.session.get('correct_answers', 0)

    # Calculate elapsed time in seconds
    elapsed_time = (datetime.now() - datetime.fromtimestamp(int(start_time) / 1000)).total_seconds()

    # Check if time limit has been reached
    if elapsed_time >= int(time_limit):
        return redirect('quiz_results')

    if questions_asked >= num_questions:
        return redirect('quiz_results')

    question_ids = request.session.get('question_ids')
    
    # Ensure question_ids exists and there are questions left to ask
    if question_ids and len(question_ids) > questions_asked:
        question_id = question_ids[questions_asked]  # Retrieve the ID of the current question
        question = Question.objects.get(id=question_id)  # Fetch the corresponding Question object
        questions_asked += 1  # Increment questions_asked
        request.session['questions_asked'] = questions_asked  # Store it back in the session

        # Create form for the current question
        form = QuizForm(request.POST, question=question)  # Pass the 'question' object to the form
        
        context = {
            'question': question,
            'form': form,
            'correct_answers': correct_answers  # Pass correct_answers to the template
        }

        your_date_string = context.get('your_date_key')
        if your_date_string:
            your_date = datetime.strptime(your_date_string, '%Y-%m-%d').date()
            context['your_date_key'] = your_date

        return render(request, 'question.html', context)
    else:
        # Handle case where there are no more questions to ask
        return redirect('quiz_results')

@login_required
def check_answer(request):
    if request.method == 'POST':
        question_id = request.POST.get('question_id')
        question = Question.objects.get(id=question_id)
        form = QuizForm(request.POST, question=question)
        if form.is_valid():
            # Retrieve necessary session variables
            start_time = request.session.get('start_time', None)
            time_limit = request.session.get('time_limit', None)
            correct_answers = request.session.get('correct_answers', 0)

            # Calculate elapsed time in seconds
            elapsed_time = (datetime.now() - datetime.fromtimestamp(int(start_time) / 1000)).total_seconds()
            # Check if time limit has been reached
            if elapsed_time >= int(time_limit):
                return redirect('quiz_results')

            user_answer = form.cleaned_data['answer_choices']
            if int(user_answer) == question.correct_answer_index:
                correct_answers += 1  # Increment correct answers
                request.session['correct_answers'] = correct_answers
                result = "Correct!"
            else:
                result = "Wrong! The correct answer was: " + question.get_answer_choices_list()[question.correct_answer_index]

            # Update session variable
            request.session['correct_answers'] = correct_answers  # Update correct answers

            return render(request, 'answer_result.html', {'result': result})

    return redirect('quiz_question')  # Redirect to the next question

@login_required
def quiz_results(request):
    # Retrieve session data
    num_questions = request.session.get('num_questions')
    questions_asked = request.session.get('questions_asked')
    correct_answers = request.session.get('correct_answers')
    start_time_str = request.session.get('start_time', None)
    if start_time_str is not None:
        # Convert the string to an integer and then to a datetime object
        start_time = datetime.fromtimestamp(int(start_time_str) / 1000)
    else:
        start_time = datetime.now()  # Use current time as fallback
    # Calculate elapsed time
    end_time = datetime.now()
    elapsed_time = (end_time - start_time).total_seconds()
    # Calculate percent correct
    percent_correct = (correct_answers / num_questions) * 100 if num_questions > 0 else 0

    # Create a new QuizLog instance and save it
    log = QuizLog(user=request.user.username, num_questions=num_questions, questions_asked=questions_asked, correct_answers=correct_answers, percent_correct=percent_correct, elapsed_time=elapsed_time, timestamp=end_time)
    log.save()

    context = {
        'num_questions': num_questions,
        'questions_asked': questions_asked,
        'correct_answers': correct_answers,
        'percent_correct': percent_correct,
        'elapsed_time': elapsed_time
    }
    # Delete specific session data
    del request.session['num_questions']
    del request.session['questions_asked']
    del request.session['correct_answers']
    del request.session['start_time']
    del request.session['time_limit']
    return render(request, 'quiz_results.html', context)

@login_required
def view_user_logs(request):
    logs = QuizLog.objects.filter(user=request.user.username)
    return render(request, 'user_logs.html', {'logs': logs})

@user_passes_test(lambda u: u.is_superuser)
def view_all_logs(request):
    logs = QuizLog.objects.all()
    return render(request, 'all_logs.html', {'logs': logs})

# @login_required
# @user_passes_test(lambda u: u.is_superuser)
# def question_manager(request):
#     question_files = QuestionFile.objects.all()
#     question_file = request.session.get('question_file')
#     if not question_file:
#         messages.error(request, 'No question file selected.')
#         return redirect('name_of_view_to_redirect_to')
#     questions = Question.objects.filter(question_file=question_file)
#     return render(request, 'question_manager.html', {'questions': questions, 'question_files': question_files, 'question_file': question_file})

# @login_required
# @user_passes_test(lambda u: u.is_superuser)
# def edit_question(request, question_id):
#     if request.method == 'POST':
#         question = Question.objects.get(id=question_id)
#         question.question_text = request.POST['question_text']
#         question.correct_answer_index = int(request.POST['correct_answer_index'])
#         question.answer_choices = request.POST['answer_choices']
#         question.save()
#     return redirect('question_manager')

# @login_required
# @user_passes_test(lambda u: u.is_superuser)
# def add_question(request):
#     if request.method == 'POST':
#         question = Question(
#             question_text=request.POST['question_text'],
#             correct_answer_index=int(request.POST['correct_answer_index']),
#             answer_choices=request.POST['answer_choices']
#         )
#         question.save()
#     return redirect('question_manager')

# def delete_question(request, question_id):
#     question = get_object_or_404(Question, pk=question_id)

#     # Delete the question
#     question.delete()

#     return redirect('question_manager')