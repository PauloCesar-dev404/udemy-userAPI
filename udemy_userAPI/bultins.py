import json
from typing import Any
import requests
from .api import get_links, remove_tag, parser_chapers, extract_files, HEADERS_USER, assets_infor, get_add_files, \
    get_files_aule, get_external_liks, extract, get_pssh, organize_streams, get_mpd_file, get_highest_resolution
from .sections import get_course_infor
from .mpd_analyzer import MPDParser


class DRM:
    def __init__(self, license_token: str, get_media_sources: list):
        self.__mpd_content = None
        self.__dash_url = organize_streams(streams=get_media_sources).get('dash')
        self.__token = license_token
        self.get_key_for_lesson()

    def get_key_for_lesson(self):
        """get keys for lesson"""
        if self.__dash_url:
            self.__mpd_content = get_mpd_file(mpd_url=self.__dash_url[0].get('src'))
            parser = MPDParser(mpd_file_path=self.__mpd_content, is_file=True, headers=HEADERS_USER)
            resolutions = get_highest_resolution(parser.get_all_video_resolutions())
            parser.set_selected_resolution(resolution=resolutions)
            init_url = parser.get_selected_video_init_url()
            if init_url:
                pssh = get_pssh(init_url=init_url)
                if pssh:
                    keys = extract(pssh=pssh, license_token=self.__token)
                    if keys:
                        return keys


class Files:
    def __init__(self, files: list[dict], id_course):
        self.__data = files
        self.__id_course = id_course

    @property
    def get_download_url(self) -> dict[str, Any | None] | list[dict[str, Any | None]]:
        """obter url de download de um arquivo quando disponivel(geralemnete para arquivos esta opção é valida"""
        da = {}
        download_urls = []
        for files in self.__data:
            lecture_id = files.get('lecture_id', None)
            asset_id = files.get('asset_id', None)
            title = files.get("title", None)
            lecture_title = files.get('lecture_title')
            external_link = files.get('ExternalLink')
            if external_link:
                lnk = get_external_liks(course_id=self.__id_course, id_lecture=lecture_id, asset_id=asset_id)
                dt_file = {'title-file': title, 'lecture_title': lecture_title, 'lecture_id': lecture_id,
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
                    ## para cdaa dict de um fle colocar seu titulo:
                    dt_file = {'title-file': title, 'lecture_title': lecture_title, 'lecture_id': lecture_id,
                               'external_link': external_link,
                               'data-file': da['download_urls']}
                    download_urls.append(dt_file)
        return download_urls


class Lecture:
    """CRIAR objetos aula(lecture) do curso e extrair os dados.."""

    def __init__(self, data: dict, course_id: int, additional_files):
        self.__course_id = course_id
        self.__data = data
        self.__additional_files = additional_files
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

    def course_is_drmed(self) -> DRM:
        """verifica se a aula possui DRM se sim retorna as keys da aula...
         retorna 'kid:key' or None"""
        if self.__asset.get('course_is_drmed'):
            d = DRM(license_token=self.get_media_license_token,
                    get_media_sources=self.get_media_sources)
            return d
        else:
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

    @property
    def get_articles(self):
        d = assets_infor(course_id=self.__course_id, id_lecture=self.get_lecture_id, assets_id=self.__asset.get("id"))
        return d

    @property
    def get_resources(self):
        """obtem os recurso adconais reaioanddos a aula"""
        files_add = get_files_aule(lecture_id_filter=self.get_lecture_id, data=self.__additional_files)
        f = Files(files=files_add, id_course=self.__course_id).get_download_url
        return f


class Course:
    """receb um dict com os dados do curso"""

    def __init__(self, results: dict, course_id: int):
        self.__parser_chapers = parser_chapers(results=results)
        self.__data = self.__parser_chapers
        self.__course_id = course_id
        self.__results = results
        self.__additional_files_data = get_add_files(course_id)
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
        """Obtém uma lista com todas as aulas."""
        videos = []
        section_order = 1  # Iniciar a numeração das seções (capítulos)

        for chapter in self.__data.values():
            for index, video in enumerate(chapter.get('videos_in_chapter', [])):
                section = f"{section_order} {chapter.get('title_chapter')}"  # Adicionar numeração da seção
                title = video.get('video_title')
                id_lecture = video.get('lecture_id')
                id_asset = video.get('asset_id')
                dt = {
                    'section': section,
                    'title': title,
                    'lecture_id': id_lecture,
                    'asset_id': id_asset,
                    'section_order': section_order,
                    'lecture_order': index + 1  # Numeração da seção e vídeo
                }
                videos.append(dt)
            section_order += 1  # Incrementar o número da seção após processar os vídeos do capítulo
        return videos

    def get_details_lecture(self, lecture_id: int) -> Lecture:
        """obter detalhes de uma aula específica, irá retornar o objeto Lecture"""
        links = get_links(course_id=self.__course_id, id_lecture=lecture_id)
        additional_files = self.__load_assets()
        # print(f'DEBUG files passados a lecture:\n{additional_files}\n\n')
        lecture = Lecture(data=links, course_id=self.__course_id, additional_files=additional_files)
        return lecture

    @property
    def get_additional_files(self) -> list[Any]:
        """Retorna a lista de arquivos adcionais de um curso."""
        supplementary_assets = []
        files_downloader = []
        for item in self.__additional_files_data.get('results', []):
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
        # print(f'DEBUG files:\n{files}\n\n')
        files_objt = Files(files=files, id_course=self.__course_id).get_download_url
        return files_objt

    def __load_assets(self):
        """Retorna a lista de arquivos adcionais de um curso."""
        supplementary_assets = []
        files_downloader = []
        for item in self.__additional_files_data.get('results', []):
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
        return files
