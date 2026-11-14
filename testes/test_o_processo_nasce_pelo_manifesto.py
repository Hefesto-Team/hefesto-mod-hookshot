from __future__ import annotations

import asyncio
import json
import os
import shutil
import signal
import tempfile
from pathlib import Path

from porta_de_mentira import PortaDeMentira, ate

RAIZ = Path(__file__).resolve().parents[1]


def test_o_processo_do_manifesto_nasce_fora_da_pasta_e_fala_com_o_hefesto(tmp_path: Path) -> None:
    executar = json.loads((RAIZ / "hefesto-mod.json").read_text(encoding="utf-8"))["processo"][
        "executar"]
    achado = shutil.which(executar[0])
    assert achado, f"falta o {executar[0]} no PATH"
    comando = [achado, *(str(RAIZ / a) if (RAIZ / a).is_file() else a for a in executar[1:])]
    porta = PortaDeMentira()
    caminho = Path(tempfile.mkdtemp(prefix="hk")) / "p.sock"
    dados = tmp_path / "dados"
    dados.mkdir()
    ambiente = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "HOME": str(tmp_path),
        "HEFESTO_MOD_SOCKET": str(caminho),
        "HEFESTO_MOD_FICHA": "ficha",
        "HEFESTO_MOD_DADOS": str(dados),
    }

    async def tudo() -> tuple[int, bytes]:
        aberto = await asyncio.start_unix_server(porta.atender, path=str(caminho))
        processo = await asyncio.create_subprocess_exec(
            *comando, cwd=tmp_path, env=ambiente,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
        try:
            await ate(lambda: bool(porta.de("acessorios.estado")) or processo.returncode is not None,
                      prazo=10.0)
        finally:
            if processo.returncode is None:
                processo.send_signal(signal.SIGTERM)
            saida, _ = await asyncio.wait_for(processo.communicate(), 10.0)
            aberto.close()
        return processo.returncode or 0, saida

    codigo, saida = asyncio.run(tudo())
    assert porta.de("mod.ola"), saida.decode(errors="replace")
    assert porta.de("acessorios.estado"), saida.decode(errors="replace")
    assert codigo == 0, saida.decode(errors="replace")
