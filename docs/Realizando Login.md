# Realizando Login
Para usar é necessário realizar login na pltaforma usando a classe `UdemyAuth`

```python
import udemy_userAPI

auth = udemy_userAPI.UdemyAuth()
login = auth.login(email='',password='')
is_login = auth.verif_login

if is_login:
    print("Logado!")
else:
    print("Não estar Logado...")

```
## parâmetros :
- email: email do usuário cuja teha acesso a plataforma .
- password: a senha do usuário

você pode verificar se um usuário estar logado usando `verif_login` que retorna um bool

## outras funcioaliddes :
você pode obter os seus cookies de seção usando `load_cookies` que retorna em uma string os cokies de seção.
