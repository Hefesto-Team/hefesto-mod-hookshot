# Do cartucho ao Hookshot

Este guia vale para quem **tem o cartucho** de The Legend of Zelda: Ocarina of Time do Nintendo Switch 2 e quer
jogá-lo no PC pelo Hookshot. Ele não aponta ROM, chave nem jogo pronto, e não serve para cópia de terceiros. As
fontes de cada afirmação estão em [O-QUE-SE-MEDIU.md](O-QUE-SE-MEDIU.md), medidas em 14/11/2026.

## Antes de tudo: onde baixar o Hookshot

O projeto saiu do GitHub (`NotRexed/Hookshot` responde 404 desde 14/11/2026) e mora agora em
https://git.notrexed.dev/Hookshot/Hookshot (Forgejo do próprio autor, ligado por https://notrexed.dev/). A v2.1.0 de
11/11/2026 está lá, com o `Hookshot-v2.1.0-x86_64.AppImage`. O `hookshot.pro` é um site de terceiros.

- Quem já tem o `Hookshot-v2.1.0-x86_64.AppImage` guarda o arquivo e confere:

  ```bash
  sha256sum Hookshot-v2.1.0-x86_64.AppImage
  # c0b2e958ae00dc560072154f890b9be422724abd9bb522d6afd9922788b86e02
  ```

  Um AppImage de qualquer outra origem que não bata com esse número não é o do projeto.
- O botão «Update» do lançador busca a versão nova no GitHub e, enquanto o projeto estiver fora, não deve achar nada.
- O NX2navi (`tangerineturtle1/NX2navi`, MIT) é outra recompilação do mesmo jogo, viva em 14/11/2026, mas pede outra
  versão do jogo (a 1.1.1) e não foi medida a fundo aqui.

## O que o Hookshot aceita

| o quê | valor |
| --- | --- |
| Program ID | `0400486024DEC000` |
| Atualização | `v131072` |
| Build | `e0f3ccfa` |
| Entrada | um arquivo `.nup`, ou as pastas `romfs` e `exefs` |
| Tamanho de um despejo completo | cerca de 23,8 GB |

Qualquer outra versão para com a mensagem «Hookshot supports build e0f3ccfa». O Hookshot **não publica um SHA ou MD5
do despejo**: o que ele confere é o build ID, a identidade do executável principal do jogo. É essa a conferência
deste guia.

## Por que o cartucho sozinho não basta

1. **A atualização não está no cartucho.** O Hookshot pede a `v131072` e, quando a versão não bate, manda conferir
   se o jogo está «com a atualização instalada». A atualização se baixa no console. Se o cartucho já sai de
   fábrica nessa versão, nenhuma fonte disse.
2. **O conteúdo do cartucho é cifrado.** O `.nup` guarda o jogo **sem criptografia** (`base/` mais
   `updates/131072/`, cada um com `exefs/` e `romfs/`). Tirar a cifra exige as chaves do console.

Logo, o caminho passa pelo Switch 2 onde o cartucho roda e a atualização está instalada.

## A lei e o risco

- No Brasil, a Lei 9.610/98, art. 107, I, responsabiliza quem «alterar, suprimir, modificar ou inutilizar, de
  qualquer maneira, dispositivos técnicos introduzidos nos exemplares das obras e produções protegidas para evitar
  ou restringir sua cópia». Ter o cartucho não muda o texto da lei. Outros países têm regras próprias.
- A Nintendo chama aparelhos de cópia de cartucho, como o Mig Flash Dumper, de «circumvention device».
- O uso do Mig Flash no Switch 2 já fez consoles perderem o serviço online.

Este guia não ensina a abrir o console nem a extrair chaves.

## O hardware

| opção | o que faz | preço | o que se sabe |
| --- | --- | --- | --- |
| O Switch 2 onde o jogo roda | é o único que tem o cartucho, a atualização `v131072` e as chaves no mesmo lugar | US$ 449,99 no lançamento | indispensável: a atualização só existe nele |
| Mig Flash Dumper | lê cartuchos de **Switch** pelo USB | não medido | a leitura de cartão de Switch 2 não foi confirmada por nenhuma fonte; não traz a atualização |
| «switch 2 Game Card Reader» (loja MLGFIX) | leitor USB para Windows ou Mac | sob consulta | promessa da loja, sem fabricante nem formato de saída; não traz a atualização |
| O PC | compila o jogo | — | 45 GB livres (SSD de preferência), 16 GB de RAM, placa com Vulkan 1.3 e mesh shaders (RTX 20 ou mais nova, RX 6000 ou mais nova, Intel Arc) |

Os dois leitores USB entregam, no máximo, a base cifrada do cartucho, sem a atualização. Nenhum deles produz sozinho
o que o Hookshot pede.

## O passo a passo

### 1. Atualizar o jogo no console

Com o cartucho no Switch 2 e o console na internet, deixe o jogo baixar a atualização. O Hookshot só aceita a
`v131072`: uma atualização mais nova que mude o build também será recusada (o Hookshot não diz o que fazer nesse
caso).

### 2. Despejar o cartucho e a atualização

O despejo sai do próprio console, com um programa de despejo rodando nele. Em 14/11/2026 nenhuma fonte pública que
este guia pôde conferir documenta um caminho estável para isso no Switch 2: o `nxdumptool`, a referência do Switch
1, foi arquivado em 22/10/2026 sem Switch 2 confirmado, e as reportagens citam um desbloqueio preso ao PC que some
quando o console reinicia. Esta etapa fica com a documentação da ferramenta que a pessoa escolher, dentro da lei do
lugar onde ela mora.

O que se precisa ter ao fim, no PC, é esta árvore:

```
despejo/
├─ base/
│  ├─ exefs/
│  └─ romfs/
└─ updates/
   └─ 131072/
      ├─ exefs/
      └─ romfs/
```

### 3. Empacotar em `.nup`

Com a ferramenta de referência do formato (`a55uka/nup`, MIT):

```bash
python3 -m venv ~/nup-venv
~/nup-venv/bin/pip install ./tools/nup      # dentro do clone de a55uka/nup
~/nup-venv/bin/nup pack ./despejo ocarina.nup
```

O `pack` lê o title ID do `exefs/main.npdm`, tira o build ID do `exefs/main` e recusa sobrescrever um arquivo que
já existe.

### 4. Conferir antes de compilar

```bash
~/nup-venv/bin/nup info ocarina.nup
ls -l --block-size=M ocarina.nup
```

Tem de aparecer:

- o title ID `0400486024DEC000`;
- um pacote `update` na versão `131072`;
- o build ID começando por `e0f3ccfa`.

Faltando o pacote `update`, ou com outro build ID, o Hookshot vai recusar; volte ao passo 1. O `.nup` pode sair menor
que os 23,8 GB do despejo, porque o formato comprime cada arquivo que encolhe; quem confere o tamanho é a pasta
`despejo/` (`du -sh despejo`). Um despejo de cerca de 23,3 GB está incompleto: o Hookshot compila mesmo assim, mas
escreve `hookshot_damaged_files.txt` na pasta do jogo com cada arquivo estragado, e o certo é despejar de novo.

### 5. Compilar no Linux

```bash
chmod +x Hookshot-v2.1.0-x86_64.AppImage
./Hookshot-v2.1.0-x86_64.AppImage
```

Na janela do builder: em «Game files», escolha o `.nup`; em «Save the game to», deixe `~/Games/Hookshot`;
escolha o idioma e aperte «Build». Leva de 10 a 45 minutos. A segunda conferência acontece aqui: o builder lê o
build ID e para com «Hookshot supports build e0f3ccfa» se a versão não for a certa.

Sem janela, o mesmo AppImage faz:

```bash
./Hookshot-v2.1.0-x86_64.AppImage --cli --nup ~/ocarina.nup --out ~/Games/Hookshot
./Hookshot-v2.1.0-x86_64.AppImage --play ~/Games/Hookshot
```

Deixe o AppImage onde ele está: o lançador usa o arquivo para se atualizar. Depois de compilar, o `.nup` pode ir
para outro disco: os arquivos do jogo ficam na pasta do jogo e uma atualização não pede o `.nup` de novo.

### 6. O que nunca se compartilha

O `.nup`, a pasta `~/Games/Hookshot` (com o `bin/hookshot`), os saves em `~/.local/share/hookshot` e os caches
saem do jogo de quem o comprou. A licença do Hookshot e o readme dizem para não distribuí-los.
