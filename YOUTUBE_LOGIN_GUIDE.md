# Login no YouTube (anti "suspeita de bot")

O YouTube bloqueia downloads com a mensagem **"Sign in to confirm you're not a bot"**.
Para resolver, o app passa a usar cookies de uma sessão logada no YouTube.

## Como funciona

O arquivo `youtube_cookies.txt` (formato Netscape, o mesmo do yt-dlp) fica salvo
num diretório **gravável** do app:

- Android/Desktop com build Flet: `FLET_APP_STORAGE_DATA` (definido pelo Flet)
- PC sem essa variável: `~/.omniconvert/youtube_cookies.txt`
- Último recurso: pasta temporária do sistema

Cookies salvos ao lado do código-fonte por versões antigas são migrados
automaticamente na primeira execução.

O ícone de cadeado no topo mostra o estado real (verde = cookies de login válidos).

## Opção 1 — Desktop (PC): login automático

1. Toque no botão de login (ícone de seta) no topo do app.
2. O Chrome abre (Firefox se configurado). Faça login no YouTube normalmente.
3. O app detecta o login automaticamente (verifica os cookies a cada 2 segundos,
   até 5 minutos) e salva o `youtube_cookies.txt`.
4. Pronto — não é preciso fazer mais nada.

Usa o selenium-manager embutido no Selenium 4; não é preciso instalar o driver manualmente.

## Opção 2 — Android (ou qualquer aparelho): importar cookies.txt

Não existe API pública para ler os cookies do Chrome no Android, então o caminho
é exportar o arquivo e importar no app:

1. No Chrome ou Firefox do celular, instale a extensão **"Get cookies.txt LOCALLY"**.
2. Abra o **YouTube já logado** e toque em **Export** na extensão → salva/compartilha o `cookies.txt`.
3. No app, toque no botão de **upload** (ícone ao lado do login) e selecione o `cookies.txt`.
4. O app valida o arquivo (precisa conter cookies de login do YouTube/Google,
   como `SID`, `__Secure-1PSID` ou `LOGIN_INFO`) e salva no armazenamento do app.
5. O bloqueio de suspeita de bot some.

Se o arquivo for aceito mas não tiver cookies de login, o app avisa e **não**
sobrescreve cookies válidos já importados.

## Opção 3 — PC: Firefox direto

O yt-dlp também consegue ler cookies do Firefox sozinho. Se preferir não usar
nem Selenium nem exportar arquivo, exporte manualmente com a extensão
"Get cookies.txt LOCALLY" e use a Opção 2 — funciona igual no PC.

## Notas

- Cookies expiram (sessão do YouTube). Se voltar o bloqueio, exporte/importe de novo.
- Seus cookies ficam só no aparelho e são usados apenas pelo yt-dlp.
- O seletor de importação aceita apenas `.txt` e lê o conteúdo na memória
  (funciona mesmo quando o Android não expõe o caminho do arquivo).
- Verifique o estado a qualquer momento com `obter_info_cookies()` (nº de cookies,
  marcadores de login e data de modificação).
