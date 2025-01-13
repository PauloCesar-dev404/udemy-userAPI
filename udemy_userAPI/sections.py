import json
import requests
from .exeptions import UdemyUserApiExceptions, LoginException


def get_courses_plan(tipe: str) -> list:
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
    from .api import HEADERS_USER
    from .authenticate import UdemyAuth
    auth = UdemyAuth()
    if not auth.verif_login():
        raise LoginException("Sessão expirada!")
    response = requests.get(
        f"https://www.udemy.com/api-2.0/courses/{course_id}/subscriber-curriculum-items/?"
        f"caching_intent=True&fields%5Basset%5D=title%2Cfilename%2Casset_type%2Cstatus%2Ctime_estimation%2"
        f"Cis_external&fields%5Bchapter%5D=title%2Cobject_index%2Cis_published%2Csort_order&fields%5Blecture"
        f"%5D=title%2Cobject_index%2Cis_published%2Csort_order%2Ccreated%2Casset%2Csupplementary_assets%2"
        f"Cis_free&fields%5Bpractice%5D=title%2Cobject_index%2Cis_published%2Csort_order&fields%5Bquiz%5D="
        f"title%2Cobject_index%2Cis_published%2Csort_order%2Ctype&pages&page_size=400&fields[lecture]=asset,"
        f"description,download_url,is_free,last_watched_second&fields[asset]=asset_type,length,"
        f"media_license_token,course_is_drmed,external_url&q=0.3108014137011559",
        headers=HEADERS_USER)
    if response.status_code == 200:
        resposta = json.loads(response.text)
        return resposta
    else:
        UdemyUserApiExceptions(f"erro ao obter detalhes do curso! {response.status_code}")


def get_course_infor(course_id):
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
        raise UdemyUserApiExceptions("erro ao obter informações do curso!")
