class UdemyUserApiExceptions(Exception):
    def __init__(self, message="Udemy_UserApi Generic Error!"):
        self.message = message
        super().__init__(self.message)


class Upstreamconnecterror(Exception):
    def __init__(self, message="Falha na conexão com o servidor!"):
        self.message = message
        super().__init__(self.message)


class UnhandledExceptions(Exception):
    def __init__(self, message="Error Unhandled!"):
        self.message = message
        super().__init__(self.message)


class LoginException(Exception):
    def __init__(self, message="Error Login!"):
        self.message = message
        super().__init__(self.message)
