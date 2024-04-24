from django.contrib import admin
from .models import Question, QuizLog, UserData, QuestionFile

admin.site.register(Question)
# admin.site.register(QuizLog)
admin.site.register(UserData)
admin.site.register(QuestionFile)

# Define the admin class
class QuizLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'num_questions', 'questions_asked', 'correct_answers', 'percent_correct', 'elapsed_time', 'timestamp')

# Register the admin class with the associated model
admin.site.register(QuizLog, QuizLogAdmin)
