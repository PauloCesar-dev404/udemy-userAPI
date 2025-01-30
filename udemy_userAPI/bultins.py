from typing import Any
from .api import *
from .exeptions import LoginException
from .mpd_analyzer import MPDParser
from .sections import get_course_infor


class DRM:
    def __init__(self, license_token: str, get_media_sources: list):
        """
        Inicializa o objeto DRM.

        Args:
            license_token (str): O token de licença.
            get_media_sources (list): A lista de fontes de mídia.
        """
        self.__mpd_file_path = None
        self.__token = license_token
        self.__dash_url = organize_streams(streams=get_media_sources).get('dash', {})
        if not license_token or get_media_sources:
            return

    def get_key_for_lesson(self):
        """
        Obtém as chaves para a aula.

        Returns:
            As chaves da aula ou None se não for possível obtê-las.
        """
        try:
            if self.__dash_url:
                self.__mpd_file_path = get_mpd_file(mpd_url=self.__dash_url[0].get('src'))
                parser = MPDParser(mpd_content=self.__mpd_file_path)
                resolutions = get_highest_resolution(parser.get_all_video_resolutions())
                parser.set_selected_resolution(resolution=resolutions)
                init_url = parser.get_selected_video_init_url()
                if init_url:
                    pssh = get_pssh(init_url=init_url)
                    if pssh:
                        keys = extract(pssh=pssh, license_token=self.__token)
                        if keys:
                            return keys
                        else:
                            return None
                else:
                    return None
            else:
                return None
        except Exception as e:
            raise Exception(f"Não foi possível obter as chaves!\n{e}")


class Files:
    def __init__(self, files: list[dict], id_course):
        """
        Inicializa o objeto Files.

        Args:
            files (list[dict]): Lista de dicionários contendo os dados dos arquivos.
            id_course: ID do curso.
        """
        self.__data = files
        self.__id_course = id_course

    @property
    def get_download_url(self) -> dict[str, Any | None] | list[dict[str, Any | None]]:
        """
        Obtém a URL de download de um arquivo quando disponível.

        Returns:
            dict[str, Any | None] | list[dict[str, Any | None]]: URL de download do arquivo.
        """
        from .authenticate import UdemyAuth
        auth = UdemyAuth()
        if not auth.verif_login():
            raise LoginException("Sessão expirada!")
        download_urls = []
        for files in self.__data:
            lecture_id = files.get('lecture_id', None)
            asset_id = files.get('asset_id', None)
            title = files.get("title", None)
            lecture_title = files.get('lecture_title', None)
            external_link = files.get('ExternalLink', None)
            if external_link:
                lnk = get_external_liks(course_id=self.__id_course, id_lecture=lecture_id, asset_id=asset_id)
                dt_file = {'title-file': title,
                           'lecture_title': lecture_title,
                           'lecture_id': lecture_id,
                           'external_link': external_link,
                           'data-file': lnk.get('external_url', None)}
                return dt_file
            if asset_id and title and lecture_id and not external_link:
                resp = requests.get(
                    f"https://www.udemy.com/api-2.0/users/me/subscribed-courses/{self.__id_course}/lectures/"
                    f"{lecture_id}/supplementary-assets/{asset_id}/?fields[asset]=download_urls",
                    headers=HEADERS_USER)
                if resp.status_code == 200:
                    da = json.loads(resp.text)
                    # Para cada dict de um arquivo colocar seu título:
                    dt_file = {'title-file': title,
                               'lecture_title': lecture_title,
                               'lecture_id': lecture_id,
                               'external_link': external_link,
                               'data-file': da['download_urls']}
                    download_urls.append(dt_file)
        return download_urls

class Quiz:
    """Representa um quiz.
    """

    def __init__(self, quiz_data: dict):
        """
        Inicializa uma instância de Quiz.

        Args:
            quiz_data (dict): Dados do quiz.
        """
        self._data = quiz_data

    @property
    def id(self) -> int:
        """Retorna o ID do quiz."""
        return self._data.get('id', 0)

    @property
    def title(self) -> str:
        """Retorna o título do quiz."""
        return self._data.get('title', '')

    @property
    def type_quiz(self) -> str:
        """Retorna o tipo de quiz (exame ou prática)."""
        return self._data.get('type', '')

    @property
    def description(self) -> str:
        """Retorna a descrição do quiz."""
        return remove_tag(self._data.get('description', ''))

    @property
    def duration(self) -> int:
        """Retorna a duração do quiz em minutos, se aplicável."""
        duration: int = self._data.get('duration', 1)
        if duration > 1:
            return int(duration / 60)
        else:
            return 0

    @property
    def pass_percent(self) -> int:
        """Retorna a porcentagem necessária para passar."""
        return self._data.get('pass_percent', 0)

    @property
    def num_assessments(self) -> int:
        """Retorna o número de perguntas do quiz."""
        return self._data.get('num_assessments', 0)

    def content(self) -> dict:
        """Obtém o conteúdo do quiz."""
        htmls = get_quizzes(lecture_id=self.id)
        return htmls


class Caption:
    """Representa uma legenda."""

    def __init__(self, caption: dict):
        """
        Inicializa uma instância de Caption.

        Args:
            caption (dict): Dados da legenda.
        """
        self._caption = caption

    @property
    def locale(self) -> str:
        """Retorna o idioma."""
        return self._caption.get('video_label', '')

    @property
    def status(self) -> str:
        """Retorna o status da legenda 1 ou 0"""
        return self._caption.get('status')

    @property
    def title(self) -> str:
        """Retorna o título da legenda."""
        return self._caption.get('title', '')

    @property
    def created(self) -> str:
        """Retorna a data de criação da legenda."""
        return self._caption.get('created', '')

    @property
    def id(self) -> int:
        """Retorna o ID da legenda."""
        return self._caption.get('id', 0)

    @property
    def url(self) -> str:
        """Retorna a URL da legenda."""
        return self._caption.get('url', '')

    @property
    def content(self) -> str:
        """Obtém o conteúdo da legenda."""
        if self.url:
            r = requests.get(headers=HEADERS_USER, url=self.url)
            if r.status_code == 200:
                return r.text
            else:
                raise ConnectionError(
                    f'status_code: {r.status_code}, Não foi possível obter o conteúdo da legenda!'
                )
        else:
            raise FileNotFoundError(
                'Não foi possível obter a URL da legenda!'
            )

class Captions:
    """Gerencia as legendas de um vídeo."""

    def __init__(self, caption_data: list):
        """
        Inicializa uma instância de Captions.

        Args:
            caption_data (list): Dados das legendas.
        """
        self._caption_data = caption_data

    def languages(self) -> list[dict]:
        """Retorna a lista de idiomas disponíveis na aula."""
        langs = []
        for caption in self._caption_data:
            locale_id = caption.get('locale_id', '')
            video_label = caption.get('video_label','')
            if locale_id:
                langs.append({'locale_id': locale_id,'locale':video_label})
        return langs

    def get_lang(self, locale_id: str) -> Caption:
        """
        Obtém a legenda para o idioma especificado.


        Args:
            locale_id (str): ID do idioma,pode ser obtido no método -> 'languages'

        Returns:
            Caption: Objeto Caption.

        Raises:
            FileNotFoundError: Se o idioma não estiver disponível na aula.
        """
        is_t = False
        cpt = {}
        for caption in self._caption_data:
            if locale_id == caption.get('locale_id'):
                is_t = True
                cpt = caption
        if not is_t:
            raise FileNotFoundError(
                'Esse idioma não está disponível nessa aula!'
            )
        c = Caption(caption=cpt)
        return c


class Lecture:
    """Cria objetos aula (lecture) do curso e extrai os dados."""

    def __init__(self, data: dict, course_id: int, additional_files):
        """
        Inicializa o objeto Lecture.

        Args:
            data (dict): Um dicionário contendo os dados da aula.
            course_id (int): O ID do curso.
            additional_files: Arquivos adicionais relacionados à aula.
        """
        self.__course_id = course_id
        self.__data = data
        self.__additional_files = additional_files
        self.__asset = self.__data.get("asset", {})

    @property
    def get_lecture_id(self) -> int:
        """
        Obtém o ID da aula.

        Returns:
            int: O ID da aula.
        """
        return self.__data.get('id', 0)

    @property
    def get_description(self) -> str:
        """
        Obtém a descrição da aula.

        Returns:
            str: A descrição da aula.
        """
        return remove_tag(str(self.__data.get('description')))

    @property
    def is_free(self) -> bool:
        """
        Verifica se a aula é gratuita (aulas gratuitas estão disponíveis na apresentação do curso).

        Returns:
            bool: True se a aula for gratuita, False caso contrário.
        """
        return self.__data.get('is_free', False)

    @property
    def get_thumbnail(self) -> dict:
        """
        Obtém informações da miniatura (thumbnail) do vídeo.

        Returns:
            dict: Um dicionário contendo as URLs das miniaturas.
        """
        thumbnail_sprite = self.__asset.get('thumbnail_sprite', {})
        return {
            'thumbnail_vtt_url': thumbnail_sprite.get('vtt_url',[]),
            'thumbnail_img_url': thumbnail_sprite.get('img_url',[])
        }

    @property
    def get_asset_type(self) -> str:
        """
        Obtém o tipo de asset (Video, Article, etc.).

        Returns:
            str: O tipo de asset.
        """
        return self.__asset.get('asset_type', '') or self.__data.get('_class','').replace('quiz','Quiz')

    @property
    def get_media_sources(self) -> list:
        """
        Obtém dados de streaming.

        Returns:
            list: Uma lista contendo as fontes de mídia.
        """
        return self.__asset.get('media_sources',[])

    @property
    def get_captions(self) -> Captions:
        """
        Obtém as legendas.

        Returns:
            Captions: Objeto para gerenciar as legendas.
        """
        if self.__asset.get('captions',[]):
            c = Captions(caption_data=self.__asset.get('captions',[]))
            return c
        else:
            raise FileNotFoundError(
                'Não foi encontrada legendas nessa aula!'
            )
    @property
    def get_external_url(self) -> list:
        """
        Obtém links externos se houver.

        Returns:
            list: Uma lista contendo os links externos.
        """
        return self.__asset.get('external_url',[])

    @property
    def get_media_license_token(self) -> str:
        """
        Obtém o token de acesso à aula se houver.

        Returns:
            str: O token de acesso à aula.
        """
        return self.__asset.get('media_license_token','')

    def course_is_drmed(self) -> DRM:
        """
        Verifica se a aula possui DRM. Se sim, retorna as keys da aula.

        Returns:
            DRM: O objeto DRM contendo as keys da aula ou None.
        """
        d = DRM(license_token=self.get_media_license_token,
                    get_media_sources=self.get_media_sources)
        return d

    def quiz_object(self) ->Quiz:
        """se for um quiz ele retorna um objeto Quiz"""
        if self.get_asset_type.lower() == 'quiz':
            q =Quiz(get_assessments(lecture_id=self.get_lecture_id,course_id=self.__course_id))
            return q
        else:
            raise UserWarning(
                'Atenção essa aula não é um Quiz!'
            )

    @property
    def get_download_urls(self) -> list:
        """
        Obtém URLs de download se houver.

        Returns:
            list: Uma lista contendo as URLs de download.
        """
        return self.__asset.get('download_urls',[])

    @property
    def get_slide_urls(self) -> list:
        """
        Obtém URLs de slides se houver.

        Returns:
            list: Uma lista contendo as URLs de slides.
        """
        return self.__asset.get('slide_urls',[])

    @property
    def get_slides(self) -> list:
        """
        Obtém slides se houver.

        Returns:
            list: Uma lista contendo os slides.
        """
        return self.__asset.get('slides',[])

    @property
    def get_articles(self):
        """
        Obtém os artigos relacionados à aula.

        Returns:
            Os artigos relacionados à aula.
        """
        if self.__asset:
            d = assets_infor(course_id=self.__course_id, id_lecture=self.get_lecture_id, assets_id=self.__asset.get("id"))
            return d
        else:
            return []

    @property
    def get_resources(self):
        """
        Obtém os recursos adicionais relacionados à aula.

        Returns:
            Os recursos adicionais relacionados à aula.
        """
        if self.__additional_files:
            files_add = get_files_aule(lecture_id_filter=self.get_lecture_id, data=self.__additional_files)
            f = Files(files=files_add, id_course=self.__course_id).get_download_url
            return f
        else:
            return []

class Course:
    """Recebe um dicionário com os dados do curso."""

    def __init__(self, results: dict, course_id: int):
        """
        Inicializa o objeto Course.

        Args:
            results (dict): Um dicionário contendo os dados do curso.
            course_id (int): O ID do curso.
        """
        self.__parser_chapers = parser_chapters(results=results)
        self.__data:list = self.__parser_chapers
        self.__course_id = course_id
        self.__results = results
        self.__additional_files_data = get_add_files(course_id)
        self.__information = self.__load_infor_course()

    def __load_infor_course(self) -> dict:
        """
        Obtém as informações do curso.

        Returns:
            dict: Um dicionário contendo as informações do curso.
        """
        data = get_course_infor(self.__course_id)
        return data

    @property
    def title_course(self) -> str:
        """
        Obtém o título do curso.

        Returns:
            str: O título do curso.
        """
        return self.__information.get('title')

    @property
    def instructors(self) -> dict:
        """
        Obtém informações dos instrutores.

        Returns:
            dict: Um dicionário contendo as informações dos instrutores.
        """
        return self.__information.get("visible_instructors")

    @property
    def locale(self):
        """
        Obtém informações de localidade do curso.

        Returns:
            str: As informações de localidade do curso.
        """
        return self.__information.get('locale')

    @property
    def primary_category(self):
        """
        Obtém a categoria primária.

        Returns:
            str: A categoria primária.
        """
        return self.__information.get('primary_category')

    @property
    def primary_subcategory(self):
        """
        Obtém a subcategoria primária.

        Returns:
            str: A subcategoria primária.
        """
        return self.__information.get('primary_subcategory')

    @property
    def count_lectures(self) -> int:
        """
        Obtém o número total de lectures no curso.

        Returns:
            int: O número total de lectures no curso.
        """
        total_lectures = 0
        for chapter in self.__data:
            total_lectures += len(chapter.get('lectures', []))
        return total_lectures

    @property
    def count_chapters(self) -> int:
        """
        Obtém o número total de chapters (sections) no curso.

        Returns:
            int: O número total de chapters (sections) no curso.
        """
        return len(self.__data)

    @property
    def title_videos(self) -> list:
        """
        Obtém uma lista com todos os títulos de vídeos no curso.

        Returns:
            list: Uma lista contendo os títulos de vídeos no curso.
        """
        videos = []
        for chapter in self.__data:
            for video in chapter.get('videos_in_chapter', []):
                asset_type = video.get('asset_type')
                if asset_type == 'Video':
                    title = video['title']
                    if title != "Files":
                        videos.append(title)
        return videos

    @property
    def get_lectures(self) -> list:
        """
        Obtém uma lista de dicionários com todas as aulas.
        Returns:
            list: Uma lista contendo todas as aulas.
        """
        videos = []

        for chapter in self.__data:
            for video in chapter.get('lectures', []):
                dt = {
                    'section': chapter.get('title', ''),
                    'title': video.get('title', ''),
                    'lecture_id': video.get('lecture_id', ''),
                    'asset_id': video.get('asset_id', ''),
                    'asset_type': video.get('asset_type', '')
                }
                videos.append(dt)

        return videos

    def get_details_lecture(self, lecture_id: int) -> Lecture:
        """
        Obtém detalhes de uma aula específica.

        Args:
            lecture_id (int): O ID da aula.

        Returns:
            Lecture: Um objeto Lecture contendo os detalhes da aula.
        """
        type_lecture  = ''
        links= {}
        if not is_lecture_in_course(lecture_id=lecture_id,lectures=self.get_lectures):
            raise FileNotFoundError(
                'Essa aula não existe nesse curso!'
            )
        for l in self.get_lectures:
            if lecture_id == l.get('lecture_id'):
                type_lecture = l.get('asset_type')
        if type_lecture.lower() ==  'video' or type_lecture.lower() == 'article':
            links = get_links(course_id=self.__course_id, id_lecture=lecture_id)
        else:
            links = get_assessments(course_id=self.__course_id,lecture_id=lecture_id)
        additional_files = self.__load_assets()
        lecture = Lecture(data=links, course_id=self.__course_id, additional_files=additional_files)
        return lecture

    @property
    def get_additional_files(self) -> list:
        """
        Retorna a lista de arquivos adicionais de um curso.

        Returns:
            list: Uma lista contendo os arquivos adicionais de um curso.
        """
        supplementary_assets = []
        for item in self.__additional_files_data.get('results', []):
            if item.get('_class') == 'lecture':
                id_l = item.get('id', {})
                title = item.get('title', {})
                assets = item.get('supplementary_assets', [])
                for asset in assets:
                    supplementary_assets.append({
                        'lecture_id': id_l,
                        'lecture_title': title,
                        'asset': asset
                    })
        files = extract_files(supplementary_assets)
        files_objt = Files(files=files, id_course=self.__course_id).get_download_url
        return files_objt

    def __load_assets(self):
        """
        Retorna a lista de arquivos adicionais de um curso.

        Returns:
            list: Uma lista contendo os arquivos adicionais de um curso.
        """
        supplementary_assets = []
        for item in self.__additional_files_data.get('results', []):
            if item.get('_class') == 'lecture':
                id_l = item.get('id')
                title = item.get('title')
                assets = item.get('supplementary_assets', [])
                for asset in assets:
                    supplementary_assets.append({
                        'lecture_id': id_l,
                        'lecture_title': title,
                        'asset': asset
                    })
        files = extract_files(supplementary_assets)
        return files
