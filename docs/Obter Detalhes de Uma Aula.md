
# Obter Detalhes de uma Aula Específica de um Curso na Udemy

## Pré-requisitos

- Biblioteca `udemy_userAPI` instalada e configurada.
- Credenciais de autenticação válidas para acessar a API da Udemy.
- IDs válidos para o curso e a aula que deseja consultar.

## Exemplo de Código

O código a seguir ilustra o processo de autenticação e obtenção de informações detalhadas de uma aula específica em um curso:

```python
import udemy_userAPI

# Inicializa o objeto principal da API Udemy
udemy = udemy_userAPI.Udemy()

# Configura a autenticação do usuário
auth = udemy_userAPI.UdemyAuth()

# Verifica se o login foi bem-sucedido
is_login = auth.verif_login()
if is_login:
    # Defina o ID do curso que você deseja consultar
    course_id = 1234  # Substitua pelo ID real do curso

    # Obtém os detalhes do curso
    course_infor = udemy.get_details_course(course_id=course_id)

    # Obtém a lista de aulas do curso
    lectures = course_infor.get_lectures
    # Defina o ID da aula específica
    lecture_id = 12345  # Substitua pelo ID real da aula

    # Obtém os detalhes da aula específica
    lecture_infor = course_infor.get_details_lecture(lecture_id=lecture_id)

    # Exibe as informações detalhadas da aula
    print(f"ID da Aula: {lecture_infor.get_lecture_id}")
    print(f"Descrição: {lecture_infor.get_description}")
    print(f"Fontes de Mídia: {lecture_infor.get_media_sources}")
    print(f"Aula é gratuita: {lecture_infor.is_free}")
    print(f"Tipo de Ativo: {lecture_infor.get_asset_type}")
    print(f"Legendas Disponíveis: {lecture_infor.get_captions}")
    print(f"URLs para Download: {lecture_infor.get_download_urls}")
    print(f"URL Externa: {lecture_infor.get_external_url}")
    print(f"URLs dos Slides: {lecture_infor.get_slide_urls}")
    print(f"Thumbnail: {lecture_infor.get_thumbnail}")
    print(f"Token de Licença de Mídia: {lecture_infor.get_media_license_token}")

    # Verifica se a aula está protegida por DRM e exibe a chave, se aplicável
    if lecture_infor.course_is_drmed():
        print(f"Esta aula possui DRM key: {lecture_infor.course_is_drmed().get_key_for_lesson()}")

else:
    print("Autenticação falhou. Verifique suas credenciais.")
```

## Explicação das Funções e Métodos Utilizados

- **`udemy.get_details_course(course_id)`**: Inicializa e retorna as informações do curso, utilizando o ID do curso fornecido.
- **`course_infor.get_lectures`**: Retorna a lista completa de aulas disponíveis no curso.
- **`course_infor.get_details_lecture(lecture_id)`**: Obtém e retorna os detalhes de uma aula específica com base no ID fornecido.
- **`lecture_infor.get_lecture_id`**: Retorna o ID único da aula.
- **`lecture_infor.get_description`**: Fornece uma descrição textual da aula.
- **`lecture_infor.get_media_sources`**: Lista as fontes de mídia utilizadas na aula, como vídeos e outros recursos.
- **`lecture_infor.is_free`**: Indica se a aula é gratuita ou se exige pagamento.
- **`lecture_infor.get_asset_type`**: Retorna o tipo de ativo associado à aula (por exemplo, vídeo, artigo, etc.).
- **`lecture_infor.get_captions`**: Fornece as legendas disponíveis para a aula em diferentes idiomas.
- **`lecture_infor.get_download_urls`**: Retorna URLs para download da aula, se aplicável.
- **`lecture_infor.get_external_url`**: Exibe uma URL externa associada à aula, se houver.
- **`lecture_infor.get_slide_urls`**: Lista URLs dos slides que acompanham a aula.
- **`lecture_infor.get_thumbnail`**: Retorna o URL da miniatura da aula.
- **`lecture_infor.get_media_license_token`**: Fornece o token de licença de mídia, útil para verificar direitos de uso.
- **`lecture_infor.course_is_drmed()`**: Verifica se a aula possui proteção DRM e, se aplicável, retorna a chave DRM.

## Tratamento de Erros Comuns

- **Falha na Autenticação**: Caso o login falhe, nenhuma informação será retornada. Verifique se as credenciais estão corretas e tente novamente.
- **ID de Curso ou Aula Inválido**: IDs inválidos podem resultar em erros ao tentar acessar os detalhes de um curso ou aula. Certifique-se de que o ID do curso e da aula correspondem aos dados reais na plataforma Udemy.
- **Proteção DRM**: Se a aula possui proteção DRM, pode ser necessário tratamento adicional para acesso ao conteúdo.

## Observações Importantes

- Substitua `course_id` e `lecture_id` pelos valores reais correspondentes ao curso e à aula de interesse.
- Verifique se você possui permissão para acessar a aula e o curso, especialmente em casos de conteúdo pago ou restrito.
  
