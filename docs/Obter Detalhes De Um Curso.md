# Obter Detalhes de um Curso

Este exemplo demonstra como obter os detalhes de um curso na Udemy após verificar se o usuário está logado.

## Pré-requisitos

- Biblioteca `udemy_userAPI` instalada e configurada.
- Autenticação válida para a Udemy.

## Exemplo de Código

Para obter detalhes de um curso específico, siga o exemplo abaixo:

```python
import udemy_userAPI

# Instancia o objeto principal da API Udemy
udemy = udemy_userAPI.Udemy()

# Autenticação do usuário
auth = udemy_userAPI.UdemyAuth()

# Verifica se o login foi bem-sucedido
is_login = auth.verif_login

if is_login:
    # Defina o ID do curso que você deseja obter informações
    course_id = 1234  # Substitua pelo ID real do curso

    # Obtém os detalhes do curso
    course_infor = udemy.get_details_course(course_id=course_id)

    # Exibe as informações do curso
    print(f"Título do Curso: {course_infor.title_course}")
    print(f"Idioma: {course_infor.locale}")
    print(f"Número de Aulas: {course_infor.get_lectures}")
    print(f"Instrutores: {course_infor.instructors}")
    print(f"Arquivos Adicionais: {course_infor.get_additional_files}")
    print(f"Títulos dos Vídeos: {course_infor.title_videos}")
    print(f"Número de Capítulos: {course_infor.count_chapters}")
    print(f"Número de Aulas: {course_infor.count_lectures}")
    print(f"Categoria Principal: {course_infor.primary_category}")
    print(f"Subcategoria Principal: {course_infor.primary_subcategory}")

else:
    print("Não está logado...")
```

## Explicação

- `udemy.get_details_course(course_id)`: Obtém os detalhes do curso usando o ID fornecido.
- `course_infor.title_course`: Retorna o título do curso.
- `course_infor.locale`: Retorna o idioma do curso.
- `course_infor.get_lectures`: Retorna o número total de aulas do curso.
- `course_infor.instructors`: Lista os instrutores do curso.
- `course_infor.get_additional_files`: Retorna a lista de arquivos adicionais anexados ao curso.
- `course_infor.title_videos`: Lista os títulos dos vídeos do curso.
- `course_infor.count_chapters`: Retorna o número de capítulos do curso.
- `course_infor.count_lectures`: Retorna o número de aulas do curso.
- `course_infor.primary_category`: Retorna a categoria principal do curso.
- `course_infor.primary_subcategory`: Retorna a subcategoria principal do curso.

## Erros Possíveis

- **Não está logado**: Caso o usuário não esteja autenticado corretamente, a função não acessará os detalhes do curso. Verifique as credenciais de autenticação.
