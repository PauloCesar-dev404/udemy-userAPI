import json
import hashlib
import hmac
import math
from datetime import datetime
from .exeptions import UdemyUserApiExceptions, UnhandledExceptions, LoginException
from .authenticate import UdemyAuth
import os.path
from pywidevine.cdm import Cdm
from pywidevine.device import Device
from pywidevine.pssh import PSSH
import requests
import base64


AUTH = UdemyAuth()
COOKIES = AUTH._load_cookies()

HEADERS_USER = {
    "accept": "*/*",
    "accept-language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    "cache-control": "no-cache",
    "Content-Type": "text/plain",
    "pragma": "no-cache",
    "sec-ch-ua": "\"Chromium\";v=\"118\", \"Google Chrome\";v=\"118\", \"Not=A?Brand\";v=\"99\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\"",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "cross-site",
    "Cookie": COOKIES,
    "Referer": "https://www.udemy.com/"}
HEADERS_octet_stream = {
    'authority': 'www.udemy.com',
    'pragma': 'no-cache',
    'cache-control': 'no-cache',
    'sec-ch-ua': '" Not;A Brand";v="99", "Google Chrome";v="97", "Chromium";v="97"',
    'accept': 'application/json, text/plain, */*',
    "Cookie": COOKIES,
    'dnt': '1',
    'content-type': 'application/octet-stream',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'origin': 'https://www.udemy.com',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-mode': 'cors',
    'sec-fetch-dest': 'empty',
    'accept-language': 'en-US,en;q=0.9',
}

locate = os.path.dirname(__file__)
WVD_FILE_PATH = os.path.join(locate, 'mpd_analyzer', 'bin.wvd')
device = Device.load(WVD_FILE_PATH)
cdm = Cdm.from_device(device)


def read_pssh_from_bytes(bytess):
    pssh_offset = bytess.rfind(b'pssh')
    _start = pssh_offset - 4
    _end = pssh_offset - 4 + bytess[pssh_offset - 1]
    pssh = bytess[_start:_end]
    return pssh


def get_pssh(init_url):
    from .authenticate import UdemyAuth
    auth = UdemyAuth()
    if not auth.verif_login():
        raise LoginException("Sessão expirada!")
    res = requests.get(init_url, headers=HEADERS_octet_stream)
    if not res.ok:
        return
    pssh = read_pssh_from_bytes(res.content)
    return base64.b64encode(pssh).decode("utf-8")


def get_highest_resolution(resolutions):
    """
    Retorna a maior resolução em uma lista de resoluções.

    Args:
        resolutions (list of tuple): Lista de resoluções, onde cada tupla representa (largura, altura).

    Returns:
        tuple: A maior resolução em termos de largura e altura.
    """
    if not resolutions:
        return None
    return max(resolutions, key=lambda res: (res[0], res[1]))


def organize_streams(streams):
    if not streams:
        return {}
    organized_streams = {
        'dash': [],
        'hls': []
    }

    best_video = None

    for stream in streams:
        # Verifica e adiciona streams DASH
        if stream['type'] == 'application/dash+xml':
            organized_streams['dash'].append({
                'src': stream['src'],
                'label': stream.get('label', 'unknown')
            })

        # Verifica e adiciona streams HLS (m3u8)
        elif stream['type'] == 'application/x-mpegURL':
            organized_streams['hls'].append({
                'src': stream['src'],
                'label': stream.get('label', 'auto')
            })

        # Verifica streams de vídeo (mp4)
        elif stream['type'] == 'video/mp4':
            # Seleciona o vídeo com a maior resolução (baseado no label)
            if best_video is None or int(stream['label']) > int(best_video['label']):
                best_video = {
                    'src': stream['src'],
                    'label': stream['label']
                }

    # Adiciona o melhor vídeo encontrado na lista 'hls'
    if best_video:
        organized_streams['hls'].append(best_video)

    return organized_streams


def extract(pssh, license_token):
    from .authenticate import UdemyAuth
    auth = UdemyAuth()
    if not auth.verif_login():
        raise LoginException(
            "Sessão expirada!")
    license_url = (f"https://www.udemy.com/api-2.0/media-license-server/validate-auth-token?drm_type=widevine"
                   f"&auth_token={license_token}")
    session_id = cdm.open()
    challenge = cdm.get_license_challenge(session_id, PSSH(pssh))
    license_file = requests.post(license_url, headers=HEADERS_octet_stream, data=challenge)
    try:
        str(license_file.content, "utf-8")
    except Exception as e:
        base64.b64encode(license_file.content).decode()
    else:
        if "CAIS" not in license_file.text:
            return
    cdm.parse_license(session_id, license_file.content)
    final_keys = ""
    for key in cdm.get_keys(session_id):
        if key.type == "CONTENT":
            final_keys += f"{key.kid.hex}:{key.key.hex()}"
    cdm.close(session_id)

    if final_keys == "":
        return
    return final_keys.strip()


def get_mpd_file(mpd_url):
    from .authenticate import UdemyAuth
    auth = UdemyAuth()
    if not auth.verif_login():
        raise LoginException("Sessão expirada!")
    try:
        # Faz a solicitação GET com os cabeçalhos
        response = requests.get(mpd_url, headers=HEADERS_USER)
        # Exibe o código de status
        if response.status_code == 200:
            return response.text
        else:
            raise UnhandledExceptions(f"erro ao obter dados de aulas!! {response.status_code}")
    except requests.ConnectionError as e:
        raise UdemyUserApiExceptions(f"Erro de conexão: {e}")
    except requests.Timeout as e:
        raise UdemyUserApiExceptions(f"Tempo de requisição excedido: {e}")
    except requests.TooManyRedirects as e:
        raise UdemyUserApiExceptions(f"Limite de redirecionamentos excedido: {e}")
    except requests.HTTPError as e:
        raise UdemyUserApiExceptions(f"Erro HTTP: {e}")
    except Exception as e:
        raise UnhandledExceptions(f"Errro Ao Obter Mídias:{e}")


def parser_chapters(results) -> list[dict]:
    """
    Processa os dados do curso e retorna uma lista de capítulos com suas aulas e quizzes.

    Se os resultados não contiverem capítulos (i.e. apenas aulas ou quizzes), todas as
    aulas/quizzes serão agrupadas em um capítulo padrão.

    Args:
        results (dict): Dicionário com os resultados do curso, normalmente contendo a chave 'results'.

    Returns:
        list[dict]: Lista de capítulos, cada um com título, índice (se disponível) e lista de lectures/quizzes.

    Raises:
        UdemyUserApiExceptions: Se não for possível obter os detalhes do curso.
    """
    if not results:
        raise UdemyUserApiExceptions("Não foi possível obter detalhes do curso!")

    items = results.get('results', [])
    chapters_dicts = []  # Lista de capítulos
    current_chapter = None  # Capítulo atual

    # Nome padrão para o grupo quando não houver capítulos
    default_chapter_title = "CourseFiles"

    for dictionary in items:
        _class = dictionary.get('_class')
        chapter_index = dictionary.get('object_index', None)

        if _class == 'chapter':
            # Se já há um capítulo em andamento, adiciona-o à lista
            if current_chapter:
                chapters_dicts.append(current_chapter)
            # Inicia um novo capítulo
            current_chapter = {
                'title': dictionary.get('title', 'Sem Título'),
                'chapter_index': chapter_index,
                'lectures': []  # Lista para armazenar aulas e quizzes
            }
        elif _class in ('lecture', 'quiz'):
            # Se não houver um capítulo atual, cria um capítulo padrão
            if current_chapter is None:
                current_chapter = {
                    'title': default_chapter_title,
                    'chapter_index': None,
                    'lectures': []
                }
            # Processa a aula ou quiz
            if _class == 'lecture':
                asset = dictionary.get('asset')
                if asset:
                    lecture_data = {
                        'asset_type': asset.get('asset_type', ''),
                        'title': dictionary.get('title', 'Aula'),
                        'lecture_id': dictionary.get('id', ''),
                        'asset_id': asset.get('id', '')
                    }
                    current_chapter['lectures'].append(lecture_data)
            elif _class == 'quiz':
                quiz_data = {
                    'asset_type': 'quiz',
                    'title': dictionary.get('title', 'Quiz'),
                    'lecture_id': dictionary.get('id', ''),
                    'type': dictionary.get('type', ''),
                    'asset_id': ''
                }
                current_chapter['lectures'].append(quiz_data)

    # Se houver um capítulo em andamento, adiciona-o à lista
    if current_chapter:
        chapters_dicts.append(current_chapter)

    return chapters_dicts


def get_add_files(course_id: int):
    """
    Obtém arquivos adicionais de um curso.

    Args:
        course_id (int): ID do curso.

    Returns:
        dict: Um dicionário contendo os arquivos adicionais do curso.

    Raises: LoginException: Se a sessão estiver expirada. UdemyUserApiExceptions: Se houver erro de conexão,
    tempo de requisição excedido, limite de redirecionamentos excedido ou erro HTTP. UnhandledExceptions: Se houver
    erro ao obter dados das aulas.
    """
    from .authenticate import UdemyAuth
    auth = UdemyAuth()
    if not auth.verif_login():
        raise LoginException("Sessão expirada!")
    url = (f'https://www.udemy.com/api-2.0/courses/{course_id}/subscriber-curriculum-items/?page_size=2000&fields['
           f'lecture]=title,object_index,is_published,sort_order,created,asset,supplementary_assets,is_free&fields['
           f'quiz]=title,object_index,is_published,sort_order,type&fields[practice]=title,object_index,is_published,'
           f'sort_order&fields[chapter]=title,object_index,is_published,sort_order&fields[asset]=title,filename,'
           f'asset_type,status,time_estimation,is_external&caching_intent=True')
    try:
        # Faz a solicitação GET com os cabeçalhos
        response = requests.get(url, headers=HEADERS_USER)
        data = []
        # Exibe o código de status
        if response.status_code == 200:
            a = json.loads(response.text)
            return a
        else:
            raise UnhandledExceptions(f"Erro ao obter dados de aulas! Código de status: {response.status_code}")

    except requests.ConnectionError as e:
        raise UdemyUserApiExceptions(f"Erro de conexão: {e}")
    except requests.Timeout as e:
        raise UdemyUserApiExceptions(f"Tempo de requisição excedido: {e}")
    except requests.TooManyRedirects as e:
        raise UdemyUserApiExceptions(f"Limite de redirecionamentos excedido: {e}")
    except requests.HTTPError as e:
        raise UdemyUserApiExceptions(f"Erro HTTP: {e}")
    except Exception as e:
        raise UnhandledExceptions(f"Erro ao obter mídias: {e}")


def get_files_aule(lecture_id_filter, data: list):
    """
    Filtra e obtém arquivos adicionais para uma aula específica.

    Args:
        lecture_id_filter: ID da aula a ser filtrada.
        data (list): Lista de dados contendo informações dos arquivos.

    Returns:
        list: Lista de arquivos filtrados.
    """
    files = []
    for files_data in data:
        lecture_id = files_data.get('lecture_id')
        if lecture_id == lecture_id_filter:
            files.append(files_data)
    return files


def get_links(course_id: int, id_lecture: int):
    """
    Obtém links e informações de uma aula específica.

    Args:
        course_id (int): ID do curso.
        id_lecture (int): ID da aula.

    Returns:
        dict: Um dicionário contendo links e informações da aula.

    Raises: LoginException: Se a sessão estiver expirada. UdemyUserApiExceptions: Se houver erro de conexão,
    tempo de requisição excedido, limite de redirecionamentos excedido ou erro HTTP. UnhandledExceptions: Se houver
    erro ao obter dados das aulas.
    """
    get = (f"https://www.udemy.com/api-2.0/users/me/subscribed-courses/{course_id}/lectures/{id_lecture}/?"
               f"fields[lecture]"
               f"=asset,description,download_url,is_free,last_watched_second&fields[asset]=asset_type,length,"
               f"media_license_token,course_is_drmed,media_sources,captions,thumbnail_sprite,slides,slide_urls,"
               f"download_urls,"
               f"external_url&q=0.3108014137011559/?fields[asset]=download_urls")
    from .authenticate import UdemyAuth
    auth = UdemyAuth()
    if not auth.verif_login():
        raise LoginException("Sessão expirada!")
    try:
        # Faz a solicitação GET com os cabeçalhos
        response = requests.get(get, headers=HEADERS_USER)
        data = []
        # Exibe o código de status
        if response.status_code == 200:
            a = json.loads(response.text)
            return a
        else:
            raise UnhandledExceptions(
                f"Erro ao obter dados da aula! Código de status: {response.status_code}")

    except requests.ConnectionError as e:
        raise UdemyUserApiExceptions(
            f"Erro de conexão: {e}")
    except requests.Timeout as e:
        raise UdemyUserApiExceptions(
            f"Tempo de requisição excedido: {e}")
    except requests.TooManyRedirects as e:
        raise UdemyUserApiExceptions(
            f"Limite de redirecionamentos excedido: {e}")
    except requests.HTTPError as e:
        raise UdemyUserApiExceptions(
            f"Erro HTTP: {e}")
    except Exception as e:
        raise UnhandledExceptions(
            f"Erro ao obter mídias: {e}")

def get_assessments(course_id: int,lecture_id:int):
    get = (f'https://www.udemy.com/api-2.0/users/me/subscribed-courses/{course_id}/quizzes/{lecture_id}/?draft='
           f'false&fields[quiz]=id,type,title,description,object_index,num_assessments,version,duration,'
           f'is_draft,pass_percent,changelog')
    from .authenticate import UdemyAuth
    auth = UdemyAuth()
    if not auth.verif_login():
        raise LoginException("Sessão expirada!")
    try:
        # Faz a solicitação GET com os cabeçalhos
        response = requests.get(get, headers=HEADERS_USER)
        data = []
        # Exibe o código de status
        if response.status_code == 200:
            a = json.loads(response.text)
            return a
        else:
            raise ConnectionError(
                f"Erro ao obter dados da aula! Código de status: {response.status_code}\n"
                f"{response.text}"
            )

    except requests.ConnectionError as e:
        raise UdemyUserApiExceptions(
            f"Erro de conexão: {e}")
    except requests.Timeout as e:
        raise UdemyUserApiExceptions(
            f"Tempo de requisição excedido: {e}")
    except requests.TooManyRedirects as e:
        raise UdemyUserApiExceptions(
            f"Limite de redirecionamentos excedido: {e}")
    except requests.HTTPError as e:
        raise UdemyUserApiExceptions(
            f"Erro HTTP: {e}")


def get_quizzes(lecture_id:int):
    get = (f'https://www.udemy.com/api-2.0/quizzes/{lecture_id}/assessments/?version=1&page_size=1000&fields[assessment]'
           f'=id,assessment_type,prompt,correct_response,section,question_plain,related_lectures&use_remote_version=true'
           )
    from .authenticate import UdemyAuth
    auth = UdemyAuth()
    if not auth.verif_login():
        raise LoginException("Sessão expirada!")
    try:
        # Faz a solicitação GET com os cabeçalhos
        response = requests.get(get, headers=HEADERS_USER)
        data = []
        # Exibe o código de status
        if response.status_code == 200:
            a = json.loads(response.text)
            return a
        else:
            raise UnhandledExceptions(
                f"Erro ao obter dados da aula! Código de status: {response.status_code}")

    except requests.ConnectionError as e:
        raise UdemyUserApiExceptions(
            f"Erro de conexão: {e}")
    except requests.Timeout as e:
        raise UdemyUserApiExceptions(
            f"Tempo de requisição excedido: {e}")
    except requests.TooManyRedirects as e:
        raise UdemyUserApiExceptions(
            f"Limite de redirecionamentos excedido: {e}")
    except requests.HTTPError as e:
        raise UdemyUserApiExceptions(
            f"Erro HTTP: {e}")
    except Exception as e:
        raise UnhandledExceptions(
            f"Erro ao obter mídias: {e}")


def remove_tag(d: str):
    new = d.replace("<p>", '').replace("</p>", '').replace('&nbsp;', ' ')
    return new


def get_external_liks(course_id: int, id_lecture, asset_id):
    """
    Obtém links externos para um asset específico de uma aula.

    Args:
        course_id (int): ID do curso.
        id_lecture: ID da aula.
        asset_id: ID do asset.

    Returns:
        dict: Um dicionário contendo os links externos do asset.

    Raises: LoginException: Se a sessão estiver expirada. UdemyUserApiExceptions: Se houver erro de conexão,
    tempo de requisição excedido, limite de redirecionamentos excedido ou erro HTTP. UnhandledExceptions: Se houver
    erro ao obter dados das aulas.
    """
    from .authenticate import UdemyAuth
    auth = UdemyAuth()
    if not auth.verif_login():
        raise LoginException("Sessão expirada!")
    url = (f'https://www.udemy.com/api-2.0/users/me/subscribed-courses/{course_id}/lectures/{id_lecture}/'
           f'supplementary-assets/{asset_id}/?fields[asset]=external_url')
    try:
        # Faz a solicitação GET com os cabeçalhos
        response = requests.get(url, headers=HEADERS_USER)
        data = []
        # Exibe o código de status
        if response.status_code == 200:
            a = json.loads(response.text)
            return a
        else:
            raise UnhandledExceptions(f"Erro ao obter dados de aulas! Código de status: {response.status_code}")

    except requests.ConnectionError as e:
        raise UdemyUserApiExceptions(f"Erro de conexão: {e}")
    except requests.Timeout as e:
        raise UdemyUserApiExceptions(f"Tempo de requisição excedido: {e}")
    except requests.TooManyRedirects as e:
        raise UdemyUserApiExceptions(f"Limite de redirecionamentos excedido: {e}")
    except requests.HTTPError as e:
        raise UdemyUserApiExceptions(f"Erro HTTP: {e}")
    except Exception as e:
        raise UnhandledExceptions(f"Erro ao obter mídias: {e}")


def extract_files(supplementary_assets: list) -> list:
    """
    Obtém o ID da lecture, o ID do asset, o asset_type e o filename.

    Args:
        supplementary_assets (list): Lista de assets suplementares.

    Returns:
        list: Lista de dicionários contendo informações dos assets.
    """
    files = []
    for item in supplementary_assets:
        lecture_title = item.get('lecture_title')
        lecture_id = item.get('lecture_id')
        asset = item.get('asset', {})
        asset_id = asset.get('id')
        asset_type = asset.get('asset_type')
        filename = asset.get('filename')
        title = asset.get('title')
        external_url = asset.get('is_external', None)
        files.append({
            'lecture_id': lecture_id,
            'asset_id': asset_id,
            'asset_type': asset_type,
            'filename': filename,
            'title': title,
            'lecture_title': lecture_title,
            'ExternalLink': external_url
        })
    return files


def extract_course_data(course_dict) -> dict:
    """
    Extrai dados do curso de um dicionário de informações do curso.

    Args:
        course_dict (dict): Dicionário contendo dados do curso.

    Returns:
        dict: Dicionário contendo dados extraídos do curso.
    """
    # Extrair informações principais
    course_id = course_dict.get('id')
    title = course_dict.get('title')
    num_subscribers = course_dict.get('num_subscribers')
    avg_rating_recent = course_dict.get('avg_rating_recent')
    estimated_content_length = course_dict.get('estimated_content_length')

    # Extrair informações dos instrutores
    instructors = course_dict.get('visible_instructors', [])
    instructor_data = []
    for instructor in instructors:
        instructor_data.append({
            'id': instructor.get('id'),
            'title': instructor.get('title'),
            'name': instructor.get('name'),
            'display_name': instructor.get('display_name'),
            'job_title': instructor.get('job_title'),
            'image_50x50': instructor.get('image_50x50'),
            'image_100x100': instructor.get('image_100x100'),
            'initials': instructor.get('initials'),
            'url': instructor.get('url'),
        })

    # Extrair informações de localização
    locale = course_dict.get('locale', {})
    locale_data = {
        'locale': locale.get('locale'),
        'title': locale.get('title'),
        'english_title': locale.get('english_title'),
        'simple_english_title': locale.get('simple_english_title'),
    }

    # Extrair informações de categorias e subcategorias
    primary_category = course_dict.get('primary_category', {})
    primary_category_data = {
        'id': primary_category.get('id'),
        'title': primary_category.get('title'),
        'title_cleaned': primary_category.get('title_cleaned'),
        'url': primary_category.get('url'),
        'icon_class': primary_category.get('icon_class'),
        'type': primary_category.get('type'),
    }

    primary_subcategory = course_dict.get('primary_subcategory', {})
    primary_subcategory_data = {
        'id': primary_subcategory.get('id'),
        'title': primary_subcategory.get('title'),
        'title_cleaned': primary_subcategory.get('title_cleaned'),
        'url': primary_subcategory.get('url'),
        'icon_class': primary_subcategory.get('icon_class'),
        'type': primary_subcategory.get('type'),
    }

    # Extrair informações contextuais
    context_info = course_dict.get('context_info', {})
    category_info = context_info.get('category', {})
    label_info = context_info.get('label', {})

    category_data = {
        'id': category_info.get('id'),
        'title': category_info.get('title'),
        'url': category_info.get('url'),
        'tracking_object_type': category_info.get('tracking_object_type'),
    }

    label_data = {
        'id': label_info.get('id'),
        'display_name': label_info.get('display_name'),
        'title': label_info.get('title'),
        'topic_channel_url': label_info.get('topic_channel_url'),
        'url': label_info.get('url'),
        'tracking_object_type': label_info.get('tracking_object_type'),
    }

    # Compilar todos os dados em um dicionário
    result = {
        'course_id': course_id,
        'title': title,
        'num_subscribers': num_subscribers,
        'avg_rating_recent': avg_rating_recent,
        'estimated_content_length': estimated_content_length,
        'instructors': instructor_data,
        'locale': locale_data,
        'primary_category': primary_category_data,
        'primary_subcategory': primary_subcategory_data,
        'category_info': category_data,
        'label_info': label_data,
    }

    return result


def format_size(byte_size):
    # Constantes para conversão
    KB = 1024
    MB = KB ** 2
    GB = KB ** 3
    TB = KB ** 4
    try:
        byte_size = int(byte_size)

        if byte_size < KB:
            return f"{byte_size} bytes"
        elif byte_size < MB:
            return f"{byte_size / KB:.2f} KB"
        elif byte_size < GB:
            return f"{byte_size / MB:.2f} MB"
        elif byte_size < TB:
            return f"{byte_size / GB:.2f} GB"
        else:
            return f"{byte_size / TB:.2f} TB"
    except Exception as e:
        return byte_size


def lecture_infor(course_id: int, id_lecture: int):
    """
    Obtém informações de uma aula específica.

    Args:
        course_id (int): ID do curso.
        id_lecture (int): ID da aula.

    Returns:
        dict: Um dicionário contendo as informações da aula.

    Raises:
        LoginException: Se a sessão estiver expirada.
        ConnectionError: Se houver erro ao obter as informações da aula.
    """
    from .authenticate import UdemyAuth
    auth = UdemyAuth()
    if not auth.verif_login():
        raise LoginException("Sessão expirada!")
    edpoint = (f"https://www.udemy.com/api-2.0/users/me/subscribed-courses/{course_id}/lectures/{id_lecture}/?"
               f"fields[asset]=media_license_token")
    r = requests.get(edpoint, headers=HEADERS_USER)
    if r.status_code == 200:
        return json.loads(r.text)
    else:
        raise ConnectionError(f"Erro ao obter informações da aula:{r.status_code}"
                              f"\n\n"
                              f"{r.text}")


def assets_infor(course_id: int, id_lecture: int, assets_id: int):
    """
    Obtém informações de um asset específico de uma aula.

    Args:
        course_id (int): ID do curso.
        id_lecture (int): ID da aula.
        assets_id (int): ID do asset.

    Returns:
        str: Conteúdo HTML do asset.

    Raises:
        LoginException: Se a sessão estiver expirada.
        ConnectionError: Se houver erro ao obter as informações do asset.
    """
    from .authenticate import UdemyAuth
    auth = UdemyAuth()
    if not auth.verif_login():
        raise LoginException("Sessão expirada!")
    endpoint = (f'https://www.udemy.com/api-2.0/assets/{assets_id}/?fields[asset]=@min,status,delayed_asset_message,'
                f'processing_errors,body&course_id={course_id}&lecture_id={id_lecture}')
    r = requests.get(endpoint, headers=HEADERS_USER)
    if r.status_code == 200:
        dt = json.loads(r.text)
        body = dt.get("body")
        title = lecture_infor(course_id=course_id, id_lecture=id_lecture).get("title")
        return save_html(body, title_lecture=title)
    else:
        raise ConnectionError(f"Erro ao obter informações de assets! {r.status_code}"
                              f"\n\n"
                              f"{r.text}")



def save_html(body, title_lecture):
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{title_lecture}</title>
</head>
<body>
{body}
</body>
</html>"""

    return html_content

def J(e, t):
    """
    Gera um identificador único baseado na data atual e nas funções X e ee.

    Args:
        e (str): Um identificador.
        t (str): Um tipo de identificador.

    Returns:
        str: Um identificador único.
    """
    r = datetime.now()
    s = r.isoformat()[:10]
    return s + X(e, s, t)


def X(e, t, r):
    """
    Gera um código HMAC-SHA256 baseado nos parâmetros fornecidos.

    Args:
        e (str): Um identificador.
        t (str): Um timestamp.
        r (str): Um identificador de tipo.

    Returns:
        str: Um código gerado.
    """
    s = 0
    while True:
        o = ee(s)
        a = hmac.new(r.encode(), (e + t + o).encode(), hashlib.sha256).digest()
        if te(16, a):
            return o
        s += 1


def ee(e):
    """
    Gera uma string baseada no valor do contador.

    Args:
        e (int): Um valor do contador.

    Returns:
        str: Uma string gerada.
    """
    if e < 0:
        return ""
    return ee(e // 26 - 1) + chr(65 + e % 26)


def te(e, t):
    """
    Verifica se a sequência de bits gerada começa com um número específico de zeros.

    Args:
        e (int): O número de zeros.
        t (bytes): A sequência de bytes.

    Returns:
        bool: True se a sequência começa com o número especificado de zeros, False caso contrário.
    """
    r = math.ceil(e / 8)
    s = t[:r]
    o = ''.join(format(byte, '08b') for byte in s)
    return o.startswith('0' * e)
def is_lecture_in_course(lectures,lecture_id) -> bool:
        # Verifica se o lecture_id está presente na lista de aulas
        for lecture in lectures:
            if lecture.get('lecture_id') == lecture_id:
                return True
        return False