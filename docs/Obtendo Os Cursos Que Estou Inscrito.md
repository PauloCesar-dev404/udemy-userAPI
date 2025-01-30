# Obtendo os Cursos que Estou Inscrito

Este exemplo demonstra como obter os cursos que um usuário está inscrito na Udemy. Existem duas categorias de cursos:

1. **Cursos por Plano**: Cursos com acesso limitado, geralmente através de um plano de assinatura.
2. **Cursos Normais (Default)**: Cursos adquiridos individualmente ou que o usuário se inscreveu gratuitamente.

> **Atenção**: Certifique-se sempre de estar autenticado antes de realizar qualquer operação.

## Exemplo de Código

O código a seguir mostra como verificar se o usuário está logado e, em seguida, obter as listas de cursos em que está inscrito.

```python
import udemy_userAPI

# Instancia o objeto principal da API Udemy
udemy = udemy_userAPI.Udemy()

# Autenticação do usuário
auth = udemy_userAPI.UdemyAuth()

# Verifica se o login foi bem-sucedido
is_login = auth.verif_login()

if is_login:
    # Exibe os cursos por plano de assinatura
    print("Cursos por plano:", udemy.my_subscribed_courses_by_plan())
    
    # Exibe os cursos normais (adquiridos ou gratuitos)
    print("Cursos default:", udemy.my_subscribed_courses())
    
else:
    print("Não está Logado...")
```

# Explicação
- Autenticação: Antes de acessar qualquer dado, é necessário garantir que o usuário está autenticado com sucesso. Isso é feito por `uth.verif_login`.
`udemy.my_subscribed_courses_by_plan`: Retorna a lista de cursos aos quais o usuário tem acesso via um plano de assinatura.
`udemy.my_subscribed_courses`: Retorna a lista de cursos adquiridos ou cursos gratuitos aos quais o usuário se inscreveu.

# Observações
- Cursos por Plano: A lista de cursos exibidos em `my_subscribed_courses_by_plan` representa os cursos acessíveis por um período limitado, dependendo do plano de assinatura.
- Cursos Normais (Default): A lista de `my_subscribed_courses` inclui cursos que foram adquiridos permanentemente ou aqueles em que o usuário se inscreveu gratuitamente.

# Erros Possíveis
- Não está logado: Se o login não for bem-sucedido, a operação falhará. Verifique suas credenciais de login.
- Listas vazias: Se nenhuma lista de cursos for retornada, o usuário pode não estar inscrito em cursos por plano ou cursos normais.