import json
import os
import pickle
import traceback
import hashlib
import hmac
import math
from datetime import datetime
import requests
from .exeptions import UnhandledExceptions, UdemyUserApiExceptions, LoginException
import cloudscraper

DEBUG = False


class UdemyAuth:
    def __init__(self):
        """Autenticação na plataforma udemy de maneira segura, atencao ao limite de logins,recomendo que apos logar
        nao use novamnete o metodo login use apenas o verifcador de login para evitar bloqueios temporários..."""
        self.__cookie_dict = {}
        # Diretório do arquivo atual
        current_directory = os.path.dirname(__file__)
        # dir cache
        cache = '.cache'
        cache_dir = os.path.join(current_directory, cache)
        os.makedirs(cache_dir, exist_ok=True)
        # Cria o diretório completo para a API do usuário
        self.__user_dir = os.path.join(cache_dir)
        # Cria o caminho completo para um arquivo específico
        file_name = '.udemy_userAPI'  # Nome do arquivo
        self.__file_path = os.path.join(self.__user_dir, file_name)

    def verif_login(self):
        """verificar se o usuario estar logado."""

        def verif_config():
            # Verificar se o arquivo .userLogin existe e carregar cookies se existir
            try:
                with open(fr'{self.__file_path}', 'rb') as f:
                    cookies = pickle.load(f)
                    cookies_dict = {cookie.name: cookie.value for cookie in cookies}
                    cookies_str = "; ".join([f"{key}={value}" for key, value in cookies_dict.items()])
                    return cookies_str
            except Exception as e:
                if DEBUG:
                    e = traceback.format_exc()
                    raise LoginException(e)
                return False

        log = verif_config()

        if log:
            cookies_de_secao = log
            headers = {
                "accept": "*/*",
                "accept-language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
                "cache-control": "no-cache",
                "Content-Type": "text/plain",
                "pragma": "no-cache",
                "sec-ch-ua": "\"Chromium\";v=\"118\", \"Google Chrome\";v=\"118\", \"Not=A?Brand\";v=\"99\"",
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": "\"Windows\"",
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "cross-site",
                "Cookie": cookies_de_secao,
                "Referer": "https://www.udemy.com/"
            }

            try:
                url = 'https://www.udemy.com/api-2.0/contexts/me/?header=true'
                resp = requests.get(url=url, headers=headers)
                if resp.status_code == 200:
                    convert = json.loads(resp.text)
                    isLoggedIn = convert.get('header', {}).get('isLoggedIn', False)
                    if isLoggedIn:
                        if isLoggedIn == True:
                            return True
                        else:
                            return False
                    else:
                        raise LoginException(f"Erro Ao obter login atualize a lib! -> {convert}")
            except requests.ConnectionError as e:
                raise UdemyUserApiExceptions(f"Erro de conexão: {e}")
            except requests.Timeout as e:
                raise UdemyUserApiExceptions(f"Tempo de requisição excedido: {e}")
            except requests.TooManyRedirects as e:
                raise UdemyUserApiExceptions(f"Limite de redirecionamentos excedido: {e}")
            except requests.HTTPError as e:
                raise UdemyUserApiExceptions(f"Erro HTTP: {e}")
            except Exception as e:
                raise UnhandledExceptions(f"Unhandled-ERROR: {e}")
        else:
            return False

    def login(self, email: str, password: str):
        """efetuar login na udemy"""
        try:
            # Inicializa uma sessão usando cloudscraper para contornar a proteção Cloudflare
            s = cloudscraper.create_scraper()

            # Faz uma requisição GET à página de inscrição para obter o token CSRF
            r = s.get(
                "https://www.udemy.com/join/signup-popup/",
                headers={"User-Agent": "okhttp/4.9.2 UdemyAndroid 8.9.2(499) (phone)"},
            )

            # Extrai o token CSRF dos cookies
            csrf_token = r.cookies["csrftoken"]

            # Prepara os dados para o login
            data = {
                "csrfmiddlewaretoken": csrf_token,
                "locale": "pt_BR",
                "email": email,
                "password": password,
            }

            # Atualiza os cookies e cabeçalhos da sessão
            s.cookies.update(r.cookies)
            s.headers.update(
                {
                    "User-Agent": "okhttp/4.9.2 UdemyAndroid 8.9.2(499) (phone)",
                    "Accept": "application/json, text/plain, */*",
                    "Accept-Language": "en-GB,en;q=0.5",
                    "Referer": "https://www.udemy.com/join/login-popup/?locale=en_US&response_type=html&next=https%3A%2F"
                               "%2Fwww.udemy.com%2F",
                    "Origin": "https://www.udemy.com",
                    "DNT": "1",
                    "Connection": "keep-alive",
                    "Sec-Fetch-Dest": "empty",
                    "Sec-Fetch-Mode": "cors",
                    "Sec-Fetch-Site": "same-origin",
                    "Pragma": "no-cache",
                    "Cache-Control": "no-cache",
                }
            )

            # Tenta fazer login com as credenciais fornecidas
            r = s.post(
                "https://www.udemy.com/join/login-popup/?response_type=json",
                data=data,
                allow_redirects=False,
            )

            # Verifica a resposta para determinar se o login foi bem-sucedido
            if "returnUrl" in r.text:
                self._save_cookies(s.cookies)
            else:
                login_error = r.json().get("error", {}).get("data", {}).get("formErrors", [])[0]
                if login_error[0] == "Y":
                    raise LoginException("Você excedeu o número máximo de solicitações por hora.")
                elif login_error[0] == "T":
                    raise LoginException("Email ou senha incorretos")
                else:
                    raise UnhandledExceptions(login_error)
        except Exception as e:
            if DEBUG:
                e = traceback.format_exc()
            raise LoginException(e)

    def _save_cookies(self, cookies):
        try:
            with open(fr'{self.__file_path}', 'wb') as f:
                pickle.dump(cookies, f)
        except Exception as e:
            raise LoginException(e)

    @property
    def load_cookies(self) -> str:
        """Carrega cookies e retorna-os em uma string formatada"""
        try:
            file = os.path.join(self.__file_path)
            if os.path.exists(file) and os.path.getsize(file) > 0:  # Verifica se o arquivo existe e não está vazio
                with open(file, 'rb') as f:
                    cookies = pickle.load(f)
                # Converte cookies em formato de string
                cookies_dict = {cookie.name: cookie.value for cookie in cookies}
                cookies_str = "; ".join([f"{key}={value}" for key, value in cookies_dict.items()])
                return cookies_str
            else:
                return ""  # Retorna uma string vazia se o arquivo não existir ou estiver vazio
        except (EOFError, pickle.UnpicklingError):  # Trata arquivos vazios ou corrompidos
            return ""  # Retorna uma string vazia
        except Exception as e:
            if DEBUG:
                e = traceback.format_exc()
            raise LoginException(f"Erro ao carregar cookies: {e}")

    def remove_cookies(self):
        if os.path.exists(self.__file_path):
            with open(self.__file_path, 'wb') as f:
                f.write(b'')

    def login_passwordless(self, email: str, locale: str = 'pt-BR'):
        """
        Realiza login na Udemy usando autenticação de dois fatores (2FA).

        Este método utiliza o fluxo de autenticação OAuth da Udemy para enviar um
        código de verificação por e-mail ao usuário. Após inserir o código recebido,
        o login é concluído.

        :param email: Email do usuário.
        :param locale: Localização do usuário (recomendado para receber mensagens no idioma local).
        :raises LoginException: Em caso de falha no processo de login.
        """
        try:
            # Inicializa uma sessão com proteção contra Cloudflare
            session = cloudscraper.create_scraper()

            # Requisita a página de inscrição para obter o token CSRF
            signup_url = "https://www.udemy.com/join/signup-popup/"
            headers = {"User-Agent": "okhttp/4.9.2 UdemyAndroid 8.9.2(499) (phone)"}
            response = session.get(signup_url, headers=headers)

            # Obtém o token CSRF dos cookies retornados
            csrf_token = response.cookies.get("csrftoken")
            if not csrf_token:
                raise LoginException("Não foi possível obter o token CSRF.")

            # Prepara os dados do login
            data = {"email": email, "fullname": ""}

            # Atualiza os cookies e cabeçalhos da sessão
            session.cookies.update(response.cookies)
            session.headers.update({
                "User-Agent": "okhttp/4.9.2 UdemyAndroid 8.9.2(499) (phone)",
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": locale,
                "Referer": f"https://www.udemy.com/join/passwordless-auth/?locale={locale.replace('-', '_')}&next="
                           f"https%3A%2F%2Fwww.udemy.com%2Fmobile%2Fipad%2F&response_type=html",
                "Origin": "https://www.udemy.com",
                "DNT": "1",
                "Connection": "keep-alive",
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-origin",
                "Pragma": "no-cache",
                "Cache-Control": "no-cache",
            })

            # Faz a requisição para iniciar o login
            login_url = "https://www.udemy.com/api-2.0/auth/code-generation/login/4.0/"
            response = session.post(login_url, data=data, allow_redirects=False)
            if 'error_message' in response.text:
                erro_data: dict = response.json()
                error_message = erro_data.get('error_message', {})
                raise LoginException(error_message)
            for attempt in range(3):
                # Solicita o código OTP ao usuário
                otp = input("Digite o código de 6 dígitos enviado ao seu e-mail: ")
                # Realiza o login com o código OTP
                otp_login_url = "https://www.udemy.com/api-2.0/auth/udemy-passwordless/login/4.0/"
                otp_data = {
                    "email": email,
                    "fullname": "",
                    "otp": otp,
                    "subscribeToEmails": "false",
                    "upow": J(email, 'login')
                }
                session.headers.update({
                    "Referer": f"https://www.udemy.com/join/passwordless-auth/?locale={locale}&next="
                               f"https%3A%2F%2Fwww.udemy.com%2Fmobile%2Fipad%2F&response_type=html"
                })
                response = session.post(otp_login_url, otp_data, allow_redirects=False)
                # Verifica se o login foi bem-sucedido
                if response.status_code == 200:
                    self._save_cookies(session.cookies)
                else:
                    if 'error_message' in response.text:
                        erro_data: dict = response.json()
                        error_message = erro_data.get('error_message', {})
                        error_code = erro_data.get('error_code', {})
                        if error_code == '1538':
                            raise LoginException(error_message)
                        elif error_code == '2550':
                            print(error_message)
                            continue
                        elif error_code == '1330':
                            raise LoginException(error_message)
                        elif error_code == '1149':
                            LoginException(f"Erro interno ao enviar os dados veja os detalhes: '{error_message}'")
                    raise LoginException(response.text)
                break
        except Exception as e:
            if DEBUG:
                error_details = traceback.format_exc()
            else:
                error_details = str(e)
            raise LoginException(error_details)


def J(e, t):
    r = datetime.now()
    s = r.isoformat()[:10]
    return s + X(e, s, t)


def X(e, t, r):
    s = 0
    while True:
        o = ee(s)
        a = hmac.new(r.encode(), (e + t + o).encode(), hashlib.sha256).digest()
        if te(16, a):
            return o
        s += 1


def ee(e):
    if e < 0:
        return ""
    return ee(e // 26 - 1) + chr(65 + e % 26)


def te(e, t):
    r = math.ceil(e / 8)
    s = t[:r]
    o = ''.join(format(byte, '08b') for byte in s)
    return o.startswith('0' * e)
