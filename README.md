# Conversor Eronsfire

App multiplataforma (Android APK e desktop) em **Python + Flet** para baixar
vídeos e áudios de **YouTube, Instagram e TikTok** via [`yt-dlp`](https://github.com/yt-dlp/yt-dlp).

## Recursos

- Downloads em várias qualidades (até 8K) e apenas áudio
- **Anti "suspeita de bot" do YouTube**: login automático no PC (captura de cookies via Selenium) ou importação de `cookies.txt` exportado do navegador (Android) — veja [YOUTUBE_LOGIN_GUIDE.md](YOUTUBE_LOGIN_GUIDE.md)
- **Auto-update** via GitHub Releases (Android): baixa o APK, verifica o **SHA-256** publicado na release e abre o instalador; no PC, abre a página de releases
- Progresso em MB/s e status em tempo real

## Requisitos

- Python 3.11+
- (Opcional, PC) **FFmpeg** no PATH → conversão para MP3 e mescla de vídeo+áudio em qualidade máxima
- (Opcional) **Deno** → runtime JavaScript exigido pelas versões novas do yt-dlp para extração completa do YouTube (já incluído no `requirements.txt`)
- (Android, para login) extensão **"Get cookies.txt LOCALLY"** no Chrome/Firefox

## Rodar no PC

```bash
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
python main.py               # ou: flet run main.py
```

## Build do APK (CI)

A cada push de tag `v*`, o workflow [.github/workflows/build.yml](.github/workflows/build.yml):

1. Instala Flutter, Android SDK, Java 17 e as dependências Python
2. Gera o APK assinado (`arm64-v8a` e `armeabi-v7a`) com `flet build apk`
3. Calcula o **SHA-256** do APK (`Conversor_Eronsfire_vTAG.apk.sha256`)
4. Publica APK + checksum na release (`softprops/action-gh-release@v2`)

Tudo que é necessário para o auto-update funcionar (o updater confere o SHA-256
antes de abrir o instalador, se o `.sha256` existir na release).

## Auto-update

- **Android**: baixa o novo APK para a pasta Downloads, verifica o hash e abre o instalador. APKs antigos do app são removidos antes do próximo download.
- **Desktop**: abre a página de releases no navegador (APK não se instala no PC).

## Estrutura

| Arquivo | Papel |
|---|---|
| `main.py` | UI Flet (abas YouTube / Insta+TikTok, status, progresso) |
| `downloader.py` | yt-dlp: formatos, cookies, FFmpeg |
| `updater.py` | Checa releases, baixa e verifica SHA-256, abre instalador |
| `youtube_auth.py` | Login YouTube (Selenium no PC / importação de cookies.txt) |
| `utils.py` | Pasta de dados gravável, downloads, detecção de Android |
| `config.py` | `APP_VERSION` e repositório GitHub |

## Notas

- No Android, MP3 de verdade exige FFmpeg (não embutido); sem ele, o áudio é baixado no formato nativo do YouTube.
- "Melhor Qualidade" no PC/com FFmpeg usa segmentos vídeo+áudio mesclados; no Android usa o melhor arquivo pré-mesclado disponível.
- Tokens do GitHub, keystore e segredos de assinatura ficam nos **Secrets** do repositório — nunca no código.

## Licença

Sem licença por enquanto. Por padrão de copyright, você (autor) mantém todos os
direitos: ninguém além de você pode reusar, copiar ou redistribuir o código.
Uma licença pode ser adicionada depois a qualquer momento (MIT, proprietária,
etc.). As licenças dos componentes de terceiros embutidos (flet, yt-dlp, etc.)
continuam valendo e devem ser respeitadas/creditadas na distribuição.
