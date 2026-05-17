#!/usr/bin/env python3
"""
Automação para acessar o Portal de Serviços (DF Economia) e listar chamados em aberto.

Requisitos:
  pip install playwright
  playwright install chromium

Uso:
  python portal_chamados.py --usuario SEU_USUARIO --senha SUA_SENHA
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from typing import List

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

LOGIN_URL = (
    "https://auth.economia.df.gov.br/auth/realms/run2biz/protocol/openid-connect/auth"
    "?client_id=front-manager"
    "&redirect_uri=https%3A%2F%2Fportalservicos.economia.df.gov.br%2Fselfservice%2Fpages%2FexperienceCenter%2FexperienceCenter.load"
    "&state=e5b5a5f6-c5af-4964-be08-ee1b0f8d3789"
    "&response_mode=fragment"
    "&response_type=code"
    "&scope=openid"
    "&nonce=c5497198-6c2f-463b-8af1-c8185d3b56ce"
)


@dataclass
class Chamado:
    local: str
    data_abertura: str
    categoria: str


def _normalizar_texto(txt: str) -> str:
    return re.sub(r"\s+", " ", txt).strip()


def _extrair_data(texto: str) -> str:
    padroes = [
        r"\b\d{2}/\d{2}/\d{4}\b",
        r"\b\d{2}-\d{2}-\d{4}\b",
        r"\b\d{4}-\d{2}-\d{2}\b",
    ]
    for p in padroes:
        m = re.search(p, texto)
        if m:
            return m.group(0)
    return "Não identificado"


def _buscar_por_rotulo(texto: str, rotulo: str) -> str:
    m = re.search(rf"{rotulo}\s*[:\-]\s*(.+?)(?:\||$)", texto, re.IGNORECASE)
    return _normalizar_texto(m.group(1)) if m else "Não identificado"


def extrair_chamados_da_tela(page) -> List[Chamado]:
    """
    Estratégia resiliente:
    - tenta localizar cards/linhas contendo termos relacionados a chamados em aberto
    - extrai local, data e categoria por heurísticas de texto
    """
    termos = ["aberto", "open", "chamado", "solicitação", "ticket"]
    seletores = [
        "tr",
        "tbody tr",
        "[role='row']",
        ".card",
        ".ticket",
        ".chamado",
        "li",
    ]

    candidatos_texto: List[str] = []
    for seletor in seletores:
        try:
            elementos = page.locator(seletor)
            total = min(elementos.count(), 300)
            for i in range(total):
                txt = _normalizar_texto(elementos.nth(i).inner_text())
                if not txt:
                    continue
                if any(t in txt.lower() for t in termos):
                    candidatos_texto.append(txt)
        except Exception:
            continue

    chamados: List[Chamado] = []
    vistos = set()
    for txt in candidatos_texto:
        if txt in vistos:
            continue
        vistos.add(txt)

        local = _buscar_por_rotulo(txt, "local")
        categoria = _buscar_por_rotulo(txt, "categoria")
        data = _buscar_por_rotulo(txt, "data(?: de abertura)?")
        if data == "Não identificado":
            data = _extrair_data(txt)

        chamados.append(Chamado(local=local, data_abertura=data, categoria=categoria))

    return chamados


def fazer_login_e_coletar(usuario: str, senha: str, headless: bool = True) -> List[Chamado]:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page()

        try:
            page.goto(LOGIN_URL, wait_until="networkidle", timeout=120_000)

            # Campos comuns do Keycloak
            page.locator("#username, input[name='username'], input[type='text']").first.fill(usuario)
            page.locator("#password, input[name='password'], input[type='password']").first.fill(senha)
            page.locator("#kc-login, button[type='submit'], input[type='submit']").first.click()

            # Aguarda redirecionamento para o portal
            page.wait_for_url("**portalservicos.economia.df.gov.br**", timeout=120_000)
            page.wait_for_load_state("networkidle")

            # Tenta navegar para área de chamados, caso exista menu com esse nome
            menus = ["Chamados", "Solicitações", "Tickets", "Atendimentos"]
            for menu in menus:
                el = page.get_by_text(menu, exact=False)
                if el.count() > 0:
                    try:
                        el.first.click(timeout=3000)
                        page.wait_for_load_state("networkidle", timeout=10_000)
                        break
                    except Exception:
                        pass

            chamados = extrair_chamados_da_tela(page)
            return chamados

        except PlaywrightTimeoutError as e:
            raise RuntimeError(f"Timeout durante acesso ao portal: {e}") from e
        finally:
            browser.close()


def imprimir_chamados(chamados: List[Chamado]) -> None:
    if not chamados:
        print("Nenhum chamado em aberto encontrado (ou não foi possível identificar os campos automaticamente).")
        return

    print(f"Total de chamados em aberto identificados: {len(chamados)}")
    print("=" * 80)
    for i, c in enumerate(chamados, start=1):
        print(f"#{i}")
        print(f"  Local: {c.local}")
        print(f"  Data de abertura: {c.data_abertura}")
        print(f"  Categoria: {c.categoria}")
        print("-" * 80)


def main() -> int:
    parser = argparse.ArgumentParser(description="Lista chamados em aberto no Portal de Serviços DF.")
    parser.add_argument("--usuario", required=True, help="Usuário de acesso ao portal")
    parser.add_argument("--senha", required=True, help="Senha de acesso ao portal")
    parser.add_argument("--mostrar-navegador", action="store_true", help="Mostra navegador (modo não headless)")
    args = parser.parse_args()

    try:
        chamados = fazer_login_e_coletar(
            usuario=args.usuario,
            senha=args.senha,
            headless=not args.mostrar_navegador,
        )
        imprimir_chamados(chamados)
        return 0
    except Exception as e:
        print(f"Erro: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
