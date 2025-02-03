import json
import requests
from .exeptions import UdemyUserApiExceptions, LoginException


def get_courses_plan(tipe: str) -> list:
    """ Obtém uma lista de cursos com base no tipo de plano.

    Args: tipe (str): Tipo de plano ('default' ou 'plan'). Returns: list: Lista de cursos. Raises: LoginException: Se
    a sessão estiver expirada. UdemyUserApiExceptions: Se houver erro ao obter os cursos."""
    from .api import HEADERS_USER
    from .authenticate import UdemyAuth
    auth = UdemyAuth()
    if not auth.verif_login():
        raise LoginException("Sessão expirada!")
    courses_data = []
    if tipe == 'default':
        response = requests.get(f"https://www.udemy.com/api-2.0/users/me/subscribed-courses/?page_size=1000"
                                f"&ordering=-last_accessed&fields[course]=image_240x135,title,completion_ratio&"
                                f"is_archived=false",
                                headers=HEADERS_USER)
        if response.status_code == 200:
            r = json.loads(response.text)
            results = r.get("results", None)
            if results:
                courses_data.append(results)
        else:
            r = json.loads(response.text)
            raise UdemyUserApiExceptions(f"Error obtain courses 'default' -> {r}")
    elif tipe == 'plan':
        response2 = requests.get(
            url="https://www.udemy.com/api-2.0/users/me/subscription-course-enrollments/?"
                "fields[course]=@min,visible_instructors,image_240x135,image_480x270,completion_ratio,"
                "last_accessed_time,enrollment_time,is_practice_test_course,features,num_collections,"
                "published_title,buyable_object_type,remaining_time,is_assigned,next_to_watch_item,"
                "is_in_user_subscription&fields[user]=@min&ordering=-last_accessed&page_size=1000&"
                "max_progress=99.9&fields[lecture]=@min,content_details,asset,url,thumbnail_url,"
                "last_watched_second,object_index&fields[quiz]=@min,content_details,asset,url,object_index&"
                "fields[practice]=@min,content_details,asset,estimated_duration,learn_url,object_index",
            headers=HEADERS_USER)
        if response2.status_code == 200:
            r = json.loads(response2.text)
            results2 = r.get("results", None)
            if results2:
                courses_data.append(results2)
        else:
            r = json.loads(response2.text)
            raise UdemyUserApiExceptions(f"Error obtain courses 'plan' -> {r}")
    else:
        raise UdemyUserApiExceptions("Atenção dev! os parametros são : 'plan' e 'default'")
    return courses_data


def get_details_courses(course_id):
    """
    Obtém detalhes de um curso específico, realizando paginação caso haja múltiplas páginas.

    Args:
        course_id (int): ID do curso.

    Returns:
        dict: Dicionário contendo os detalhes do curso com todos os itens concatenados.

    Raises:
        LoginException: Se a sessão estiver expirada.
        UdemyUserApiExceptions: Se houver erro ao obter os detalhes do curso.
    """
    from .api import HEADERS_USER
    from .authenticate import UdemyAuth
    auth = UdemyAuth()
    if not auth.verif_login():
        raise LoginException("Sessão expirada!")

    # URL base com parâmetros
    base_url = (
        f"https://www.udemy.com/api-2.0/courses/{course_id}/subscriber-curriculum-items/?"
        f"page_size=1000&"
        f"fields[lecture]=title,object_index,is_published,sort_order,created,asset,supplementary_assets,is_free&"
        f"fields[quiz]=title,object_index,is_published,sort_order,type&"
        f"fields[practice]=title,object_index,is_published,sort_order&"
        f"fields[chapter]=title,object_index,is_published,sort_order&"
        f"fields[asset]=title,filename,asset_type,status,time_estimation,is_external&"
        f"caching_intent=True"
    )

    try:
        response = requests.get(base_url, headers=HEADERS_USER)
        if response.status_code != 200:
            raise UdemyUserApiExceptions(
                f"Erro ao obter detalhes do curso! Código de status: {response.status_code}")

        data = json.loads(response.text)
        all_results = data.get('results', [])
        next_page = data.get('next', '')

        # Enquanto houver próxima página, faz requisição e junta os resultados
        while next_page:
            response = requests.get(next_page, headers=HEADERS_USER)
            if response.status_code != 200:
                # Caso ocorra erro na próxima página, pode-se optar por interromper ou registrar o erro.....por enquanto
                # irei parar..mais se por acaso futuramente não der certo mudarei esta implementação!
                # @pauloCesarDev404
                break
            next_data = json.loads(response.text)
            all_results.extend(next_data.get('results', []))
            next_page = next_data.get('next', '')

        # Atualiza o dicionário final com todos os itens concatenados
        data['results'] = all_results
        return data

    except Exception as e:
        raise UdemyUserApiExceptions(f"Erro ao obter detalhes do curso! {e}")


def get_course_infor(course_id):
    """
    Obtém informações de um curso específico.

    Args:
        course_id (int): ID do curso.

    Returns:
        dict: Dicionário contendo as informações do curso.

    Raises:
        LoginException: Se a sessão estiver expirada.
        UdemyUserApiExceptions: Se houver erro ao obter as informações do curso.
    """
    from .api import HEADERS_USER
    from .authenticate import UdemyAuth
    auth = UdemyAuth()
    if not auth.verif_login():
        raise LoginException("Sessão expirada!")
    end_point = (
        f'https://www.udemy.com/api-2.0/courses/{course_id}/?fields[course]=title,context_info,primary_category,'
        'primary_subcategory,avg_rating_recent,visible_instructors,locale,estimated_content_length,'
        'num_subscribers')
    response = requests.get(end_point, headers=HEADERS_USER)
    if response.status_code == 200:
        return json.loads(response.text)
    else:
        raise UdemyUserApiExceptions("Erro ao obter informações do curso!")
