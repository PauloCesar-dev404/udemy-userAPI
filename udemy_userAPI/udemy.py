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
        """
        cookies de seção.
        """
        self.__headers = HEADERS_USER
        if verif_login is None:
            raise LoginException("User Not Logged!")

    @property
    def my_subscribed_courses_by_plan(self) -> list[dict]:
        """obtém os cursos que o usuário esatá inscrito, obtidos atraves de planos(assinatura)"""
        try:
            courses = get_courses_plan(tipe='plan')
            return courses
        except UdemyUserApiExceptions as e:
            UnhandledExceptions(e)

    @property
    def my_subscribed_courses(self) -> list[dict]:
        """obtém os cursos que o usuário esatá inscrito"""
        try:
            courses = get_courses_plan(tipe='default')
            return courses
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
