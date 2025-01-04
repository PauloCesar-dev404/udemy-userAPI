# Realizando Login

Para acessar a plataforma Udemy utilizando a classe `UdemyAuth`, existem duas formas de realizar o login:

### 1. **Login Convencional (Com Email e Senha)**

O login convencional exige que o usuário forneça seu e-mail e senha.

```python
from udemy_userAPI import UdemyAuth

auth = UdemyAuth()
login = auth.login(email='', password='')  # Substitua com suas credenciais
is_login = auth.verif_login()

if is_login:
    print("Logado!")
else:
    print("Não está Logado...")
```

#### Parâmetros:
- `email`: E-mail do usuário registrado na plataforma.
- `password`: Senha associada ao e-mail do usuário.

---

### 2. **Login Passwordless (Sem Senha)**

No login passwordless, o usuário recebe um código de verificação diretamente no e-mail para concluir o login, sem a necessidade de fornecer uma senha.

```python
from udemy_userAPI import UdemyAuth

auth = UdemyAuth()
login = auth.login_passwordless(email='', locale='en-US')  # Substitua com seu e-mail e localidade
is_login = auth.verif_login()

if is_login:
    print("Logado!")
else:
    print("Não está Logado...")
```

#### Parâmetros:
- `email`: E-mail do usuário registrado na plataforma.
- `locale` (Opcional): Localidade preferida para receber mensagens de erro ou instruções da API no idioma desejado (por exemplo, `en-US` para inglês ou `pt-BR` para português).

---
