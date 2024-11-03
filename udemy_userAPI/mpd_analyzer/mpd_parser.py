import re
import xml.etree.ElementTree as ET


class MPDParser:
    """
    Classe para analisar e extrair informações de manifestos MPD (Media Presentation Description),
    com foco em arquivos VOD (Video on Demand). Atualmente, não oferece suporte para transmissões ao vivo
    """

    def __init__(self, mpd_file_path: str, headers=None,is_file=None):
        """
        Inicializa o parser para um arquivo MPD a partir de um caminho de arquivo.

        Args:
            mpd_file_path (str): Caminho do arquivo MPD.
            headers (dict, opcional): Headers HTTP adicionais para requisição, caso necessário.
        """
        self.is_file = is_file
        self.availability_start_time = None
        self.mpd_file_path = mpd_file_path
        self.headers = headers if headers else {}
        self.video_representations = {}  # Armazena representações de vídeo, organizadas por resolução
        self.audio_representations = {}  # Armazena representações de áudio, organizadas por taxa de bits
        self.content_protection = {}  # Armazena informações de proteção de conteúdo
        self.selected_resolution = None  # Resolução selecionada para recuperação de segmentos de vídeo
        self.initi = self.__parse_mpd2()
        if not self.initi:
            initi = self.__parse_mpd()

    def __parse_mpd(self):
        """
        Faz o parsing do arquivo MPD localizado no caminho especificado e
        extrai informações sobre segmentos de vídeo e áudio, além de proteção de conteúdo.
        """
        mpd_content = ''
        if not self.is_file:
            try:
                    with open(self.mpd_file_path, 'r', encoding='utf-8') as file:
                        mpd_content = file.read()
            except FileNotFoundError:
                    print(f"Erro: Arquivo '{self.mpd_file_path}' não encontrado.")
                    return
            except IOError:
                    print(f"Erro ao ler o arquivo '{self.mpd_file_path}'.")
                    return
        else:
            mpd_content = self.mpd_file_path
        # Analisa o conteúdo MPD usando namespaces XML para acessar nós DASH
        root = ET.fromstring(mpd_content)
        ns = {'dash': 'urn:mpeg:dash:schema:mpd:2011'}

        # Processa cada AdaptationSet para extração de representações de áudio e vídeo
        for adaptation_set in root.findall('.//dash:AdaptationSet', ns):
            mime_type = adaptation_set.attrib.get('mimeType', '')
            # Extrai informações de proteção de conteúdo, se presentes
            for content_protection in adaptation_set.findall('dash:ContentProtection', ns):
                scheme_id_uri = content_protection.attrib.get('schemeIdUri', '')
                value = content_protection.attrib.get('value', '')
                self.content_protection[scheme_id_uri] = value

            # Extrai informações de cada representação de mídia
            for representation in adaptation_set.findall('dash:Representation', ns):
                rep_id = representation.attrib.get('id')
                width = int(representation.attrib.get('width', 0))
                height = int(representation.attrib.get('height', 0))
                resolution = (width, height) if width and height else None
                bandwidth = int(representation.attrib.get('bandwidth', 0))
                # Obtém a quantidade de canais de áudio, se disponível
                audio_channels = representation.find('dash:AudioChannelConfiguration', ns)
                audio_channels_count = int(audio_channels.attrib.get('value', 0)) if audio_channels is not None else 0

                # Processa SegmentTemplate para URLs de inicialização e segmentos
                segment_template = representation.find('dash:SegmentTemplate', ns)
                if segment_template is not None:
                    init_template = segment_template.get('initialization')
                    init_url = self.__build_url(init_template, rep_id, bandwidth) if init_template else None

                    media_url_template = segment_template.get('media')
                    timescale = int(segment_template.get('timescale', 1))

                    # Processa SegmentTimeline para obtenção de segmentos individuais
                    segment_timeline = segment_template.find('dash:SegmentTimeline', ns)
                    segments = []
                    if segment_timeline is not None:
                        segment_number = int(segment_template.get('startNumber', 1))
                        start_time = 0
                        for segment in segment_timeline.findall('dash:S', ns):
                            t = int(segment.get('t', start_time))
                            d = int(segment.get('d'))
                            r = int(segment.get('r', 0))

                            # Adiciona segmentos repetidos se necessário
                            for _ in range(r + 1):
                                segments.append(
                                    self.__calculate_segment_url(media_url_template, segment_number, t, rep_id,
                                                                 bandwidth)
                                )
                                t += d
                                segment_number += 1

                    # Armazena informações de representação com resolução ou taxa de bits como chave
                    representation_info = {
                        'id': rep_id,
                        'resolution': resolution,
                        'bandwidth': bandwidth,
                        'audio_channels': audio_channels_count,
                        'init_url': init_url,
                        'segments': segments,
                    }
                    if 'video' in mime_type:
                        self.video_representations[resolution] = representation_info
                    elif 'audio' in mime_type:
                        self.audio_representations[bandwidth] = representation_info

    def __parse_mpd2(self):
        """
        Faz o parsing do arquivo MPD localizado no caminho especificado e
        extrai informações sobre segmentos de vídeo e áudio, além de proteção de conteúdo.
        """
        mpd_content = ''
        if not self.is_file:
            try:
                    with open(self.mpd_file_path, 'r', encoding='utf-8') as file:
                        mpd_content = file.read()
            except FileNotFoundError:
                    print(f"Erro: Arquivo '{self.mpd_file_path}' não encontrado.")
                    return
            except IOError:
                    print(f"Erro ao ler o arquivo '{self.mpd_file_path}'.")
                    return
        else:
            mpd_content = self.mpd_file_path

        # Analisar o conteúdo MPD
        root = ET.fromstring(mpd_content)
        ns = {'dash': 'urn:mpeg:dash:schema:mpd:2011'}

        # Extrai a duração total da apresentação em segundos
        self.media_presentation_duration = self.parse_duration(root.attrib.get('mediaPresentationDuration', 'PT0S'))

        for adaptation_set in root.findall('.//dash:AdaptationSet', ns):
            mime_type = adaptation_set.attrib.get('mimeType', '')

            # Extrai proteção de conteúdo
            for content_protection in adaptation_set.findall('dash:ContentProtection', ns):
                scheme_id_uri = content_protection.attrib.get('schemeIdUri', '')
                value = content_protection.attrib.get('value', '')
                self.content_protection[scheme_id_uri] = value

            # Extrai representações de vídeo e áudio
            for representation in adaptation_set.findall('dash:Representation', ns):
                rep_id = representation.attrib.get('id')
                width = int(representation.attrib.get('width', 0))
                height = int(representation.attrib.get('height', 0))
                resolution = (width, height) if width and height else None
                bandwidth = int(representation.attrib.get('bandwidth', 0))

                # SegmentTemplate e SegmentTimeline
                segment_template = adaptation_set.find('dash:SegmentTemplate', ns)
                if segment_template is not None:
                    init_template = segment_template.get('initialization')
                    media_template = segment_template.get('media')
                    timescale = int(segment_template.get('timescale', 1))
                    start_number = int(segment_template.get('startNumber', 1))

                    # Processa SegmentTimeline
                    segment_timeline = segment_template.find('dash:SegmentTimeline', ns)
                    segments = []
                    if segment_timeline is not None:
                        segment_number = start_number
                        for segment in segment_timeline.findall('dash:S', ns):
                            t = int(segment.get('t', 0))
                            d = int(segment.get('d'))
                            r = int(segment.get('r', 0))  # Quantidade de repetições

                            for i in range(r + 1):  # Inclui o segmento e suas repetições
                                segment_time = t + i * d
                                segment_url = self.__calculate_segment_url2(media_template, segment_number, segment_time,
                                                                         rep_id)
                                segments.append(segment_url)
                                segment_number += 1
                    else:
                        # No SegmentTimeline, gera segmentos contínuos
                        duration = int(segment_template.get('duration', 1))
                        total_segments = int((self.media_presentation_duration * timescale) // duration)
                        for segment_number in range(start_number, start_number + total_segments):
                            segment_time = (segment_number - 1) * duration
                            segment_url = self.__calculate_segment_url2(media_template, segment_number, segment_time,
                                                                     rep_id)
                            segments.append(segment_url)

                    # Armazena representações de vídeo e áudio com URLs de segmentos
                    representation_info = {
                        'id': rep_id,
                        'resolution': resolution,
                        'bandwidth': bandwidth,
                        'init_url': self.__build_url2(init_template, rep_id),
                        'segments': segments,
                    }
                    if 'video' in mime_type:
                        self.video_representations[resolution] = representation_info
                    elif 'audio' in mime_type:
                        self.audio_representations[bandwidth] = representation_info
    def parse_duration(self, duration_str):
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

    @staticmethod
    def __build_url(template, rep_id, bandwidth):
        """
        Constrói uma URL substituindo placeholders em um template de URL.

        Args:
            template (str): Template de URL com placeholders.
            rep_id (str): ID da representação.
            bandwidth (int): Largura de banda da representação.

        Returns:
            str: URL formatada com placeholders substituídos.
        """
        if '$RepresentationID$' in template:
            template = template.replace('$RepresentationID$', rep_id)
        if '$Bandwidth$' in template:
            template = template.replace('$Bandwidth$', str(bandwidth))
        return template

    def __build_url2(self, template, rep_id):
        """
        Constrói a URL substituindo variáveis no template com base nos atributos.
        """
        if '$RepresentationID$' in template:
            template = template.replace('$RepresentationID$', rep_id)
        return template

    @staticmethod
    def __calculate_segment_url(media_template, segment_number, segment_time, rep_id, bandwidth):
        """
        Constrói a URL de um segmento substituindo placeholders por valores reais.

        Args:
            media_template (str): Template de URL do segmento.
            segment_number (int): Número do segmento.
            segment_time (int): Timestamp do segmento.
            rep_id (str): ID da representação.
            bandwidth (int): Largura de banda da representação.

        Returns:
            str: URL do segmento com placeholders substituídos.
        """
        url = media_template.replace('$Number$', str(segment_number))
        url = url.replace('$RepresentationID$', rep_id).replace('$Bandwidth$', str(bandwidth))
        if '$Time$' in url:
            url = url.replace('$Time$', str(segment_time))
        return url

    def __calculate_segment_url2(self, media_template, segment_number, segment_time, rep_id):
        """
        Calcula a URL de um segmento específico, substituindo variáveis no template.
        """
        url = media_template.replace('$Number$', str(segment_number))
        url = url.replace('$RepresentationID$', rep_id)
        if '$Time$' in url:
            url = url.replace('$Time$', str(segment_time))
        return url

    def get_video_representations(self):
        """
        Retorna as representações de vídeo extraídas do arquivo MPD.

        Returns:
            dict: Representações de vídeo com resoluções como chaves.
        """
        return self.video_representations

    def get_audio_representations(self):
        """
        Retorna as representações de áudio extraídas do arquivo MPD.

        Returns:
            dict: Representações de áudio com taxas de bits como chaves.
        """
        return self.audio_representations

    def get_content_protection_info(self):
        """
        Retorna as informações de proteção de conteúdo extraídas do MPD.

        Returns:
            dict: Dados de proteção de conteúdo com URI do esquema como chaves.
        """
        return self.content_protection

    def set_selected_resolution(self, resolution: tuple):
        """
        Define a resolução selecionada para a recuperação de segmentos de vídeo.

        Args:
            resolution (tuple): Resolução desejada (largura, altura).

        Raises:
            Exception: Se a resolução não estiver disponível no manifesto.
        """
        if resolution in self.video_representations:
            self.selected_resolution = resolution
        else:
            raise Exception(
                f'A resolução {resolution} não está disponível!\n\n\t=> Resoluções disponíveis no arquivo: {self.get_all_video_resolutions()}')

    def get_selected_video_segments(self):
        """
        Retorna os URLs dos segmentos de vídeo para a resolução selecionada.

        Returns:
            list: URLs dos segmentos de vídeo para a resolução selecionada.
        """
        if self.selected_resolution:
            return self.video_representations[self.selected_resolution].get('segments', [])
        else:
            raise Exception(f'Você deve selecioanar uma resolução no método self.set_selected_resolution()')

    def get_selected_video_init_url(self):
        """
        Retorna o URL de inicialização para a resolução de vídeo selecionada.

        Returns:
            str: URL de inicialização do vídeo, ou None se não houver resolução selecionada.
        """
        if self.selected_resolution:
            return self.video_representations[self.selected_resolution].get('init_url')
        return None

    def get_all_video_resolutions(self):
        """
        Retorna uma lista de todas as resoluções de vídeo disponíveis.

        Returns:
            list: Lista de tuplas com resoluções de vídeo (largura, altura).
        """
        return list(self.video_representations.keys())

    def get_audio_channels_count(self):
        """
        Retorna um dicionário com a quantidade de canais de áudio para cada taxa de bits de áudio.

        Returns:
            dict: Quantidade de canais de áudio para cada taxa de bits.
        """
        return {bandwidth: info['audio_channels'] for bandwidth, info in self.audio_representations.items()}
