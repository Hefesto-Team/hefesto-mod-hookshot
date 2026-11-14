# Mudanças

## 1.2.0 (14/11/2026)

- O botão «Jogar» da janela abre o jogo pelo Hefesto (`lancador.abrir`), com o ambiente e o perfil
  do jogo; a extensão nunca roda o jogo de dentro da caixa. Num Hefesto que ainda não abre o jogo, o
  «Agora» diz «Jogar: Este Hefesto não abre o jogo».
- Cada controle ganha a chave «Giroscópio». Desligada, a mira pelo giroscópio fica parada naquele
  controle enquanto o jogo está aberto (`mira.ligada`), e volta ao fechar o jogo ou ao parar a
  extensão.
- A extensão traz o modo «Hookshot» na aba Controles, e o perfil do jogo nasce com ele aceso: o
  Hefesto só deixa a extensão desligar o giroscópio do controle cuja seção Controles está no modo
  dela. Quando o modo acende depois do jogo, a chave vale na hora; quando ele apaga, o giroscópio
  volta (`ler:modo.aba`).
- Pede o Hefesto que abre o jogo e desliga o giroscópio de um controle (`pedir:lancador.abrir`,
  `escrever:mira`, `ler:modo.aba`). Um Hefesto mais velho recusa a instalação e diz por quê.

## 1.1.0 (14/11/2026)

- A janela «Configurar»: o Hookshot e o jogo em cor no «Agora», a escolha dos «Botões» (Posição ou
  Nintendo) que vale ao abrir o jogo, um cartão por controle pela cor do plástico com a Luz, os Gatilhos e a
  Vibração, e o guia do dump numa aba.
- A Luz, os Gatilhos Firme e a Vibração Forte de cada controle valem só com o jogo aberto.
- O processo da extensão nasce pelo `python3 -I` do manifesto: o `servidor.py` acha a `janela.py` ao lado dele.

## 1.0.0 (14/11/2026)

- A extensão nasce: o Ocarina of Time do Hookshot na aba Experimental do Hefesto, o comando e o atalho que o abrem,
  os botões do DualSense no `hookshot_options.ini` (com cópia do original), o perfil do jogo e o reconhecimento do
  jogo aberto.
