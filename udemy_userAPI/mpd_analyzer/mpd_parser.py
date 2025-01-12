import re
import xml.etree.ElementTree as Et


def calculate_segment_url2(media_template, segment_number, segment_time, rep_id):
    """
    Calcula a URL de um segmento específico, substituindo variáveis no template.
    """
    url = media_template.replace('$Number$', str(segment_number))
    url = url.replace('$RepresentationID$', rep_id)
    if '$Time$' in url:
        url = url.replace('$Time$', str(segment_time))
    return url


def build_url2(template, rep_id):
    """
    Constrói a URL substituindo variáveis no template com base nos atributos.
    """
    if '$RepresentationID$' in template:
        template = template.replace('$RepresentationID$', rep_id)
    return template


def parse_duration(duration_str):
    """
    Converte uma duração em formato ISO 8601 (ex: "PT163.633S") para segundos (float).
    """
    match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+(?:\.\d+)?)S)?', duration_str)
    if match:
        hours = int(match.group(1)) if match.group(1) else 0
        minutes = int(match.group(2)) if match.group(2) else 0
        seconds = float(match.group(3)) if match.group(3) else 0.0
        return hours * 3600 + minutes * 60 + seconds
    return 0.0


class MPDParser:
    """
    Classe para analisar e extrair informações de manifestos MPD (Media Presentation Description),
    com foco em arquivos VOD (Video on Demand). Atualmente, não oferece suporte para transmissões ao vivo.
    """

    def __init__(self, mpd_content: str):
        """
        Inicializa o parser para um arquivo MPD.

        Args:
            mpd_content (str): Caminho do arquivo MPD ou conteúdo bruto.
        """
        self._mpd_content = mpd_content
        self._video_representations = {}
        self._audio_representations = {}
        self._content_protection = {}
        self._selected_resolution = None

        # Tenta fazer o parsing com diferentes métodos
        if not self.__parse_mpd_v2():
            self.__parse_mpd_v1()

    def __parse_mpd_v1(self):
        """
        Parsing básico do MPD (versão 1).
        """
        content = self._mpd_content
        root = Et.fromstring(content)
        ns = {'dash': 'urn:mpeg:dash:schema:mpd:2011'}

        for adaptation_set in root.findall('.//dash:AdaptationSet', ns):
            mime_type = adaptation_set.attrib.get('mimeType', '')
            self.__parse_adaptation_set(adaptation_set, mime_type, ns)

    def __parse_mpd_v2(self):
        """
        Parsing avançado do MPD (versão 2).
        """
        content = self._mpd_content
        root = Et.fromstring(content)
        ns = {'dash': 'urn:mpeg:dash:schema:mpd:2011'}

        for adaptation_set in root.findall('.//dash:AdaptationSet', ns):
            mime_type = adaptation_set.attrib.get('mimeType', '')
            self.__parse_adaptation_set(adaptation_set, mime_type, ns)
        return True

    def __parse_adaptation_set(self, adaptation_set, mime_type, ns):
        """
        Analisa um AdaptationSet para representações de vídeo ou áudio.

        Args:
            adaptation_set (ET.Element): Elemento do AdaptationSet.
            mime_type (str): Tipo MIME (vídeo ou áudio).
            ns (dict): Namespace para parsing do XML.
        """
        # Extrai informações de proteção de conteúdo
        for content_protection in adaptation_set.findall('dash:ContentProtection', ns):
            scheme_id_uri = content_protection.attrib.get('schemeIdUri', '')
            value = content_protection.attrib.get('value', '')
            self._content_protection[scheme_id_uri] = value

        # Processa representações dentro do AdaptationSet
        for representation in adaptation_set.findall('dash:Representation', ns):
            self.__process_representation(representation, mime_type, ns)

    def __process_representation(self, representation, mime_type, ns):
        """
        Processa uma representação de mídia (vídeo ou áudio).

        Args:
            representation (ET.Element): Elemento da Representação.
            mime_type (str): Tipo MIME da mídia.
            ns (dict): Namespace para parsing do XML.
        """
        rep_id = representation.attrib.get('id')
        width = int(representation.attrib.get('width', 0))
        height = int(representation.attrib.get('height', 0))
        resolution = (width, height) if width and height else None
        bandwidth = int(representation.attrib.get('bandwidth', 0))

        # Extrai informações do SegmentTemplate
        segment_template = representation.find('dash:SegmentTemplate', ns)
        if segment_template:
            init_url = self.__build_url(segment_template.get('initialization'), rep_id, bandwidth)
            segments = self.__generate_segments(segment_template, ns, rep_id, bandwidth)

            representation_info = {
                'id': rep_id,
                'resolution': resolution,
                'bandwidth': bandwidth,
                'init_url': init_url,
                'segments': segments,
            }
            if 'video' in mime_type:
                self._video_representations[resolution] = representation_info
            elif 'audio' in mime_type:
                self._audio_representations[bandwidth] = representation_info

    def __generate_segments(self, segment_template, ns, rep_id, bandwidth):
        """
        Gera a lista de URLs de segmentos com base no SegmentTemplate.

        Args:
            segment_template (ET.Element): Elemento do SegmentTemplate.
            ns (dict): Namespace para parsing do XML.
            rep_id (str): ID da representação.
            bandwidth (int): Largura de banda da representação.

        Returns:
            list: URLs dos segmentos.
        """
        segments = []
        media_template = segment_template.get('media')
        segment_timeline = segment_template.find('dash:SegmentTimeline', ns)

        if segment_timeline:
            segment_number = int(segment_template.get('startNumber', 1))
            for segment in segment_timeline.findall('dash:S', ns):
                t = int(segment.get('t', 0))
                d = int(segment.get('d'))
                r = int(segment.get('r', 0))
                for i in range(r + 1):
                    segment_time = t + i * d
                    segments.append(self.__build_url(media_template, rep_id, bandwidth, segment_time, segment_number))
                    segment_number += 1
        return segments

    @staticmethod
    def __build_url(template, rep_id, bandwidth, segment_time=None, segment_number=None):
        """
        Constrói uma URL substituindo placeholders.

        Args:
            template (str): Template de URL.
            rep_id (str): ID da representação.
            bandwidth (int): Largura de banda.
            segment_time (int, opcional): Timestamp do segmento.
            segment_number (int, opcional): Número do segmento.

        Returns:
            str: URL formatada.
        """
        url = template.replace('$RepresentationID$', rep_id).replace('$Bandwidth$', str(bandwidth))
        if segment_time is not None:
            url = url.replace('$Time$', str(segment_time))
        if segment_number is not None:
            url = url.replace('$Number$', str(segment_number))
        return url

    def set_selected_resolution(self, resolution: tuple):
        """
        Define a resolução selecionada para a recuperação de segmentos de vídeo.

        Args:
            resolution (tuple): Resolução desejada (largura, altura).

        Raises:
            Exception: Se a resolução não estiver disponível no manifesto.
        """
        if resolution in self._video_representations:
            self._selected_resolution = resolution
        else:
            raise Exception(
                f'A resolução {resolution} não está disponível!\n\n'
                f'\t=> Resoluções disponíveis no arquivo: {self.get_all_video_resolutions()}')

    def get_selected_video_init_url(self):
        """
        Retorna o URL de inicialização para a resolução de vídeo selecionada.

        Returns:
            str: URL de inicialização do vídeo, ou None se não houver resolução selecionada.
        """
        if self._selected_resolution:
            return self._video_representations[self._selected_resolution].get('init_url')
        return None

    def get_all_video_resolutions(self):
        """
        Retorna uma lista de todas as resoluções de vídeo disponíveis.

        Returns:
            list: lista de tuplas com resoluções de vídeo (largura, altura).
        """
        return list(self._video_representations.keys())
