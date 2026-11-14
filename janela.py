from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence
from typing import Any

PERFIL_DO_JOGO = "Hookshot"
SHA_DO_APPIMAGE_CONHECIDO = "c0b2e958ae00dc560072154f890b9be422724abd9bb522d6afd9922788b86e02"
VERSAO_DO_APPIMAGE_CONHECIDO = "v2.1.0"
NOME_SEM_COR = "DualSense"

LUZES: dict[str, tuple[str, str]] = {
    "kokiri": ("#2e9e44", "Kokiri"),
    "goron": ("#c8402a", "Goron"),
    "zora": ("#2a6fd0", "Zora"),
    "fada": ("#f0c8ff", "Fada"),
}
GATILHOS: dict[str, str] = {"leve": "Leve", "firme": "Firme"}
VIBRACOES: dict[str, str] = {"jogo": "Jogo", "forte": "Forte"}
PADRAO: dict[str, str | None] = {"luz": None, "gatilhos": "leve", "vibracao": "jogo"}
FIRME: tuple[str, list[int]] = ("Feedback", [2, 7])
GANHO_DO_FORTE = 1.5

DICA_DA_LUZ = "A cor da barra com o jogo aberto; outro clique na mesma devolve a do Hefesto"
DICA_DOS_GATILHOS = "Leve: o toque do perfil. Firme: o gatilho resiste desde o começo"
DICA_DA_VIBRACAO = "Forte: a vibração do jogo uma vez e meia neste controle"


def ident(uniq: str) -> str:
    return "c" + hashlib.sha256(uniq.encode("utf-8", "surrogateescape")).hexdigest()[:10]


def valida(acao: str, valor: object) -> bool:
    if acao == "luz":
        return valor is None or valor in LUZES
    if acao == "gatilhos":
        return valor in GATILHOS
    if acao == "vibracao":
        return valor in VIBRACOES
    return False


def escolha_de(escolhas: Mapping[str, Mapping[str, Any]], chave: str) -> dict[str, Any]:
    guardada = escolhas.get(chave) or {}
    return {acao: guardada[acao] if acao in guardada and valida(acao, guardada[acao]) else padrao
            for acao, padrao in PADRAO.items()}


def nomes(controles: Sequence[Mapping[str, Any]]) -> dict[str, str]:
    vistos: dict[str, int] = {}
    saida: dict[str, str] = {}
    ordem = sorted(controles, key=lambda c: (c.get("jogador") is None, c.get("jogador") or 0))
    for c in ordem:
        cor = c.get("cor")
        base = cor.strip()[:50] if isinstance(cor, str) and cor.strip() else NOME_SEM_COR
        base = base[:1].upper() + base[1:]
        vistos[base] = vistos.get(base, 0) + 1
        saida[str(c["uniq"])] = base if vistos[base] == 1 else f"{base} {vistos[base]}"
    return saida


def controles_do_cartao(escolha: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [
        {"id": "luz", "tipo": "paleta", "rotulo": "Luz", "valor": escolha["luz"],
         "dica": DICA_DA_LUZ,
         "opcoes": [{"id": k, "cor": cor, "rotulo": rotulo} for k, (cor, rotulo) in LUZES.items()]},
        {"id": "gatilhos", "tipo": "escolha", "rotulo": "Gatilhos", "valor": escolha["gatilhos"],
         "dica": DICA_DOS_GATILHOS,
         "opcoes": [{"id": k, "rotulo": r} for k, r in GATILHOS.items()]},
        {"id": "vibracao", "tipo": "escolha", "rotulo": "Vibração", "valor": escolha["vibracao"],
         "dica": DICA_DA_VIBRACAO,
         "opcoes": [{"id": k, "rotulo": r} for k, r in VIBRACOES.items()]},
    ]


def aparelhos(controles: Sequence[Mapping[str, Any]],
              escolhas: Mapping[str, Mapping[str, Any]]) -> list[dict[str, Any]]:
    batizados = nomes(controles)
    saida = []
    for c in sorted(controles, key=lambda c: (c.get("jogador") is None, c.get("jogador") or 0)):
        chave = ident(str(c["uniq"]))
        saida.append({"id": chave, "nome": batizados[str(c["uniq"])], "tipo": "Controle",
                      "estado": "ligado", "bateria": None, "forca": None,
                      "controles": controles_do_cartao(escolha_de(escolhas, chave))})
    return saida[:32]


def _curto(caminho: str, casa: str) -> str:
    if casa and (caminho == casa or caminho.startswith(casa.rstrip("/") + "/")):
        caminho = "~" + caminho[len(casa.rstrip("/")):]
    return caminho if len(caminho) <= 40 else "…" + caminho[-39:]


def conexoes(retrato: Mapping[str, Any]) -> list[dict[str, Any]]:
    if not retrato:
        motivo = "Abra o jogo uma vez pelo Hefesto para conferir"
        return [{"id": "hookshot", "tipo": "Hookshot", "transporte": "local",
                 "estado": "desligado", "motivo": motivo},
                {"id": "jogo", "tipo": "Jogo", "transporte": "local",
                 "estado": "desligado", "motivo": motivo}]
    app = retrato.get("appimage")
    if not isinstance(app, dict):
        hookshot = ("desligado", "Ponha o AppImage do Hookshot em ~/Applications")
    elif app.get("sha256") == SHA_DO_APPIMAGE_CONHECIDO:
        hookshot = ("ligado", f"O AppImage {VERSAO_DO_APPIMAGE_CONHECIDO}, SHA-256 conferido")
    else:
        hookshot = ("falhou", f"O SHA-256 não é o do AppImage {VERSAO_DO_APPIMAGE_CONHECIDO}")
    jogo = {
        "compilado": ("ligado", "Compilado do seu despejo, que o Hookshot aceitou"),
        "danificado": ("falhou", "O despejo veio incompleto: refaça o dump (aba Dump)"),
    }.get(str(retrato.get("jogo")), ("desligado", "Faça o dump do cartucho e compile (aba Dump)"))
    return [{"id": "hookshot", "tipo": "Hookshot", "transporte": "local",
             "estado": hookshot[0], "motivo": hookshot[1]},
            {"id": "jogo", "tipo": "Jogo", "transporte": "local",
             "estado": jogo[0], "motivo": jogo[1]}]


def linhas(retrato: Mapping[str, Any]) -> list[dict[str, str]]:
    casa = str(retrato.get("casa") or "")
    saida = []
    pasta = retrato.get("pasta")
    if isinstance(pasta, str) and pasta:
        saida.append({"rotulo": "Pasta", "valor": _curto(pasta, casa)})
    app = retrato.get("appimage")
    if isinstance(app, dict) and isinstance(app.get("caminho"), str):
        nome = app["caminho"].rsplit("/", 1)[-1]
        saida.append({"rotulo": "AppImage", "valor": nome if len(nome) <= 40 else nome[:39] + "…"})
        sha = app.get("sha256")
        if isinstance(sha, str):
            saida.append({"rotulo": "SHA-256", "valor": sha[:16] + "…"})
    return saida


def estado(controles: Sequence[Mapping[str, Any]], escolhas: Mapping[str, Mapping[str, Any]],
           retrato: Mapping[str, Any]) -> dict[str, Any]:
    return {"ligado": True, "nivel": 0, "perfil": None,
            "aparelhos": aparelhos(controles, escolhas),
            "conexoes": conexoes(retrato), "linhas": linhas(retrato)}


def em_cena(dados: Mapping[str, Any]) -> bool:
    if dados.get("perfil") == PERFIL_DO_JOGO:
        return True
    return any(isinstance(c, dict) and c.get("perfil") == PERFIL_DO_JOGO
               for c in dados.get("controles") or [])


def rgb(cor: str) -> list[int]:
    return [int(cor[i:i + 2], 16) for i in (1, 3, 5)]


def forte(pedido: Sequence[Any]) -> tuple[int, int]:
    fraco, forte_ = (max(0, min(255, int(v))) if isinstance(v, (int, float))
                     and not isinstance(v, bool) else 0 for v in (list(pedido) + [0, 0])[:2])
    return (min(255, round(fraco * GANHO_DO_FORTE)), min(255, round(forte_ * GANHO_DO_FORTE)))
