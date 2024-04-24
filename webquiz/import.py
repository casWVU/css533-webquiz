import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'webquiz.settings')
django.setup()

from quiz4.models import Question

def parse_question_file(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()

    questions = []
    current_question = None
    for line_index, line in enumerate(lines):
        line = line.strip()
        if line.startswith('@Q'):
            if current_question:
                questions.append(current_question)
            current_question = {'question_text': "", 'correct_answer_index': None, 'answer_choices': ""}
        elif line.startswith('@A'):
            print(f"Processing '@A' line: {line}")  # Debug statement
            if line_index + 1 < len(lines):
                correct_answer_index_line = lines[line_index + 1].strip()
                if correct_answer_index_line.isdigit():
                    correct_answer_index = int(correct_answer_index_line) - 1
                    print("Correct answer index:", correct_answer_index)  # Debug statement
                    current_question['correct_answer_index'] = correct_answer_index
                else:
                    print("Error: No valid correct answer index found for a question.")
            else:
                print("Error: '@A' is not followed by a valid answer index line.")
        elif line.startswith('@E'):
            questions.append(current_question)
            current_question = None
        else:
            if current_question:
                if line:
                    if 'question_text' in current_question.keys():
                        current_question['question_text'] += line + '\n'
                    elif 'answer_choices' in current_question.keys():
                        current_question['answer_choices'] += line + '\n'

    # Save questions to the database
    for question_data in questions:
        try:
            Question.objects.create(
                question_text=question_data['question_text'].strip(),
                correct_answer_index=question_data['correct_answer_index'],
                answer_choices=question_data['answer_choices'].strip()
            )
        except Exception as e:
            print("Error while saving question to the database:", e)

if __name__ == "__main__":
    file_path = '/users/catherineswope/questions2.txt'
    parse_question_file(file_path)
