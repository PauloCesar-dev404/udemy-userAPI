from .exeptions import UdemyUserApiExceptions, UnhandledExceptions, LoginException
from .sections import get_courses_plan, get_details_courses
from .api import HEADERS_USER
from .bultins import Course
from .authenticate import UdemyAuth

auth = UdemyAuth()
verif_login = auth.verif_login


class Udemy:
    """wrapper para api de usuario da plataforma udemy"""

    def __init__(self):
        self.__headers = HEADERS_USER
        if verif_login is None:
            raise LoginException("User Not Logged!")

    @staticmethod
    def my_subscribed_courses_by_plan() -> list[dict]:
        """obtém os cursos que o usuário esatá inscrito, obtidos atraves de planos(assinatura)
        :return:
        """
        try:
            courses = get_courses_plan(tipe='plan')
            return courses
        except UdemyUserApiExceptions as e:
            UnhandledExceptions(e)

    @staticmethod
    def my_subscribed_courses() -> list[dict]:
        """Obtém os cursos que o usuário está inscrito, excluindo listas vazias ou nulas"""
        try:
            # Obtém os cursos
            courses1 = get_courses_plan(tipe='default')  # lista de cursos padrão
            courses2 = get_courses_plan(tipe='plan')  # lista de cursos de um plano

            # Cria uma lista vazia para armazenar os cursos válidos
            all_courses = []

            # Adiciona a lista somente se não estiver vazia ou nula
            if courses1:
                for i in courses1:
                    all_courses.extend(i)
            if courses2:
                for i in courses2:
                    all_courses.extend(i)

            return all_courses

        except UdemyUserApiExceptions as e:
            UnhandledExceptions(e)

    @staticmethod
    def get_details_course(course_id):
        """obtenha detalhes de um curso atarves do id"""
        try:
            d = get_details_courses(course_id)
            b = Course(course_id=course_id, results=d)
            return b
        except UnhandledExceptions as e:
            UnhandledExceptions(e)
