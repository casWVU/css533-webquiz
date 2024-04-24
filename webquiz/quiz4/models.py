from django.db import models

class QuestionFile(models.Model):
    file = models.FileField()
    
    def __str__(self):
        return self.file.name


class Question(models.Model):
    question_file = models.ForeignKey(QuestionFile, on_delete=models.CASCADE)
    question_text = models.TextField()
    correct_answer_index = models.IntegerField()
    answer_choices = models.TextField()

    def get_answer_choices_list(self):
        return self.answer_choices.split('\n')

    def __str__(self):
        return self.question_text[:300] + "..."

class QuizLog(models.Model):
    user = models.CharField(max_length=25)
    question_file = models.FileField()
    num_questions = models.IntegerField()
    questions_asked = models.IntegerField()
    correct_answers = models.IntegerField()
    percent_correct = models.FloatField()
    elapsed_time = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

    @classmethod
    def get_num_questions(cls):
        params = cls.objects.first()
        return params.num_questions if params else 0

class UserData(models.Model):
    superusers = models.TextField(default=dict)
    users = models.TextField(default=dict)
