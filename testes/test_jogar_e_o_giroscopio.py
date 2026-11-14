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


@pytest.mark.parametrize("uniq", [c["uniq"] for c in MESA_MISTA])
def test_o_giroscopio_espera_o_modo_da_extensao_e_volta_a_pedir_quando_ele_acende(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, uniq: str) -> None:
    alvo = janela.ident(uniq)

    def modo(valor: str) -> dict[str, Any]:
        return {"uniq": uniq, "jogador": 1, "secoes": {"controles": valor}}

    async def corpo(porta: PortaDeMentira, _ext: Any) -> None:
        porta.modos = {}
        await ate(lambda: bool(porta.de("acessorios.estado")))
        await porta.evento("extensao.acao", {"mod": "hookshot", "acao": "giro",
                                             "alvo": alvo, "valor": False})
        await ate(lambda: len(porta.de("acessorios.estado")) >= 2)
        await porta.evento("perfil.trocou", NA_CENA, "perfil.jogo")
        await ate(lambda: len(porta.de("mira.ligada")) >= 1)
        porta.modos[uniq] = servidor.MODO_DA_EXTENSAO
        await porta.evento("modo.aba", modo(servidor.MODO_DA_EXTENSAO), "modo.aba")
        await ate(lambda: len(porta.de("mira.ligada")) >= 2)
        porta.modos[uniq] = "personalizado"
        await porta.evento("modo.aba", modo("personalizado"), "modo.aba")
        porta.modos[uniq] = servidor.MODO_DA_EXTENSAO
        await porta.evento("modo.aba", modo(servidor.MODO_DA_EXTENSAO), "modo.aba")
        await ate(lambda: len(porta.de("mira.ligada")) >= 3)
        await porta.evento("perfil.trocou", FORA_DE_CENA, "perfil.jogo")
        await ate(lambda: len(porta.de("mira.ligada")) >= 4)

    porta = rodar_com_a_porta(tmp_path, monkeypatch, corpo, dados=tmp_path)
    desligado, ligado = {"uniq": uniq, "ligada": False}, {"uniq": uniq, "ligada": True}
    assert porta.de("mira.ligada") == [desligado, desligado, desligado, ligado]


def test_o_perfil_do_jogo_acende_o_modo_e_a_guarda_do_hefesto_deixa_os_quatro(
        monkeypatch: pytest.MonkeyPatch) -> None:
    pytest.importorskip("hefesto_dualsense4unix")
    from types import SimpleNamespace

    from hefesto_dualsense4unix.core.virtual_motion import chave_de_sensor
    from hefesto_dualsense4unix.daemon.subsystems import tato_vivo
    from hefesto_dualsense4unix.mods.manifesto import ler_manifesto
    from hefesto_dualsense4unix.mods.porta import Porta as PortaDoHefesto
    from hefesto_dualsense4unix.profiles.schema import modo_que_vale

    perfil = json.loads((RAIZ / "perfis" / "hookshot.json").read_text(encoding="utf-8"))
    assert ["02"] in [m.abas for m in ler_manifesto(RAIZ).modos_de_aba]

    def no_modo(perfil_lido: dict[str, Any], vivas: frozenset[str], mod_id: str) -> set[str]:
        monkeypatch.setattr(tato_vivo, "_MODO_DA_ABA_DITO", {c["uniq"]: {
            "uniq": c["uniq"], "jogador": c["jogador"], "secoes": {
                s: modo_que_vale(m, vivas) or m
                for s, m in tato_vivo.secoes_do_perfil(perfil_lido, c["uniq"]).items()}}
            for c in MESA_MISTA})
        sessao: Any = SimpleNamespace(mod_id=mod_id)
        return set(PortaDoHefesto._no_modo_da_extensao(sessao))

    quatro = {chave_de_sensor(c["uniq"]) for c in MESA_MISTA}
    assert no_modo(perfil, frozenset({"hookshot"}), "hookshot") == quatro
    assert no_modo(perfil, frozenset(), "hookshot") == set()
    assert no_modo(perfil, frozenset({"hookshot", "outra"}), "outra") == set()
    sem_modo = {k: v for k, v in perfil.items() if k != "controles_modo"}
    assert no_modo(sem_modo, frozenset({"hookshot"}), "hookshot") == set()
