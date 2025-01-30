### Obter quiz

```python
from udemy_userAPI import Udemy
udemy  = Udemy()
course_id = 123456
lecture = 123456
details_course = udemy.get_details_course(course_id)
lecture_details = details_course.get_details_lecture(lecture_id=lecture)
if lecture_details.get_asset_type.lower() == 'quiz':
    print("Quiz!!")
    quiz_object = lecture_details.quiz_object() # Objeto Quiz()
    ### -- quiz data
    print("Tipo (str):",quiz_object.type_quiz)
    print("Id (int):",quiz_object.id)
    print("Duração (int):",quiz_object.duration)
    print("Porcentagem necessária (str):",quiz_object.pass_percent)
    print("Descrição (str):",quiz_object.description)
    print("Conteúdo (dict):",quiz_object.content())

```