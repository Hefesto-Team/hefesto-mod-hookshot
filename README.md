# hefesto-mod-hookshot

O Ocarina of Time recompilado pelo Hookshot na aba Experimental do Hefesto, com o DualSense pronto: os botões, a
vibração, a mira pelo giroscópio e o perfil do jogo.

> **Aviso.** Extensão independente: não é afiliada ao projeto Hookshot nem à Nintendo, e nenhum dos dois a endossa. Ela não traz o jogo: jogue só o que você copiou do cartucho que comprou, no seu próprio console; não baixe jogo pirata.

## Antes: o jogo no PC

A extensão não traz nem baixa o jogo nem o Hookshot. Do cartucho até o jogo compilado em `~/Games/Hookshot`, siga o
[guia do dump](docs/GUIA-DO-DUMP.md). O que se mediu do Hookshot, com a fonte de cada linha, está em
[O-QUE-SE-MEDIU](docs/O-QUE-SE-MEDIU.md).

## O que ela faz

- **O jogo na aba Experimental.** O leitor acha o jogo compilado (`bin/hookshot`) na pasta que o builder do Hookshot
  guarda em `~/.config/hookshot/builder.ini` ou em `~/Games/Hookshot`.
- **Abrir pelo Hefesto e pelo menu.** O comando `hefesto-hookshot` e o atalho «Ocarina of Time (Hookshot)» abrem o
  jogo com a janela batizada `hookshot`, e não abrem um segundo se o jogo já está aberto.
- **Os botões.** Na primeira abertura, o `hookshot_options.ini` recebe os botões do DualSense pela posição: a Cruz é
  o A, o Círculo é o B, o Quadrado é o X, o Triângulo é o Y, o L2 e o R2 são o ZL e o ZR. O original fica em
  `hookshot_options.ini.antes-do-hefesto`. Depois disso, o que você remapear no menu do jogo fica.
- **O perfil do jogo.** `hookshot.json` entra nos perfis do Hefesto (se você ainda não tem um com esse nome) e vale
  quando a janela ou o processo `hookshot` aparece: a vibração do jogo passa aos dois motores, os gatilhos ganham um
  toque leve e cada controle mantém a cor do jogador. O giroscópio chega ao jogo pelo próprio controle; na máscara
  Xbox, ligue a «Mira Virtual» do controle no Hefesto.
- **A janela «Configurar».** No «Agora», o Hookshot e o jogo em cor, com o motivo na dica. Na aba Jogo, os
  «Botões» (Posição ou Nintendo), que valem ao abrir o jogo. Na aba Controles, um cartão por controle, pela cor
  do plástico, com a Luz, os Gatilhos e a Vibração dele, que só valem com o jogo aberto. Na aba Dump, os quatro
  passos e o que o Hookshot confere.
- **De 1 a 4 controles, pelo cabo ou pelo rádio.** Os botões valem para qualquer controle, e o perfil não separa
  controle, modo nem conexão.

## Instalar

```bash
hefesto-dualsense4unix mod instalar https://github.com/vitoriamariadb/hefesto-mod-hookshot
hefesto-dualsense4unix mod ligar hookshot
```

Também se instala de uma pasta local (`mod instalar /caminho/da/pasta`), e essa nunca se atualiza sozinha.

O «ligar» roda o `install.sh --yes`, sem sudo. Remover, nesta ordem (o `mod remover` apaga a pasta onde o
`uninstall.sh` mora):

```bash
bash ~/.local/share/hefesto-dualsense4unix/mods/hookshot/uninstall.sh
hefesto-dualsense4unix mod remover hookshot
```

O `uninstall.sh` desfaz o comando, o atalho, o perfil que ele pôs e os botões, sem tocar no que você mudou depois.

## Testes

```bash
python3 -m pytest testes
```

Os testes montam uma casa de mentira e não leem nada da sua. Com o Hefesto no `PYTHONPATH`, eles também conferem o
manifesto e o perfil contra o próprio Hefesto.

## Licença

GPL-3.0-or-later, de Vitória Maria e André Farias (`LICENSE`).
