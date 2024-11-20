import json
from .exeptions import UdemyUserApiExceptions, UnhandledExceptions
from .authenticate import UdemyAuth
import os.path
from pywidevine.cdm import Cdm
from pywidevine.device import Device
from pywidevine.pssh import PSSH
import requests
import base64
import logging

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

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)
# Obtém o diretório do arquivo em execução
locate = os.path.dirname(__file__)
# Cria o caminho para o arquivo bin.wvd na subpasta bin
binn = 'bin.py'
WVD_FILE_PATH = os.path.join(locate, 'mpd_analyzer', 'bin.wvd')

device = Device.load(WVD_FILE_PATH)
cdm = Cdm.from_device(device)


def read_pssh_from_bytes(bytes):
    pssh_offset = bytes.rfind(b'pssh')
    _start = pssh_offset - 4
    _end = pssh_offset - 4 + bytes[pssh_offset - 1]
    pssh = bytes[_start:_end]
    return pssh


def get_pssh(init_url):
    logger.info(f"INIT URL: {init_url}")
    res = requests.get(init_url, headers=HEADERS_octet_stream)
    if not res.ok:
        logger.exception("Could not download init segment: " + res.text)
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
    license_url = (f"https://www.udemy.com/api-2.0/media-license-server/validate-auth-token?drm_type=widevine"
                   f"&auth_token={license_token}")
    logger.info(f"License URL: {license_url}")
    session_id = cdm.open()
    challenge = cdm.get_license_challenge(session_id, PSSH(pssh))
    logger.info("Sending license request now")
    license = requests.post(license_url, headers=HEADERS_octet_stream, data=challenge)
    try:
        str(license.content, "utf-8")
    except:
        base64_license = base64.b64encode(license.content).decode()
        logger.info("[+] Acquired license sucessfully!")
    else:
        if "CAIS" not in license.text:
            logger.exception("[-] Couldn't to get license: [{}]\n{}".format(license.status_code, license.text))
            return

    logger.info("Trying to get keys now")
    cdm.parse_license(session_id, license.content)
    final_keys = ""
    for key in cdm.get_keys(session_id):
        logger.info(f"[+] Keys: [{key.type}] - {key.kid.hex}:{key.key.hex()}")
        if key.type == "CONTENT":
            final_keys += f"{key.kid.hex}:{key.key.hex()}"
    cdm.close(session_id)

    if final_keys == "":
        logger.exception("Keys were not extracted sucessfully.")
        return
    return final_keys.strip()


def get_mpd_file(mpd_url):
    try:
        # Faz a solicitação GET com os cabeçalhos
        response = requests.get(mpd_url, headers=HEADERS_USER)
        data = []
        # Exibe o código de status
        if response.status_code == 200:
            return response.content
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


def parser_chapers(results):
    """
    :param results:
    :param tip: chaper,videos
    :return:
    """
    if not results:
        raise UdemyUserApiExceptions("Não foi possível obter detalhes do curso!")
    results = results.get('results', None)
    if not results:
        raise UdemyUserApiExceptions("Não foi possível obter detalhes do curso!")
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
                video_title = dictionary.get('title', None)
                if not video_title:
                    video_title = 'Files'
                current_chapter['videos_in_chapter'].append({
                    'video_title': video_title,
                    'title_lecture': dictionary.get('title'),
                    'lecture_id': dictionary.get('id'),
                    'asset_id': asset.get('id')
                })
    return chapters_dict


def get_add_files(course_id: int):
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


def get_files_aule(lecture_id_filter, data: list):
    files = []
    # print(f'DEBUG:\n\n{data}')
    for files_data in data:
        lecture_id = files_data.get('lecture_id')
        if lecture_id == lecture_id_filter:
            files.append(files_data)
    return files


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


def get_external_liks(course_id: int, id_lecture, asset_id):
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


def extract_files(supplementary_assets: list) -> list:
    """Obtém o ID da lecture, o ID do asset, o asset_type e o filename."""
    files = []
    for item in supplementary_assets:
        # print(f'DEBUG files:\n{item}\n\n')
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
    edpoint = (f"https://www.udemy.com/api-2.0/users/me/subscribed-courses/{course_id}/lectures/{id_lecture}/?"
               f"fields[asset]=media_license_token&q=0.06925737374647678")
    r = requests.get(edpoint, headers=HEADERS_USER)
    if r.status_code == 200:
        return json.loads(r.text)


def assets_infor(course_id: int, id_lecture: int, assets_id: int):
    endpoint = (f'https://www.udemy.com/api-2.0/assets/{assets_id}/?fields[asset]=@min,status,delayed_asset_message,'
                f'processing_errors,body&course_id={course_id}&lecture_id={id_lecture}')
    r = requests.get(endpoint, headers=HEADERS_USER)
    if r.status_code == 200:
        dt = json.loads(r.text)
        body = dt.get("body")
        title = lecture_infor(course_id=course_id, id_lecture=id_lecture).get("title")
        return save_html(body, title_lecture=title)


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
