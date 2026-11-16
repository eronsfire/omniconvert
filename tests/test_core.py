"""Testes do Conversor Eronsfire — foco: autenticação YouTube, integridade e formatos."""

import hashlib
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import mapear_formato, obter_pasta_dados  # noqa: E402
from youtube_auth import YouTubeAuthenticator  # noqa: E402
from updater import AppUpdater  # noqa: E402


# ---------- mapear_formato ----------

def test_mapear_formato_audio_mp3():
    assert mapear_formato("Apenas Áudio (MP3 no PC)") == "audio"
    assert mapear_formato("Apenas Áudio (MP3 no PC)", tem_ffmpeg=True) == "audio"
    assert mapear_formato("Apenas Áudio (MP3 no PC)", tem_ffmpeg=False) == "audio"


def test_mapear_formato_melhor_qualidade_com_ffmpeg():
    assert mapear_formato("Melhor Qualidade (Máxima)", tem_ffmpeg=True) == "bv*+ba/best"


def test_mapear_formato_melhor_qualidade_sem_ffmpeg():
    assert mapear_formato("Melhor Qualidade (Máxima)", tem_ffmpeg=False) == "best[ext=mp4]/best"


def test_mapear_formato_altura_com_ffmpeg_mescla_segmentos():
    assert (
        mapear_formato("Full HD (1080p)", tem_ffmpeg=True)
        == "bv*[height<=1080]+ba/b[height<=1080]/best[height<=1080][ext=mp4]/best"
    )


def test_mapear_formato_altura_sem_ffmpeg_arquivo_unico():
    assert (
        mapear_formato("HD (720p)", tem_ffmpeg=False)
        == "best[height<=720][ext=mp4]/best[height<=720]/best"
    )


def test_mapear_formato_rotulo_desconhecido_cai_no_padrao():
    assert mapear_formato("Qualidade Inventada") == "best[ext=mp4]/best"


def test_mapear_formato_melhor_audio():
    assert mapear_formato("Apenas Áudio (Melhor Qualidade)") == "bestaudio/ba"


# ---------- obter_pasta_dados ----------

def test_obter_pasta_dados_usa_env_var(tmp_path, monkeypatch):
    alvo = tmp_path / "dados_app"
    monkeypatch.setenv("FLET_APP_STORAGE_DATA", str(alvo))
    assert obter_pasta_dados() == str(alvo)
    assert alvo.exists()


# ---------- YouTubeAuthenticator: análise e importação de cookies ----------

COOKIE_VALIDO = (
    "# Netscape HTTP Cookie File\n"
    "# comment line\n"
    "#HttpOnly_.youtube.com\tTRUE\t/\tTRUE\t1893456000\t__Secure-1PSID\tvalor-ps\n"
    ".youtube.com\tTRUE\t/\tTRUE\t1893456000\tSID\tvalor-sid\n"
    ".google.com\tTRUE\t/\tFALSE\t1893456000\tHSID\tvalor-hsid\n"
)

COOKIE_SEM_LOGIN = (
    "# Netscape HTTP Cookie File\n"
    ".youtube.com\tTRUE\t/\tTRUE\t1893456000\tCONSENT\tYES+1\n"
    ".youtube.com\tTRUE\t/\tTRUE\t1893456000\tPREF\tid=abc\n"
)


def _auth(tmp_path, monkeypatch):
    monkeypatch.setenv("FLET_APP_STORAGE_DATA", str(tmp_path / "data"))
    return YouTubeAuthenticator(callback_status=lambda m, e=False: None)


def test_analisar_cookies_detecta_httponly_e_marcadores():
    auth = YouTubeAuthenticator(callback_status=lambda m, e=False: None)
    info = auth.analisar_cookies_netscape(COOKIE_VALIDO)
    assert info["total"] == 3
    assert info["youtube"] == 3
    assert set(info["marcadores"]) == {"__Secure-1PSID", "SID", "HSID"}


def test_importar_cookies_valido_salva_e_verifica(tmp_path, monkeypatch):
    auth = _auth(tmp_path, monkeypatch)
    ok, msg = auth.importar_cookies(COOKIE_VALIDO.encode("utf-8"))
    assert ok, msg
    assert os.path.exists(auth.cookies_path)
    assert auth.verificar_cookies_validos() is True


def test_importar_cookies_sem_marcadores_nao_sobrescreve(tmp_path, monkeypatch):
    auth = _auth(tmp_path, monkeypatch)
    ok, _ = auth.importar_cookies(COOKIE_VALIDO.encode("utf-8"))
    assert ok
    conteudo_backup = open(auth.cookies_path, encoding="utf-8").read()

    ok2, msg2 = auth.importar_cookies(COOKIE_SEM_LOGIN.encode("utf-8"))
    assert not ok2
    assert "login" in msg2.lower()
    # arquivo válido anterior permanece intacto
    assert open(auth.cookies_path, encoding="utf-8").read() == conteudo_backup
    assert auth.verificar_cookies_validos() is True


def test_importar_cookies_lixo_rejeitado(tmp_path, monkeypatch):
    auth = _auth(tmp_path, monkeypatch)
    ok, msg = auth.importar_cookies(b"isso nao e um cookies.txt")
    assert not ok
    assert not os.path.exists(auth.cookies_path)
    assert auth.verificar_cookies_validos() is False


# ---------- AppUpdater: verificação SHA-256 ----------

def test_verificar_sha256_correto(tmp_path):
    up = AppUpdater(callback_status=lambda m, e=False: None)
    arquivo = tmp_path / "app.apk"
    dados = b"conteudo-do-apk-simulado"
    arquivo.write_bytes(dados)
    sha = hashlib.sha256(dados).hexdigest()
    assert up._verificar_sha256(str(arquivo), sha) is True


def test_verificar_sha256_formato_sha256sum(tmp_path):
    up = AppUpdater(callback_status=lambda m, e=False: None)
    arquivo = tmp_path / "app.apk"
    dados = b"conteudo-do-apk-simulado"
    arquivo.write_bytes(dados)
    sha = hashlib.sha256(dados).hexdigest()
    # formato padrão do `sha256sum`: "hash  nome-do-arquivo"
    assert up._verificar_sha256(str(arquivo), f"{sha}  Conversor_Eronsfire_v0.10.0.apk\n") is True


def test_verificar_sha256_incorreto_rejeitado(tmp_path):
    up = AppUpdater(callback_status=lambda m, e=False: None)
    arquivo = tmp_path / "app.apk"
    arquivo.write_bytes(b"conteudo")
    assert up._verificar_sha256(str(arquivo), "0" * 64) is False
