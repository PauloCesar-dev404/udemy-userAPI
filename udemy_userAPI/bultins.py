import requests
import json
from .sections import get_course_infor
from .api import get_links, remove_tag, parser_chapers, extract_files, HEADERS_USER



class Files:
    def __init__(self, files: list[dict], id_course):
        self.__data = files
        self.__id_course = id_course

    @property
    def get_download_url(self) -> dict[list]:
        """obter url de download de um arquivo quando disponivel(geralemnete para arquivos esta opção é valida"""
        da = {}
        download_urls = ''
        for files in self.__data:
            lecture_id = files.get('lecture_id', None)
            asset_id = files.get('asset_id', None)
            title = files.get("title", None)
            if asset_id and title and lecture_id:
                resp = requests.get(
                    f"https://www.udemy.com/api-2.0/users/me/subscribed-courses/{self.__id_course}/lectures/{lecture_id}/supplementary-assets/{asset_id}/?fields[asset]=download_urls",
                    headers=HEADERS_USER)
                if resp.status_code == 200:
                    da = json.loads(resp.text)
                    download_urls = da['download_urls']
        return download_urls


class Lecture:
    """CRIAR objetos aula(lecture) do curso e extrair os dados.."""

    def __init__(self, data: dict):
        self.__data = data
        self.__asset = self.__data.get("asset")

    @property
    def get_lecture_id(self) -> int:
        """Obtém o ID da lecture"""
        return self.__data.get('id')

    @property
    def get_description(self) -> str:
        """Obtém a descrição da aula"""
        return remove_tag(str(self.__data.get('description')))

    @property
    def is_free(self) -> bool:
        """Verifica se a lecture é gratuita (aulas gratís estão disponíveis na apresentação do curso)"""
        return self.__data.get('is_free', False)

    @property
    def get_thumbnail(self) -> dict:
        """Obtém informações da miniatura (thumbnail) do vídeo"""
        thumbnail_sprite = self.__asset.get('thumbnail_sprite', {})
        return {
            'thumbnail_vtt_url': thumbnail_sprite.get('vtt_url'),
            'thumbnail_img_url': thumbnail_sprite.get('img_url')
        }

    @property
    def get_asset_type(self) -> str:
        """Obtém o tipo de asset (Video, Article, etc.)"""
        return self.__asset.get('asset_type', 'Undefined')

    @property
    def get_media_sources(self) -> list:
        """obtém dados de streaming"""
        return self.__asset.get('media_sources')

    @property
    def get_captions(self) -> list:
        """obtem as legendas"""
        return self.__asset.get('captions')

    @property
    def get_external_url(self) -> list:
        """obtem links externos se tiver..."""
        return self.__asset.get('external_url')

    @property
    def get_media_license_token(self) -> str:
        """obtem token de acesso a aula se tiver.."""
        return self.__asset.get('media_license_token')

    @property
    def course_is_drmed(self) -> bool:
        """verifica se possui DRM.."""
        return self.__asset.get('course_is_drmed')

    @property
    def get_download_urls(self) -> list:
        """obtém urls de downloads se tiver.."""
        return self.__asset.get('download_urls')

    @property
    def get_slide_urls(self) -> list:
        """obtém url de slides se tiver..."""
        return self.__asset.get('slide_urls')

    @property
    def get_slides(self) -> list:
        """obtem slides se tiver.."""
        return self.__asset.get('slides')


class Course:
    """receb um dict com os dados do curso"""

    def __init__(self, results: dict, course_id: int):
        self.__parser_chapers = parser_chapers(results=results)
        self.__data = self.__parser_chapers
        self.__course_id = course_id
        self.__results = results
        self.__information = self.__load_infor_course()

    def __load_infor_course(self) -> dict:
        """obtem as informações do curso"""
        data = get_course_infor(self.__course_id)
        return data

    @property
    def title_course(self):
        """obter titulo do curso"""
        return self.__information.get('title')

    @property
    def instructors(self):
        """obter informações de instrutores"""
        return self.__information.get("visible_instructors")

    @property
    def locale(self):
        """obter informações de localidade do curso"""
        return self.__information.get('locale')

    @property
    def primary_category(self):
        """obter categoria primaria"""
        return self.__information.get('primary_category')

    @property
    def primary_subcategory(self):
        """obter subcategoria primaria"""
        return self.__information.get('primary_subcategory')

    @property
    def count_lectures(self) -> int:
        """Obtém o número total de lectures no curso"""
        total_lectures = 0
        for chapter in self.__data.values():
            total_lectures += len(chapter.get('videos_in_chapter', []))
        return total_lectures

    @property
    def count_chapters(self) -> int:
        """Obtém o número total de chapters(sections) no curso"""
        return len(self.__data)

    @property
    def title_videos(self) -> list:
        """Obtém uma lista com todos os títulos de vídeos no curso"""
        videos = []
        for chapter in self.__data.values():
            for video in chapter.get('videos_in_chapter', []):
                title = video['video_title']
                if title != "Files":
                    videos.append(title)
        return videos

    @property
    def get_lectures(self) -> list:
        """Obtém uma lista com todos as aulas"""
        videos = []
        for chapter in self.__data.values():
            for video in chapter.get('videos_in_chapter', []):
                title = video['video_title']
                id_lecture = video['id_lecture']
                id_asset = video['id_asset']
                dt = {"title": title, 'id_lecture': id_lecture, 'id_asset': id_asset}
                videos.append(dt)
        return videos

    def get_details_lecture(self, lecture_id: int) -> Lecture:
        """obter detalhes de uma aula específica, irá retornar o objeto Lecture"""
        links = get_links(course_id=self.__course_id, id_lecture=lecture_id)
        lecture = Lecture(data=links)
        return lecture

    @property
    def get_additional_files(self) -> dict[list]:
        """Retorna a lista de arquivos adcionais de um curso."""
        supplementary_assets = []
        for item in self.__results.get('results', []):
            # Check if the item is a lecture with supplementary assets
            if item.get('_class') == 'lecture':
                id = item.get('id')
                title = item.get('title')
                assets = item.get('supplementary_assets', [])
                for asset in assets:
                    supplementary_assets.append({
                        'lecture_id': id,
                        'lecture_title': title,
                        'asset': asset
                    })
        files = extract_files(supplementary_assets)
        files_objt = Files(files=files, id_course=self.__course_id).get_download_url
        return files_objt
