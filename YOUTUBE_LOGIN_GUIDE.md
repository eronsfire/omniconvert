# 🔐 Guia de Autenticação YouTube - Downloader Eronsfire

## ✨ O que foi implementado

Seu app agora possui **autenticação automática do YouTube com Selenium**, que permite fazer login uma única vez e usar cookies para downloads ilimitados, contornando bloqueios de bot.

---

## 🚀 Como usar

### **1️⃣ Fazer Login (primeira vez)**

1. Abra o app
2. Clique no botão **🔓 Login** (ícone de cadeado no topo da interface)
3. Um navegador Firefox/Chrome se abrirá automaticamente
4. **Faça login no YouTube normalmente** (email e senha)
5. Após o login, o app capturará automaticamente seus cookies
6. O ícone de cadeado mudará para 🔒 (verde) indicando sucesso

**⏱️ Você tem até 5 minutos para fazer login no navegador**

---

## 📁 Como funciona

### **Antes do Login:**
```
❌ YouTube bloqueia como suspeita de bot
❌ Mensagem: "Sign in to confirm you're not a bot"
```

### **Depois do Login:**
```
✅ Cookies salvos em: youtube_cookies.txt
✅ Autenticado no YouTube
✅ Downloads funcionam normalmente
✅ Bloqueia de bot contornado
```

---

## 🔄 Downloads com Autenticação

Após fazer login:

1. Cole a URL do vídeo YouTube
2. Escolha a qualidade desejada
3. Clique em **Baixar YouTube**
4. O app automaticamente usa seus cookies para autenticar

**Sem limite de downloads, sem suspeita de bot!**

---

## ⚙️ Detalhes Técnicos

### **Como os cookies são salvos**

- **Formato:** Netscape (compatível com yt-dlp)
- **Localização:** `youtube_cookies.txt` na pasta do app
- **Segurança:** Permissões restritivas (0o600)
- **Persistência:** Salvos entre execuções

### **Fluxo de Login**

```
1. Clica em "Login" 
   ↓
2. Selenium abre Firefox/Chrome
   ↓
3. YouTube detecta login humano (não é bot)
   ↓
4. App captura cookies após detecção de login
   ↓
5. Cookies salvos em youtube_cookies.txt
   ↓
6. yt-dlp usa cookies em todos os downloads
```

---

## 🛠️ Troubleshooting

### **Q: O navegador não abriu**
**A:** Verifique se tem Firefox ou Chrome instalados. Se o Selenium não conseguir encontrar, instale:
- Firefox: https://www.mozilla.org/firefox/
- Chrome: https://www.google.com/chrome/

### **Q: Timeout no login (5 minutos passaram)**
**A:** Clique em "Login" novamente e faça o login mais rápido. A detecção do login é automática.

### **Q: Continuação com erro de bot após login**
**A:** 
1. Clique em "Login" novamente
2. Faça logout no YouTube primeiro (se necessário)
3. Faça novo login
4. Os cookies antigos serão sobrescritos

### **Q: Como remover os cookies?**
**A:** Apague manualmente o arquivo `youtube_cookies.txt` na pasta do app.

---

## 🔐 Segurança

✅ Seus dados de login **NÃO são salvos** no app
✅ Apenas os **cookies da sessão** são armazenados
✅ Cookies salvos localmente com permissões restritas
✅ YouTube reconhece como login legítimo (não bot)

---

## 📊 Status de Autenticação

Observe o ícone no topo da interface:

| Ícone | Status | Significado |
|-------|--------|------------|
| 🔓 (laranja) | Não autenticado | Faça login para usar |
| 🔒 (verde) | Autenticado | Pronto para baixar |

---

## 🎯 Para Múltiplos Celulares

Se quer distribuir para vários usuários:

1. **Cada usuário faz login uma vez** no seu dispositivo
2. App captura e salva cookies **localmente**
3. Todos os downloads futuros usam esses cookies
4. **Cada dispositivo tem seus próprios cookies**

Não há limite de cookies ou sessões simultâneas!

---

## 📝 Changelog

**v0.9.9.2+**
- ✨ Adicionado suporte a autenticação Selenium
- ✨ Captura automática de cookies
- ✨ Indicador visual de status de autenticação
- ✨ Headers realistas para evitar bloqueios
- ✨ Retry automático em falhas
- 🔧 Melhorado tratamento de erros de bot

---

## 💡 Dicas

1. **Não compartilhe cookies:** Cada usuário deve fazer seu próprio login
2. **Login único:** Uma vez feito login, use indefinidamente
3. **Velocidade:** Com cookies válidos, downloads são mais rápidos
4. **Privacidade:** Você pode fazer logout da conta YouTube no navegador após o app capturar cookies

---

## 🆘 Suporte

Se encontrar problemas:

1. Verifique se o Firefox/Chrome está instalado
2. Tente fazer login manualmente no YouTube primeiro (navegador normal)
3. Limpe os cookies e tente novamente
4. Reinicie o app

---

**Desenvolvido com ❤️ por Eronsfire Team**
