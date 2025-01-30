from .exeptions import UdemyUserApiExceptions, UnhandledExceptions, LoginException
from .sections import get_courses_plan, get_details_courses
from .api import HEADERS_USER
from .bultins import Course
from .authenticate import UdemyAuth

auth = UdemyAuth()
verif_login = auth.verif_login()


class Udemy:
    """Wrapper para API de usuário da plataforma Udemy"""

    def __init__(self):
        """
        Inicializa o objeto Udemy.

        Raises:
            LoginException: Se a sessão estiver expirada.
        """
        self.__headers = HEADERS_USER
    @staticmethod
    def my_subscribed_courses_by_plan() -> list[dict]:
        """
        Obtém os cursos que o usuário está inscrito, obtidos através de planos (assinatura).

        Returns:
            list[dict]: Lista de cursos inscritos através de planos.

        Raises:
            UdemyUserApiExceptions: Se houver erro ao obter os cursos.
        """
        if not verif_login:
            raise LoginException(
                                 "Nenhuma sessão ativa,primeiro efetue login!")

        try:
            courses = get_courses_plan(tipe='plan')
            return courses
        except UdemyUserApiExceptions as e:
            raise UnhandledExceptions(e)

    @staticmethod
    def my_subscribed_courses() -> list[dict]:
        """
        Obtém os cursos que o usuário está inscrito, excluindo listas vazias ou nulas.

        Returns:
            list[dict]: Lista de todos os cursos inscritos.

        Raises:
            UdemyUserApiExceptions: Se houver erro ao obter os cursos.
        """
        if not verif_login:
            raise LoginException(
                "Nenhuma sessão ativa,primeiro efetue login!")

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
            raise UnhandledExceptions(e)

    @staticmethod
    def get_details_course(course_id) ->Course:
        """
        Obtém detalhes de um curso através do ID.

        Args:
            course_id: O ID do curso.

        Returns:
            Course: Um objeto Course contendo os detalhes do curso.

        Raises:
            UnhandledExceptions: Se houver erro ao obter os detalhes do curso.
        """
        if not verif_login:
            raise LoginException(
                                 "Nenhuma sessão ativa,primeiro efetue login!")

        try:
            d = get_details_courses(course_id)
            b = Course(course_id=course_id, results=d)
            return b
        except UnhandledExceptions as e:
            raise UnhandledExceptions(e)
