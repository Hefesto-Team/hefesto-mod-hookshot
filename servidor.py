#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import contextlib
import json
import os
import signal
import sys
import tempfile
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

AQUI = Path(__file__).resolve().parent
if str(AQUI) not in sys.path:
    sys.path.insert(0, str(AQUI))

import janela  # noqa: E402

TOPICOS = ["conexao", "perfil.jogo", "jogo.vibracao", "modo.aba"]
MODO_DA_EXTENSAO = "extensao:hookshot"
EVENTO_DA_ACAO = "extensao.acao"
ESCOLHAS = "controles.json"
RETRATO = "retrato.json"
PRAZO_MS = 300_000
RENOVAR_S = 240.0
OLHAR_O_RETRATO_S = 2.0
INTERVALO_DA_VIBRACAO_S = 0.125
MANTER_A_VIBRACAO_S = 1.0


def diario(frase: str) -> None:
    print(frase, file=sys.stderr, flush=True)


class RecusaDaPorta(RuntimeError):
    def __init__(self, mensagem: str, codigo: int | None = None) -> None:
        super().__init__(mensagem)
        self.codigo = codigo


METODO_DESCONHECIDO = -32601
JOGO = {"chave": "hookshot-ocarina-of-time",
        "nome": "The Legend of Zelda: Ocarina of Time (Hookshot)",
        "abrir": ["hefesto-hookshot"], "janela": "hookshot"}


class Porta:
    def __init__(self, leitor: asyncio.StreamReader, escritor: asyncio.StreamWriter) -> None:
        self._leitor = leitor
        self._escritor = escritor
        self._proximo = 0
        self._esperando: dict[int, asyncio.Future[dict[str, Any]]] = {}
        self.eventos: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self.fechada = False
        self._lendo = asyncio.create_task(self._ler())

    @classmethod
    async def abrir(cls, caminho: str) -> Porta:
        leitor, escritor = await asyncio.open_unix_connection(caminho, limit=1 << 20)
        return cls(leitor, escritor)

    async def _ler(self) -> None:
        with contextlib.suppress(ConnectionError):
            while linha := await self._leitor.readline():
                try:
                    mensagem = json.loads(linha)
                except ValueError:
                    continue
                if not isinstance(mensagem, dict):
                    continue
                ident = mensagem.get("id")
                espera = self._esperando.pop(ident, None) if isinstance(ident, int) else None
                if espera is not None and not espera.done():
                    espera.set_result(mensagem)
                elif "method" in mensagem:
                    await self.eventos.put(mensagem)
        self.fechada = True
        for espera in self._esperando.values():
            if not espera.done():
                espera.set_exception(ConnectionError("a porta fechou"))
        await self.eventos.put({"method": "porta.fechou"})

    async def pedir(self, metodo: str, params: dict[str, Any]) -> dict[str, Any]:
        if self.fechada:
            raise ConnectionError("a porta fechou")
        self._proximo += 1
        espera: asyncio.Future[dict[str, Any]] = asyncio.get_running_loop().create_future()
        self._esperando[self._proximo] = espera
        linha = {"jsonrpc": "2.0", "id": self._proximo, "method": metodo, "params": params}
        self._escritor.write(json.dumps(linha).encode() + b"\n")
        await self._escritor.drain()
        resposta = await asyncio.wait_for(espera, 10)
        if "error" in resposta:
            erro = resposta["error"] if isinstance(resposta["error"], dict) else {}
            codigo = erro.get("code")
            raise RecusaDaPorta(str(erro.get("message", "recusado")),
                                codigo if isinstance(codigo, int) else None)
        resultado: dict[str, Any] = resposta.get("result") or {}
        return resultado

    def fechar(self) -> None:
        self._lendo.cancel()
        self._escritor.close()


class Extensao:
    def __init__(self, porta: Porta, dados: Path | None,
                 relogio: Callable[[], float] = time.monotonic) -> None:
        self.porta = porta
        self.dados = dados
        self.relogio = relogio
        self.controles: list[dict[str, Any]] = []
        self.escolhas: dict[str, dict[str, Any]] = self._ler_as_escolhas()
        self.em_cena = False
        self.retrato: dict[str, Any] = {}
        self._marca_do_retrato: int | None = None
        self._vibrou: dict[str, tuple[float, tuple[int, int]]] = {}
        self.pedidos: set[tuple[str, str]] = set()
        self.recusa_do_jogar: str | None = None
        self.ler_o_retrato()

    def _ler_as_escolhas(self) -> dict[str, dict[str, Any]]:
        if self.dados is None:
            return {}
        try:
            lido = json.loads((self.dados / ESCOLHAS).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}
        if not isinstance(lido, dict):
            return {}
        return {str(k): v for k, v in lido.items() if isinstance(v, dict)}

    def _gravar_as_escolhas(self) -> None:
        if self.dados is None:
            return
        texto = json.dumps(self.escolhas, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
        descritor, temporario = tempfile.mkstemp(prefix=".controles.", dir=self.dados)
        try:
            with os.fdopen(descritor, "w", encoding="utf-8") as saida:
                saida.write(texto)
            os.replace(temporario, self.dados / ESCOLHAS)
        except BaseException:
            Path(temporario).unlink(missing_ok=True)
            raise

    def ler_o_retrato(self) -> bool:
        if self.dados is None:
            return False
        alvo = self.dados / RETRATO
        try:
            marca: int | None = alvo.stat().st_mtime_ns
        except OSError:
            marca = None
        if marca == self._marca_do_retrato:
            return False
        self._marca_do_retrato = marca
        try:
            lido = json.loads(alvo.read_text(encoding="utf-8")) if marca is not None else {}
        except (OSError, ValueError):
            lido = {}
        self.retrato = lido if isinstance(lido, dict) else {}
        return True

    def estado(self) -> dict[str, Any]:
        return janela.estado(self.controles, self.escolhas, self.retrato, self.recusa_do_jogar)

    async def publicar(self) -> None:
        await self.porta.pedir("acessorios.estado", self.estado())

    def _uniq_de(self, alvo: object) -> str | None:
        return next((str(c["uniq"]) for c in self.controles
                     if janela.ident(str(c["uniq"])) == alvo), None)

    async def _escrever(self, metodo: str, params: dict[str, Any]) -> bool:
        try:
            await self.porta.pedir(metodo, params)
        except (RecusaDaPorta, asyncio.TimeoutError) as exc:
            diario(f"{metodo}: {exc}")
            return False
        return True

    async def aplicar(self, uniq: str) -> None:
        escolha = janela.escolha_de(self.escolhas, janela.ident(uniq))
        luz = escolha["luz"]
        if self.em_cena and luz is not None:
            self.pedidos.add((uniq, "luz"))
            await self._escrever("luz.set", {"uniq": uniq, "rgb": janela.rgb(janela.LUZES[luz][0]),
                                             "ate_ms": PRAZO_MS})
        elif (uniq, "luz") in self.pedidos:
            self.pedidos.discard((uniq, "luz"))
            await self._escrever("luz.set", {"uniq": uniq, "rgb": [0, 0, 0]})
        await self.aplicar_o_giro(uniq, escolha)
        firme = self.em_cena and escolha["gatilhos"] == "firme"
        if not firme and (uniq, "gatilhos") not in self.pedidos:
            return
        for lado in ("esquerdo", "direito"):
            if firme:
                modo, params = janela.FIRME
                await self._escrever("gatilho.set", {"uniq": uniq, "lado": lado, "modo": modo,
                                                     "params": params, "ate_ms": PRAZO_MS})
            else:
                await self._escrever("gatilho.set", {"uniq": uniq, "lado": lado, "modo": "Off",
                                                     "params": []})
        if firme:
            self.pedidos.add((uniq, "gatilhos"))
        else:
            self.pedidos.discard((uniq, "gatilhos"))

    async def aplicar_o_giro(self, uniq: str, escolha: dict[str, Any]) -> None:
        desligado = self.em_cena and escolha["giro"] is False
        if desligado == ((uniq, "giro") in self.pedidos):
            return
        if await self._escrever("mira.ligada", {"uniq": uniq, "ligada": not desligado}):
            if desligado:
                self.pedidos.add((uniq, "giro"))
            else:
                self.pedidos.discard((uniq, "giro"))

    async def o_modo_mudou(self, dados: dict[str, Any]) -> None:
        uniq, secoes = dados.get("uniq"), dados.get("secoes")
        if not isinstance(uniq, str) or not isinstance(secoes, dict):
            return
        if secoes.get("controles") != MODO_DA_EXTENSAO:
            self.pedidos.discard((uniq, "giro"))
            return
        if uniq in {str(c["uniq"]) for c in self.controles}:
            await self.aplicar_o_giro(uniq, janela.escolha_de(self.escolhas, janela.ident(uniq)))

    async def jogar(self) -> None:
        try:
            await self.porta.pedir("lancador.abrir", {"chave": JOGO["chave"]})
            self.recusa_do_jogar = None
        except RecusaDaPorta as exc:
            diario(f"lancador.abrir: {exc}")
            self.recusa_do_jogar = (janela.SEM_O_ABRIR if exc.codigo == METODO_DESCONHECIDO
                                    else str(exc))
        except asyncio.TimeoutError:
            self.recusa_do_jogar = "O Hefesto não respondeu"
        await self.publicar()

    async def entregar_o_jogo(self) -> None:
        try:
            await self.porta.pedir("lancador.jogos", {"jogos": [JOGO]})
        except (RecusaDaPorta, asyncio.TimeoutError) as exc:
            diario(f"lancador.jogos: {exc}")

    async def aplicar_a_todos(self) -> None:
        for c in list(self.controles):
            await self.aplicar(str(c["uniq"]))

    async def atualizar_os_controles(self) -> None:
        lista = (await self.porta.pedir("controles.lista", {})).get("controles", [])
        self.controles = [c for c in lista if isinstance(c, dict) and isinstance(c.get("uniq"), str)]
        presentes = {str(c["uniq"]) for c in self.controles}
        self.pedidos = {p for p in self.pedidos if p[0] in presentes}
        await self.aplicar_a_todos()
        await self.publicar()

    async def agir(self, dados: dict[str, Any]) -> None:
        acao, alvo, valor = dados.get("acao"), dados.get("alvo"), dados.get("valor")
        if acao == janela.ACAO_DE_JOGAR:
            await self.jogar()
            return
        uniq = self._uniq_de(alvo)
        if uniq is None or not isinstance(acao, str) or acao not in janela.PADRAO:
            await self.publicar()
            return
        escolha = janela.escolha_de(self.escolhas, str(alvo))
        if acao == "luz" and valor == escolha["luz"]:
            valor = None
        if not janela.valida(acao, valor):
            await self.publicar()
            return
        escolha[acao] = valor
        self.escolhas[str(alvo)] = escolha
        self._gravar_as_escolhas()
        await self.aplicar(uniq)
        await self.publicar()

    async def o_perfil_trocou(self, dados: dict[str, Any]) -> None:
        agora = janela.em_cena(dados)
        if agora != self.em_cena:
            self.em_cena = agora
            await self.aplicar_a_todos()

    async def vibracao_do_jogo(self, params: dict[str, Any], dados: dict[str, Any]) -> None:
        uniq = dados.get("uniq", params.get("uniq"))
        if not isinstance(uniq, str) or uniq not in {str(c["uniq"]) for c in self.controles}:
            return
        if janela.escolha_de(self.escolhas, janela.ident(uniq))["vibracao"] != "forte":
            return
        pedido = dados.get("pedido")
        par = janela.forte(pedido if isinstance(pedido, list) else []) if self.em_cena else (0, 0)
        agora = self.relogio()
        quando, ultimo = self._vibrou.get(uniq, (-1e9, (0, 0)))
        if par == ultimo and (par == (0, 0) or agora - quando < MANTER_A_VIBRACAO_S):
            return
        if par != (0, 0) and agora - quando < INTERVALO_DA_VIBRACAO_S:
            return
        self._vibrou[uniq] = (agora, par)
        await self._escrever("vibracao.set", {"uniq": uniq, "fraco": par[0], "forte": par[1]})

    async def ao_evento(self, mensagem: dict[str, Any]) -> bool:
        if mensagem.get("method") == "porta.fechou":
            return False
        params = mensagem.get("params") or {}
        if not isinstance(params, dict):
            return True
        nome, dados = params.get("nome"), params.get("dados")
        if nome == EVENTO_DA_ACAO and isinstance(dados, dict):
            await self.agir(dados)
        elif nome == "perfil.trocou" and isinstance(dados, dict):
            await self.o_perfil_trocou(dados)
        elif nome == "jogo.vibracao" and isinstance(dados, dict):
            await self.vibracao_do_jogo(params, dados)
        elif nome == "modo.aba" and isinstance(dados, dict):
            await self.o_modo_mudou(dados)
        elif params.get("topico") == "conexao":
            with contextlib.suppress(RecusaDaPorta, ConnectionError, asyncio.TimeoutError):
                await self.atualizar_os_controles()
        return True

    async def voltas(self) -> None:
        renovado = self.relogio()
        while True:
            await asyncio.sleep(OLHAR_O_RETRATO_S)
            if self.ler_o_retrato():
                with contextlib.suppress(RecusaDaPorta, ConnectionError, asyncio.TimeoutError):
                    await self.publicar()
            if self.em_cena and self.relogio() - renovado >= RENOVAR_S:
                renovado = self.relogio()
                with contextlib.suppress(ConnectionError):
                    await self.aplicar_a_todos()

    async def soltar_tudo(self) -> None:
        self.em_cena = False
        with contextlib.suppress(ConnectionError, RecusaDaPorta, asyncio.TimeoutError):
            await self.aplicar_a_todos()


async def rodar(ao_nascer: Callable[[Extensao], None] | None = None) -> int:
    caminho, ficha = os.environ.get("HEFESTO_MOD_SOCKET"), os.environ.get("HEFESTO_MOD_FICHA")
    if not caminho or not ficha:
        diario("sem HEFESTO_MOD_SOCKET e HEFESTO_MOD_FICHA: quem abre esta extensão é o Hefesto")
        return 2
    dados = Path(os.environ["HEFESTO_MOD_DADOS"]) if os.environ.get("HEFESTO_MOD_DADOS") else None
    porta = await Porta.abrir(caminho)
    await porta.pedir("mod.ola", {"ficha": ficha})
    extensao = Extensao(porta, dados)
    await porta.pedir("eventos.assinar", {"topicos": TOPICOS})
    await extensao.entregar_o_jogo()
    try:
        await extensao.atualizar_os_controles()
    except (RecusaDaPorta, asyncio.TimeoutError) as exc:
        diario(f"controles.lista: {exc}")
        await extensao.publicar()
    if ao_nascer is not None:
        ao_nascer(extensao)

    fim = asyncio.Event()
    laco = asyncio.get_running_loop()
    for sinal in (signal.SIGTERM, signal.SIGINT):
        with contextlib.suppress(NotImplementedError, RuntimeError):
            laco.add_signal_handler(sinal, fim.set)

    async def ouvir_a_porta() -> None:
        while await extensao.ao_evento(await porta.eventos.get()):
            pass
        fim.set()

    tarefas = [asyncio.create_task(t) for t in (ouvir_a_porta(), extensao.voltas())]
    try:
        await fim.wait()
    finally:
        if not porta.fechada:
            await extensao.soltar_tudo()
        for tarefa in tarefas:
            tarefa.cancel()
        await asyncio.gather(*tarefas, return_exceptions=True)
        porta.fechar()
    return 0


def main() -> int:
    return asyncio.run(rodar())


if __name__ == "__main__":
    raise SystemExit(main())
