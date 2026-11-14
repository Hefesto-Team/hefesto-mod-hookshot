from __future__ import annotations

import asyncio
import json
import tempfile
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any

AZUL = "aa:bb:cc:00:00:01"
BRANCO = "aa:bb:cc:00:00:02"
VERMELHO = "aa:bb:cc:00:00:03"
ROXO = "aa:bb:cc:00:00:04"

MESA_MISTA: list[dict[str, Any]] = [
    {"uniq": AZUL, "jogador": 1, "cor": "Starlight Blue"},
    {"uniq": BRANCO, "jogador": 2, "cor": "White"},
    {"uniq": VERMELHO, "jogador": 3, "cor": "Cosmic Red"},
    {"uniq": ROXO, "jogador": 4, "cor": "Galactic Purple"},
]


class PortaDeMentira:
    def __init__(self, controles: list[dict[str, Any]] | None = None) -> None:
        self.controles = list(MESA_MISTA if controles is None else controles)
        self.pedidos: list[tuple[str, dict[str, Any]]] = []
        self.escritores: list[asyncio.StreamWriter] = []

    def de(self, metodo: str) -> list[dict[str, Any]]:
        return [p for m, p in self.pedidos if m == metodo]

    def ultimo_estado(self) -> dict[str, Any]:
        return self.de("acessorios.estado")[-1]

    async def atender(self, leitor: asyncio.StreamReader, escritor: asyncio.StreamWriter) -> None:
        self.escritores.append(escritor)
        while linha := await leitor.readline():
            pedido = json.loads(linha)
            metodo, params = pedido["method"], pedido.get("params") or {}
            self.pedidos.append((metodo, params))
            resultado: Any = {"status": "ok"}
            if metodo == "mod.ola":
                resultado = {"id": "hookshot", "api": 2, "permissoes": []}
            elif metodo == "controles.lista":
                resultado = {"controles": self.controles}
            elif metodo == "acessorios.estado":
                resultado = {"recebido": True}
            elif metodo == "eventos.assinar":
                resultado = {"assinados": params.get("topicos", [])}
            escritor.write(json.dumps({"jsonrpc": "2.0", "id": pedido["id"],
                                       "result": resultado}).encode() + b"\n")
            await escritor.drain()

    async def evento(self, nome: str, dados: dict[str, Any], topico: str = "",
                     uniq: str | None = None) -> None:
        for escritor in self.escritores:
            escritor.write(json.dumps({"jsonrpc": "2.0", "method": "evento", "params": {
                "topico": topico, "nome": nome, "uniq": uniq, "dados": dados}}).encode() + b"\n")
            await escritor.drain()


async def ate(condicao: Callable[[], bool], prazo: float = 5.0) -> None:
    fim = asyncio.get_running_loop().time() + prazo
    while not condicao():
        if asyncio.get_running_loop().time() > fim:
            raise AssertionError("a condição não chegou no prazo")
        await asyncio.sleep(0.01)


def rodar_com_a_porta(tmp_path: Path, monkeypatch: Any,
                      corpo: Callable[[PortaDeMentira, Any], Awaitable[None]],
                      controles: list[dict[str, Any]] | None = None,
                      dados: Path | None = None) -> PortaDeMentira:
    import servidor

    porta = PortaDeMentira(controles)
    caminho = Path(tempfile.mkdtemp(prefix="hk")) / "p.sock"
    monkeypatch.setenv("HEFESTO_MOD_SOCKET", str(caminho))
    monkeypatch.setenv("HEFESTO_MOD_FICHA", "ficha")
    if dados is not None:
        monkeypatch.setenv("HEFESTO_MOD_DADOS", str(dados))
    else:
        monkeypatch.delenv("HEFESTO_MOD_DADOS", raising=False)

    async def tudo() -> None:
        aberto = await asyncio.start_unix_server(porta.atender, path=str(caminho))
        nascida: list[Any] = []
        tarefa = asyncio.create_task(servidor.rodar(nascida.append))
        try:
            await ate(lambda: bool(nascida))
            await corpo(porta, nascida[0])
        finally:
            tarefa.cancel()
            await asyncio.gather(tarefa, return_exceptions=True)
            aberto.close()

    asyncio.run(tudo())
    return porta
