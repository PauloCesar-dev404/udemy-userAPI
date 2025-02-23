import json
import os
import pickle
import traceback
import requests
from .exeptions import UnhandledExceptions, UdemyUserApiExceptions, LoginException, Upstreamconnecterror
import cloudscraper

DEBUG = False


class UdemyAuth:
    def __init__(self):
        """
        Autenticação na plataforma Udemy de maneira segura.
        Atenção ao limite de logins. Recomendo que após logar não use novamente o método login,
        use apenas o verificador de login para evitar bloqueios temporários.
        """
        self.__cookie_dict = {}
        current_directory = os.path.dirname(__file__)
        cache = '.cache'
        cache_dir = os.path.join(current_directory, cache)
        os.makedirs(cache_dir, exist_ok=True)
        self.__user_dir = os.path.join(cache_dir)
        file_name = '.udemy_userAPI'
        file_credenntials = '.udemy_Credentials'
        self.__file_path = os.path.join(self.__user_dir, file_name)
        self.__credentials_path = os.path.join(self.__user_dir, file_credenntials)

    def verif_login(self) -> bool:
        """
        Verifica se o usuário está logado.

        Returns:
            bool: True se o usuário estiver logado, False caso contrário.
        """

        def verif_config():
            """
            Verifica se o arquivo .userLogin existe e carrega cookies se existir.

            Returns:
                str: Cookies em formato de string ou False se não existir.
            """
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
                        if isLoggedIn is True:
                            return True
                        else:
                            return False
                    else:
                        return False
                else:
                    if 'error: 111' in resp.text:
                        raise Upstreamconnecterror(message=
                                                   'Erro ao se comunicar com o servidor remoto!')
                    elif 'upstream connect error or disconnect/reset before headers. reset reason: connection timeout' in resp.text:
                        raise Upstreamconnecterror(""
                                                   "Ocorreu uma  falha de tempo de resposta!")
                    else:
                        raise LoginException(f"Erro Ao obter login : {resp.text}")
            except requests.ConnectionError as e:
                raise UdemyUserApiExceptions(f"Erro de conexão: {e}")
            except requests.Timeout as e:
                raise UdemyUserApiExceptions(f"Tempo de requisição excedido: {e}")
            except requests.TooManyRedirects as e:
                raise UdemyUserApiExceptions(f"Limite de redirecionamentos excedido: {e}")
            except requests.HTTPError as e:
                raise UdemyUserApiExceptions(f"Erro HTTP: {e}")
            except Exception as e:
                raise UnhandledExceptions(f"{e}")
        else:
            return False

    def login(self, email: str, password: str, locale: str = 'pt_BR'):
        """
        Efetua login na Udemy.

        Args:
            email (str): Email do usuário.
            password (str): Senha do usuário.
            locale (str): Localidade. Padrão é 'pt_BR'.
        """
        try:
            if self.verif_login():
                raise UserWarning("Atenção, você já possui uma Sessão válida!")
            s = cloudscraper.create_scraper()
            r = s.get(
                "https://www.udemy.com/join/signup-popup/",
                headers={"User-Agent": "okhttp/4.9.2 UdemyAndroid 8.9.2(499) (phone)"},
            )
            csrf_token = r.cookies["csrftoken"]
            data = {
                "csrfmiddlewaretoken": csrf_token,
                "locale": locale,
                "email": email,
                "password": password,
            }
            s.cookies.update(r.cookies)
            s.headers.update(
                {
                    "User-Agent": "okhttp/4.9.2 UdemyAndroid 8.9.2(499) (phone)",
                    "Accept": "application/json, text/plain, */*",
                    "Accept-Language": "en-GB,en;q=0.5",
                    "Referer": "https://www.udemy.com/join/login-popup/?locale=en_US&response_type="
                               "html&next=https%3A%2F"
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

    def _load_cookies(self) -> str:
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

    def login_passwordless(self, email: str, locale: str = 'pt-BR', otp_callback=None):
        """
        Realiza login na Udemy usando autenticação de dois fatores (2FA).

        Este método utiliza o fluxo de autenticação OAuth da Udemy para enviar um
        código de verificação por e-mail ao usuário. Após inserir o código recebido,
        o login é concluído.

        Args:
            email (str): Email do usuário.
            locale (str): Localização do usuário (recomendado para receber mensagens no idioma local).
            otp_callback (callable, opcional): Função para obter o código OTP (se None, usa input padrão).

        Raises:
            LoginException: Em caso de falha no processo de login.
        """
        from .api import J
        try:
            if self.verif_login():
                raise UserWarning("Atenção, você já possui uma Sessão válida!")

            session = cloudscraper.create_scraper()
            signup_url = "https://www.udemy.com/join/signup-popup/"
            headers = {"User-Agent": "okhttp/4.9.2 UdemyAndroid 8.9.2(499) (phone)"}
            response = session.get(signup_url, headers=headers)
            csrf_token = response.cookies.get("csrftoken")
            if not csrf_token:
                raise LoginException("Não foi possível obter o token CSRF.")

            data = {"email": email, "fullname": ""}
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

            login_url = "https://www.udemy.com/api-2.0/auth/code-generation/login/4.0/"
            response = session.post(login_url, data=data, allow_redirects=False)

            if 'error_message' in response.text:
                erro_data: dict = response.json()
                error_message = erro_data.get('error_message', {})
                raise LoginException(error_message)

            for attempt in range(3):
                # Obtém o código OTP via callback ou terminal
                if otp_callback and callable(otp_callback):
                    otp = otp_callback()
                else:
                    otp = input("Digite o código de 6 dígitos enviado ao seu e-mail: ")
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

                if response.status_code == 200:
                    self._save_cookies(session.cookies)
                    break  # Sai do loop se o login for bem-sucedido
                else:
                    if 'error_message' in response.text:
                        erro_data: dict = response.json()
                        error_message = erro_data.get('error_message', {})
                        error_code = erro_data.get('error_code', {})

                        if error_code == '1538':
                            raise LoginException(error_message)
                        elif error_code == '2550':
                            ### codigo errado....
                            raise LoginException(error_message)
                        elif error_code == '1330':
                            raise LoginException(error_message)
                        elif error_code == '1149':
                            raise LoginException(
                                f"Erro interno ao enviar os dados, veja os detalhes: '{error_message}'")

                    raise LoginException(response.text)

        except Exception as e:
            error_details = traceback.format_exc() if DEBUG else str(e)
            raise LoginException(error_details)
