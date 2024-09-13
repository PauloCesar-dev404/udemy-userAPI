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
- email: oo email do usuário cuja teha acesso a plataforma .
- password: a senha do usuário

voce pode veririfcar se um usuario estar logado usando `verif_login` que retorna um bool

## outras funcioaliddes :
voce pode obter os seus cookies ee secao usando `load_cookies` que retorn em uma string os cokies de seção.
