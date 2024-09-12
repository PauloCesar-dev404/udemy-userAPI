import json
import requests
from .exeptions import UdemyUserApiExceptions, UnhandledExceptions
from .authenticate import UdemyAuth

AUTH = UdemyAuth()
COOKIES = AUTH.load_cookies

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


def parser_chapers(results):
    """
    :param results:
    :param tip: chaper,videos
    :return:
    """
    results = results.get('results')
    chapters_dict = {}  # Dicionário para armazenar os capítulos e seus vídeos correspondentes

    # Primeiro, construímos um dicionário de capítulos
    current_chapter = None
    for dictionary in results:
        _class = dictionary.get('_class')

        if _class == 'chapter':
            chapter_index = dictionary.get('object_index')
            current_chapter = {
                'title_chapter': dictionary.get('title'),
                'videos_in_chapter': []
            }
            chapters_dict[f"chapter_{chapter_index}"] = current_chapter
        elif _class == 'lecture' and current_chapter is not None:
            asset = dictionary.get('asset')
            if asset:
                video_title = asset.get('title', None)
                if not video_title:
                    video_title = 'Files'
                current_chapter['videos_in_chapter'].append({
                    'video_title': video_title,
                    'title_lecture': dictionary.get('title'),
                    'id_lecture': dictionary.get('id'),
                    'id_asset': asset.get('id')
                })

    return chapters_dict


def get_links(course_id: int, id_lecture: int):
    """
        :param course_id: id do curso
        :param id_lecture: id da aula
        :return: dict
        """
    get = (f"https://www.udemy.com/api-2.0/users/me/subscribed-courses/{course_id}/lectures/{id_lecture}/?"
           f"fields[lecture]"
           f"=asset,description,download_url,is_free,last_watched_second&fields[asset]=asset_type,length,"
           f"media_license_token,course_is_drmed,media_sources,captions,thumbnail_sprite,slides,slide_urls,"
           f"download_urls,"
           f"external_url&q=0.3108014137011559/?fields[asset]=download_urls")
    try:
        # Faz a solicitação GET com os cabeçalhos
        response = requests.get(get, headers=HEADERS_USER)
        data = []
        # Exibe o código de status
        if response.status_code == 200:
            a = json.loads(response.text)
            return a
        else:
            UnhandledExceptions(f"erro ao obter dados de aulas!! {response.status_code}")

    except requests.ConnectionError as e:
        UdemyUserApiExceptions(f"Erro de conexão: {e}")
    except requests.Timeout as e:
        UdemyUserApiExceptions(f"Tempo de requisição excedido: {e}")
    except requests.TooManyRedirects as e:
        UdemyUserApiExceptions(f"Limite de redirecionamentos excedido: {e}")
    except requests.HTTPError as e:
        UdemyUserApiExceptions(f"Erro HTTP: {e}")
    except Exception as e:
        UnhandledExceptions(f"Errro Ao Obter Mídias:{e}")


def remove_tag(d: str):
    new = d.replace("<p>", '').replace("</p>", '').replace('&nbsp;', ' ')
    return new


def extract_files(supplementary_assets: list) -> list:
    """Obtém o ID da lecture, o ID do asset, o asset_type e o filename."""
    files = []
    for item in supplementary_assets:
        lecture_title = item.get('lecture_title')
        lecture_id = item.get('lecture_id')
        asset = item.get('asset', {})
        asset_id = asset.get('id')
        asset_type = asset.get('asset_type')
        filename = asset.get('filename')
        title = asset.get('title')

        files.append({
            'lecture_id': lecture_id,
            'asset_id': asset_id,
            'asset_type': asset_type,
            'filename': filename,
            'title': title,
            'lecture_title': lecture_title
        })
    return files


def extract_course_data(course_dict) -> dict:
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
