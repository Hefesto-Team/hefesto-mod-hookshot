# O que se mediu do Hookshot

Medido em 14/11/2026. Cada linha diz de onde veio. O que nenhuma fonte disse fica como **não medido**; nada aqui foi
deduzido do nome de um arquivo ou do costume de outro programa.

## As fontes

| sigla | fonte | como foi lida |
| --- | --- | --- |
| LEIA | o `readme.md` do repositório `NotRexed/Hookshot`, na cópia do Internet Archive de 13/11/2026 05h20 UTC (`web.archive.org/web/20261113052057/https://github.com/NotRexed/Hookshot`) | página baixada, texto extraído |
| NOTAS | as notas das versões v2.1.0, v2.0.12 e v2.0.0, no espelho `newreleases.io/project/github/NotRexed/Hookshot/release/<versão>` | página baixada, texto extraído |
| SITE | `hookshot.pro` (raiz, `/install/linux/`, `/builder/`, `/requirements/`, `/download/`, `/settings/`, `/compare/`, `/about/`) | página baixada, texto extraído |
| GH | a API do GitHub (`gh api`) | consultada em 14/11/2026 |
| NUP | o `README.md` de `a55uka/nup` (licença MIT) | pela API do GitHub |
| WP | Wikipédia em inglês, «Nintendo Switch 2» e «Mig Flash» (texto bruto) | baixada |
| BUSCA | resultado de busca na web, sem a página aberta (o site recusou com 403 ou não foi aberto) | só o resumo |

## O achado que muda o resto

| o quê | medida | fonte |
| --- | --- | --- |
| O repositório `NotRexed/Hookshot` | **responde 404** em 14/11/2026, pela API e pela página | GH |
| O usuário `NotRexed` | **responde 404** em 14/11/2026 | GH |
| A última cópia pública do repositório | Internet Archive, 13/11/2026 05h20 UTC | GH (API `archive.org/wayback/available`) |
| Onde o projeto mora agora | https://git.notrexed.dev/Hookshot/Hookshot (Forgejo), com a v2.1.0 de 11/11/2026 e o AppImage; o endereço sai de https://notrexed.dev/ | medido por quem coordena, 14/11/2026 |
| O `hookshot.pro` | site de terceiros, com anúncios e analytics; diz não ser afiliado ao autor nem à Nintendo e que os downloads apontam para os releases do GitHub, que hoje não respondem | SITE (`/about/`) |

Consequência: o AppImage não tem mais origem oficial alcançável, e o botão «Update» do lançador busca a versão nova
nos releases (NOTAS: `hookshot-linux.txt` e o `.zsync` «são para os atualizadores»). Quem já tem o AppImage confere
o SHA-256 abaixo.

## O que é

| o quê | medida | fonte |
| --- | --- | --- |
| O jogo | The Legend of Zelda: Ocarina of Time, o remake do Nintendo Switch 2 | LEIA |
| O que o programa é | recompilação estática: o código do jogo vira C e é compilado na máquina de quem joga; o sistema do console é reimplementado e os gráficos do Switch 2 são refeitos em Vulkan. Não é emulador | LEIA |
| O que o repositório trazia | nem o jogo, nem chaves, nem executável; o readme diz que não explica como obtê-los | LEIA |
| A licença | GPL-3.0-or-later, com código do Eden e do suyu | LEIA |
| A versão estável | v2.1.0, publicada em 11/11/2026 02h29 UTC; havia uma v2.2.0-rc.1 | SITE (`/download/`), NOTAS |
| Plataformas | Windows 10/11 x64 e Linux x86_64 | LEIA |
| Alternativa viva | `tangerineturtle1/NX2navi` (MIT), outra recompilação do mesmo jogo, na versão 1.1.1 do jogo; lê `.nup`; configuração em `nx2navi.ini`; o readme cita rumble e giroscópio | GH (readme do NX2navi) |

## O que o jogo precisa ser

| o quê | medida | fonte |
| --- | --- | --- |
| Program ID | `0400486024DEC000` | LEIA |
| Atualização | `v131072` | LEIA |
| Build | `e0f3ccfa`; outra versão para com «Hookshot supports build e0f3ccfa» ou «This version isn't supported» | LEIA |
| O que a mensagem de versão errada pede | «Check that you chose the right game with its update installed» | LEIA |
| Formato de entrada | um arquivo `.nup`, ou as pastas `romfs` e `exefs` | LEIA |
| O que é o `.nup` | contêiner de despejo **sem criptografia** de jogo de Switch 1 ou 2, com `base/`, `updates/<versão decimal>/` e `dlc/`, cada um com `exefs/` e `romfs/`; compressão zstd por arquivo | NUP |
| O que o `nup info` mostra | pacote, title ID, versões, metadados e o build ID (o ModuleId do NSO, tirado de `exefs/main`) | NUP |
| Hash do despejo | **não publicado**: o Hookshot confere o build ID, não um SHA ou MD5 do arquivo | LEIA |
| Tamanho do despejo completo | cerca de 23,8 GB; um incompleto, cerca de 23,3 GB, gera `hookshot_damaged_files.txt` na pasta do jogo | LEIA |
| As pastas `romfs`/`exefs` já com a atualização aplicada ou separadas | não medido | — |
| O cartucho traz o jogo inteiro | sim, segundo duas reportagens (Creative Bloq, TweakTown); uma terceira (ConsolePulse) diz que a caixa ainda não estava rotulada | BUSCA |
| O cartucho já vem na `v131072` | não medido; a mensagem do Hookshot sugere que a atualização se instala à parte | LEIA |
| Cartão «Game-Key» | existe no Switch 2 (o cartão só traz a licença e o jogo baixa) | WP |

## Como se instala no Linux

| o quê | medida | fonte |
| --- | --- | --- |
| Pacote | um AppImage, `Hookshot-v2.1.0-x86_64.AppImage`, 242.149.880 bytes | SITE (`/install/linux/`, `/download/`) |
| SHA-256 do AppImage v2.1.0 | `c0b2e958ae00dc560072154f890b9be422724abd9bb522d6afd9922788b86e02` | SITE (`/download/`, tirado do `SHA256SUMS` do release) |
| Conferência oficial | `sha256sum -c --ignore-missing SHA256SUMS` ou `gh attestation verify <arquivo> -R NotRexed/Hookshot` | NOTAS |
| Flatpak | nenhuma fonte cita | LEIA, SITE |
| Requisitos | glibc 2.35 ou mais nova, CPU com AVX2 (o AppImage recusa sem), Vulkan 1.3 com mesh shaders (RTX 20 ou mais nova, RX 6000 ou mais nova, Intel Arc) | LEIA |
| Memória e disco | 16 GB de RAM (o jogo usa cerca de 10 GB), 8 GB de vídeo; 45 GB livres para compilar desde a v2.0.12 (antes, 60 GB), de preferência SSD | LEIA, NOTAS |
| Tempo de compilação | 10 a 45 minutos | LEIA |
| Pasta do jogo | `~/Games/Hookshot` por padrão | LEIA |
| Entrada no menu de aplicativos | «Hookshot» | LEIA |
| Linha de comando | `--cli --nup <arquivo> --out <pasta>`; `--play` (o último compilado); `--play <pasta>`; `--update <pasta>` | LEIA |
| Ajuste da compilação | `HOOKSHOT_JOBS=<n>` (ou `--jobs`), `HOOKSHOT_MEM_LIMIT_GB=<n>`, `HOOKSHOT_KEEP_BUILD_FILES=1` | LEIA |
| O AppImage não pode mudar de lugar | o lançador usa o arquivo para atualizar | LEIA |
| `/dev/udmabuf` | acelera a importação de memória no AMD; no driver próprio da NVIDIA não precisa | LEIA |
| Steam Deck, travamento na Floresta Kokiri | `RX_VK_MESH_NOCULL=2c56dc1006942f74` (issue 817) | SITE, NOTAS |

## Onde guarda as coisas (Linux)

| o quê | caminho | fonte |
| --- | --- | --- |
| O lançador | `<pasta do jogo>/hookshot` | LEIA |
| O jogo | `<pasta do jogo>/bin/hookshot` | LEIA |
| Opções do menu e os controles | `<pasta do jogo>/hookshot_options.ini` | LEIA |
| Chaves de teste do jogo | `<pasta do jogo>/hookshot_env.txt`, uma `NOME=VALOR` por linha, só nomes `RX_`, `HOS_`, `HOOKSHOT_`, `EDEN_`, `NVN_`, `SDL_`; `HOS_ENV_FILE=<caminho>` aponta outro | LEIA |
| Idioma | `<pasta do jogo>/language.txt` | LEIA |
| Mods | `<pasta do jogo>/mods/<nome>/romfs/...`, só RomFS | LEIA |
| Registro | `<pasta do jogo>/hookshot_log.txt` (e `.1` a `.4`); `hookshot_startup.log` | LEIA |
| Saves | `~/.local/share/hookshot` | LEIA |
| Configuração do builder | `~/.config/hookshot/builder.ini` | LEIA |
| Cache do builder | `~/.cache/hookshot-builder` | LEIA |

## Os controles

| o quê | medida | fonte |
| --- | --- | --- |
| Camada de entrada | SDL (SDL3; SDL2 também serve no build do código-fonte) | LEIA, NOTAS |
| Remapeamento | página Controls do menu (Insert, F1 ou Esc; no controle, Home ou Select+Start); salvo no `hookshot_options.ini` | LEIA |
| Formato no `.ini` | `pad_<botão>=<n>` pela posição: 0 face de baixo, 1 direita, 2 esquerda, 3 de cima, 4 Select, 5 Home, 6 Start, 7 e 8 os cliques dos analógicos, 9 e 10 os ombros, 11 a 14 o direcional (cima, baixo, esquerda, direita), 15 e 16 os gatilhos, -1 nenhum. Botões: `a b x y l r zl zr plus minus ls rs left up right down`. Teclado: `key_<botão>=<código>[,<código>]` | LEIA |
| Disposição | Nintendo (padrão, A na face direita), Xbox / PC, Swap Face, Custom | LEIA |
| Ícones dos botões | Auto, Switch, Xbox, PlayStation 4, PlayStation 5, Steam Deck | LEIA |
| Touchpad do DualSense | o clique faz o mesmo que F1 (abre o menu) | LEIA |
| Controle com a janela fora de foco | opção «Controller in background» (padrão: desligada) | LEIA |
| Zona morta do analógico | padrão cerca de 24%, opções de 5% a 30% | LEIA |
| Rumble no DualSense | a vibração do jogo nos dois motores (o HD rumble fica para Pro Controller e Joy-Con); escala «Rumble strength» de 0 a 150% | LEIA |
| Giroscópio | «Motion controls»: mira pelo giroscópio onde o jogo usa movimento; funciona com DualSense e DualShock 4 pelo SDL; sensibilidade X 10–600%, Y 10–300%, inversão, zona morta; a deriva se aprende com o controle parado | LEIA, NOTAS |
| Microfone | a ocarina escuta um microfone escolhido no menu (padrão: o padrão do sistema) | LEIA |
| Gatilhos adaptativos | nenhuma fonte cita | LEIA, NOTAS, SITE |
| Barra de luz e LEDs | nenhuma fonte cita | LEIA, NOTAS, SITE |
| Mais de um controle | o giroscópio segue o controle usado por último; os ícones Auto seguem o primeiro; o comportamento com 2 a 4 controles ao mesmo tempo não foi medido | LEIA |
| O SDL abre o DualSense pelo hidraw | não medido (o readme só diz isso do controle de Switch) | LEIA |

## Como reconhecer o jogo aberto

| o quê | medida | fonte |
| --- | --- | --- |
| Executável do jogo | `bin/hookshot` dentro da pasta do jogo | LEIA |
| Nome do processo (`comm`) | não medido no aparelho; o executável se chama `hookshot` | LEIA |
| `app_id` / `WM_CLASS` da janela | não medido | — |
| Título da janela | não medido | — |
| Status do Discord | «Playing Hookshot» | LEIA, NOTAS |

## O hardware de despejo

| o quê | medida | fonte |
| --- | --- | --- |
| O próprio Switch 2 | preço de lançamento US$ 449,99 (€ 469,99) | WP |
| Mig Flash Dumper | aparelho USB que copia cartuchos de **Switch** (chip ESP32); a Nintendo o chama de «circumvention device»; leitura de cartão de Switch 2 não medida; preço não medido | WP |
| Contas banidas | o uso do Mig Flash no Switch 2 derrubou o serviço online de consoles | WP |
| «switch 2 Game Card Reader» (loja MLGFIX, Dubai) | promete ler «todos os Game Cards de Switch 2» no Windows ou Mac; preço sob consulta; formato de saída e fabricante não ditos; página com texto de modelo não preenchido | página da loja |
| `nxdumptool` | o despejador de referência do Switch 1 foi arquivado em 22/10/2026; suporte a Switch 2 não confirmado | BUSCA |
| Um caminho público e estável de despejo do Switch 2 | não medido; reportagens citam um desbloqueio preso ao PC que some ao reiniciar o console | BUSCA |
