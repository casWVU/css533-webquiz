from django import forms
from django.core.exceptions import ValidationError
from .models import Question, QuestionFile
import os

class SetParametersForm(forms.Form):
    existing_file = forms.ModelChoiceField(
        queryset=QuestionFile.objects.none(), 
        required=False, 
        widget=forms.Select(attrs={'class': 'form-field'}), 
        help_text="Select an existing file from the dropdown or upload a new file below."
    )  
    question_file = forms.FileField(
        required=False, 
        widget=forms.FileInput(attrs={'class': 'form-field'}), 
    )  
    time_limit = forms.IntegerField(
        required=False, 
        widget=forms.NumberInput(attrs={'class': 'form-field'}), 
        help_text="Set an optional time limit for the quiz."
    )  
    num_questions = forms.IntegerField(
        required=False, 
        widget=forms.NumberInput(attrs={'class': 'form-field'}), 
        help_text="Set an optional number of questions for the quiz."
    )  

    def __init__(self, *args, **kwargs):
        super(SetParametersForm, self).__init__(*args, **kwargs)
        self.fields['existing_file'].queryset = QuestionFile.objects.all()

    def clean_time_limit(self):
        time_limit = self.cleaned_data.get('time_limit')
        if time_limit is not None and time_limit <= 0:
            raise forms.ValidationError("Time limit must be greater than 0.")
        return time_limit

    def clean_num_questions(self):
        num_questions = self.cleaned_data.get('num_questions')
        if num_questions is not None and num_questions <= 0:
            raise forms.ValidationError("Number of questions must be greater than 0.")
        return num_questions

    def clean_question_file(self):
        question_file = self.cleaned_data.get('question_file')

        # Check if a file was uploaded
        if question_file:
            # Check the file extension
            _, ext = os.path.splitext(question_file.name)
            if ext.lower() != '.txt':
                raise forms.ValidationError("Please upload a .txt file.")
            
            # Read the file's content
            content = question_file.read().decode('utf-8').splitlines()

            # Ignore lines that begin with an asterisk or are blank
            content = [line for line in content if line and not line.startswith('*')]

            # Count the number of questions
            num_questions = content.count('@Q')

            # Check the number of questions
            if num_questions > 10000:
                raise forms.ValidationError("The uploaded file exceeds the 10000 question limit.")

            # Check the structure of each question
            for i in range(num_questions):
                try:
                    # Find the indices of the markers for the current question
                    q_index = content.index('@Q', i)
                    a_index = content.index('@A', q_index)
                    e_index = content.index('@E', a_index)

                    # Check the number of lines for the question and the answers
                    if a_index - q_index > 11 or e_index - a_index > 11:
                        raise forms.ValidationError("A question or its answers exceed the maximum number of lines.")
                except ValueError:
                    raise forms.ValidationError("The uploaded file does not follow the required format.")

            return question_file
        
    def clean(self):
        cleaned_data = super().clean()
        existing_file = cleaned_data.get('existing_file')
        question_file = cleaned_data.get('question_file')

        if existing_file and question_file:
            raise forms.ValidationError(
                "Please only provide either an existing file or a question file, not both."
            )
        elif not existing_file and not question_file:
            raise forms.ValidationError(
                "Please provide either an existing file or a question file."
            )

        return cleaned_data
    
class QuestionsForm(forms.Form):
    question_text = forms.CharField()
    correct_answer_index = forms.IntegerField()
    answer_choices = forms.MultipleChoiceField()

    def __init__(self, *args, **kwargs):
        super(QuestionsForm, self).__init__(*args, **kwargs)

class QuizForm(forms.Form):
    def __init__(self, *args, **kwargs):
        question = kwargs.pop('question')
        super(QuizForm, self).__init__(*args, **kwargs)
        self.fields['answer_choices'] = forms.ChoiceField(choices=[(index, answer) for index, answer in enumerate(question.get_answer_choices_list())],
                                                          widget=forms.RadioSelect, label=question.question_text)

    answer_choices = forms.ChoiceField(widget=forms.RadioSelect)

