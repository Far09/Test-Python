# Portal Chamados

Programa para acessar o Portal de Serviços DF, autenticar com usuário/senha e listar chamados em aberto.

## Uso com Python

```bash
python portal_chamados.py --usuario SEU_USUARIO --senha SUA_SENHA
```

Opcional:

```bash
python portal_chamados.py --usuario SEU_USUARIO --senha SUA_SENHA --mostrar-navegador
```

## Gerar executável

### Linux/macOS

```bash
./build_executaveis.sh
```

O binário será criado em `dist/portal-chamados`.

### Windows (PowerShell)

```powershell
./build_executaveis.ps1
```

O executável será criado em `dist/portal-chamados.exe`.

## Dependências de execução

- O programa usa Playwright.
- Para rodar via Python ou executável, instale os browsers uma vez no ambiente:

```bash
playwright install chromium
```
