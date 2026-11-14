from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

import pytest
from porta_de_mentira import MESA_MISTA, PortaDeMentira, ate, rodar_com_a_porta

import hookshot
import janela
import servidor

NA_CENA: dict[str, Any] = {"perfil": "Hookshot", "jogo": None, "controles": [
    {"jogador": n, "perfil": "Hookshot", "jogo": None} for n in (1, 2, 3, 4)]}
FORA_DE_CENA: dict[str, Any] = {"perfil": "Padrão", "jogo": None, "controles": []}
RAIZ = Path(__file__).resolve().parents[1]


def test_o_jogo_entregue_e_o_do_leitor_e_abre_pelo_comando_do_manifesto() -> None:
    manifesto = json.loads((RAIZ / "hefesto-mod.json").read_text(encoding="utf-8"))
    assert servidor.JOGO["chave"] == hookshot.CHAVE_DO_JOGO
    assert servidor.JOGO["nome"] == hookshot.NOME_DO_JOGO
    assert servidor.JOGO["janela"] == hookshot.JANELA
    assert servidor.JOGO["abrir"][0] in manifesto["lancador"]["comandos"]
    assert {"pedir:lancador.abrir", "escrever:mira"} <= set(manifesto["permissoes"])
    assert {"id": janela.ACAO_DE_JOGAR, "rotulo": "Jogar"} in manifesto["acoes"]


def test_o_botao_jogar_pede_o_lancador_abrir_com_o_jogo_entregue(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    async def corpo(porta: PortaDeMentira, _ext: Any) -> None:
        await ate(lambda: bool(porta.de("lancador.jogos")))
        await porta.evento("extensao.acao", {"mod": "hookshot", "acao": "jogar"})
        await ate(lambda: bool(porta.de("lancador.abrir")))

    porta = rodar_com_a_porta(tmp_path, monkeypatch, corpo)
    assert porta.de("lancador.jogos") == [{"jogos": [servidor.JOGO]}]
    assert porta.de("lancador.abrir") == [{"chave": hookshot.CHAVE_DO_JOGO}]
    assert not [linha for linha in porta.ultimo_estado()["linhas"] if linha["rotulo"] == "Jogar"]


class _PortaVelha(PortaDeMentira):
    async def atender(self, leitor: asyncio.StreamReader, escritor: asyncio.StreamWriter) -> None:
        self.escritores.append(escritor)
        while linha := await leitor.readline():
            pedido = json.loads(linha)
            metodo, params = pedido["method"], pedido.get("params") or {}
            self.pedidos.append((metodo, params))
            if metodo == "lancador.abrir":
                resposta: dict[str, Any] = {"error": {
                    "code": -32601, "message": "método desconhecido: lancador.abrir"}}
            else:
                resultado: Any = {"status": "ok"}
                if metodo == "controles.lista":
                    resultado = {"controles": self.controles}
                resposta = {"result": resultado}
            escritor.write(json.dumps({"jsonrpc": "2.0", "id": pedido["id"],
                                       **resposta}).encode() + b"\n")
            await escritor.drain()


def test_o_hefesto_velho_recusa_o_jogar_e_a_janela_diz(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import porta_de_mentira

    monkeypatch.setattr(porta_de_mentira, "PortaDeMentira", _PortaVelha)

    async def corpo(porta: PortaDeMentira, _ext: Any) -> None:
        await porta.evento("extensao.acao", {"mod": "hookshot", "acao": "jogar"})
        await ate(lambda: any(linha["rotulo"] == "Jogar"
                              for linha in porta.ultimo_estado()["linhas"]))

    porta = rodar_com_a_porta(tmp_path, monkeypatch, corpo)
    assert {"rotulo": "Jogar", "valor": janela.SEM_O_ABRIR} in porta.ultimo_estado()["linhas"]


@pytest.mark.parametrize("uniq, cor", [(c["uniq"], c["cor"]) for c in MESA_MISTA])
def test_o_giroscopio_desligado_vale_so_naquele_controle_e_so_com_o_jogo_aberto(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, uniq: str, cor: str) -> None:
    alvo = janela.ident(uniq)

    async def corpo(porta: PortaDeMentira, _ext: Any) -> None:
        await ate(lambda: bool(porta.de("acessorios.estado")))
        await porta.evento("extensao.acao", {"mod": "hookshot", "acao": "giro",
                                             "alvo": alvo, "valor": False})
        await ate(lambda: len(porta.de("acessorios.estado")) >= 2)
        await porta.evento("perfil.trocou", NA_CENA, "perfil.jogo")
        await ate(lambda: bool(porta.de("mira.ligada")))
        await porta.evento("perfil.trocou", FORA_DE_CENA, "perfil.jogo")
        await ate(lambda: len(porta.de("mira.ligada")) >= 2)

    porta = rodar_com_a_porta(tmp_path, monkeypatch, corpo, dados=tmp_path)
    assert porta.de("mira.ligada") == [{"uniq": uniq, "ligada": False},
                                       {"uniq": uniq, "ligada": True}]
    cartao = next(a for a in porta.ultimo_estado()["aparelhos"] if a["nome"] == cor)
    assert {c["id"]: c["valor"] for c in cartao["controles"]}["giro"] is False
    gravado = json.loads((tmp_path / "controles.json").read_text(encoding="utf-8"))
    assert gravado[alvo]["giro"] is False
