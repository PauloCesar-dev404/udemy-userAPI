## Obter legendas
```python
from udemy_userAPI import Udemy
udemy  = Udemy()
course_id = 123456
lecture = 123456
details_course = udemy.get_details_course(course_id)
lecture_details = details_course.get_details_lecture(lecture_id=lecture)
captions_langs = lecture_details.get_captions.languages() # lista de dict com os idiomas disponíveis
#[{'locale_id': 'pt_BR', 'locale': 'Português [Automático]'}]

caption = lecture_details.get_captions.get_lang(locale_id='pt_BR') # supondo que a aula tem o idioma pt_BR disponivel
print("Id da legenda:",caption.id)
print("Url:",caption.url)
print("Título:",caption.title)
print("Status:",caption.status)
print("Idioma:",caption.locale)
print("Conteúdo da legenda:",caption.content)
print("Data de criação:",caption.created)



```