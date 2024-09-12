# Obter Detalhes de uma Aula

Este exemplo demonstra como obter os detalhes de uma aula específica de um curso na Udemy.

Para obter detalhes de uma aula específica de um curso, siga o exemplo abaixo:

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

    # Obtém os detalhes de uma aula do curso
    course_infor = udemy.get_details_course(course_id=course_id)
    
    # Obtém a lista de aulas do curso
    lectures = course_infor.get_lectures
    
    # Defina o ID da aula específica
    lecture_id = 12345  # Substitua pelo ID real da aula
    
    # Obtém os detalhes da aula específica
    lecture_infor = course_infor.get_details_lecture(lecture_id=lecture_id)
    
    # Exibe as informações da aula
    print(f"ID da Aula: {lecture_infor.get_lecture_id}")
    print(f"Descrição: {lecture_infor.get_description}")
    print(f"Curso possui DRM: {lecture_infor.course_is_drmed}")
    print(f"Fontes de Mídia: {lecture_infor.get_media_sources}")
    print(f"Aula é gratuita: {lecture_infor.is_free}")
    print(f"Tipo de Ativo: {lecture_infor.get_asset_type}")
    print(f"Legendas Disponíveis: {lecture_infor.get_captions}")
    print(f"URLs para Download: {lecture_infor.get_download_urls}")
    print(f"URL Externa: {lecture_infor.get_external_url}")
    print(f"URLs dos Slides: {lecture_infor.get_slide_urls}")
    print(f"Thumbnail: {lecture_infor.get_thumbnail}")
    print(f"Token de Licença de Mídia: {lecture_infor.get_media_license_token}")
    
else:
    print("Não está logado...")
```

## Explicação

- `udemy.get_details_course(course_id)`: Obtém os detalhes do curso usando o ID fornecido.
- `course_infor.get_lectures`: Retorna a lista de aulas do curso.
- `course_infor.get_details_lecture(lecture_id)`: Obtém os detalhes da aula usando o ID da aula.
- `lecture_infor.get_lecture_id`: Retorna o ID da aula.
- `lecture_infor.get_description`: Retorna a descrição da aula.
- `lecture_infor.course_is_drmed`: Indica se o curso está protegido por DRM.
- `lecture_infor.get_media_sources`: Retorna as fontes de mídia da aula.
- `lecture_infor.is_free`: Indica se a aula é gratuita.
- `lecture_infor.get_asset_type`: Retorna o tipo de ativo da aula.
- `lecture_infor.get_captions`: Retorna as legendas disponíveis para a aula.
- `lecture_infor.get_download_urls`: Retorna os URLs de download da aula.
- `lecture_infor.get_external_url`: Retorna um URL externo, se houver.
- `lecture_infor.get_slide_urls`: Retorna os URLs dos slides associados à aula.
- `lecture_infor.get_thumbnail`: Retorna o URLs de imagems em miniatura da aula.
- `lecture_infor.get_media_license_token`: Retorna o token de licença de mídia, se houver.

## Erros Possíveis

- **Não está logado**: Caso o usuário não esteja autenticado corretamente, a função não acessará os detalhes da aula. Verifique as credenciais de autenticação.
- **ID de aula inválido**: Certifique-se de que o ID da aula seja válido para o curso selecionado.

