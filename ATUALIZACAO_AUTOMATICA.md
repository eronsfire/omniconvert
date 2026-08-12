# 🔄 Atualização Automática com Limpeza

## ✨ Sistema de Atualização Inteligente

Seu app agora possui **atualização totalmente automática** que:
- ✅ Baixa a nova versão
- ✅ Abre o instalador automaticamente
- ✅ Apaga o APK após a instalação

Tudo **sem intervenção do usuário**!

---

## 🎯 Fluxo de Atualização

### **Processo Automático:**

```
1. Usuário clica "Buscar Atualização" 🔄
          ↓
2. Sistema verifica GitHub
          ↓
3. Encontra nova versão disponível
          ↓
4. Apaga versões antigas da pasta Download
          ↓
5. Baixa a nova versão
          ↓
6. Barra de progresso mostra download
          ↓
7. Abre o instalador do sistema automaticamente
          ↓
8. Usuário clica "Instalar" (nativo do Android/Windows)
          ↓
9. Após ~30 segundos, APK é deletado automaticamente ✓
```

---

## 📱 No Android

1. Clica no botão de atualização
2. Sistema verifica GitHub
3. Se houver versão nova → **Abre a tela de instalação do Android**
4. Usuário confirma "Atualizar"
5. App é atualizado no lugar
6. Arquivo APK é **deletado automaticamente** da pasta Download

**Resultado:** Sem arquivos lixo na pasta Download! 🎉

---

## 💻 No PC (Windows)

1. Clica no botão de atualização
2. Sistema verifica GitHub
3. Se houver versão nova → **Abre o instalador (exe, apk, ou o que estiver configurado)**
4. Usuário confirma a instalação
5. Arquivo de atualização é **deletado automaticamente**

---

## ⚙️ Como Funciona a Limpeza

### **Etapas do Sistema:**

```python
# 1. Deleta APKs antigos
for apk_antigo in glob.glob("Downloads/*.apk"):
    os.remove(apk_antigo)

# 2. Baixa nova versão
requests.get(url, stream=True)

# 3. Abre instalador
subprocess.run(cmd)

# 4. Aguarda 30 segundos
time.sleep(30)

# 5. Deleta o APK baixado
os.remove(caminho_apk)
```

### **Tratamento de Erros:**

- ❌ Se o arquivo ainda estiver em uso: **Tenta novamente em 10 segundos**
- ❌ Se ainda não conseguir: **Deixa log e continua funcionando**

---

## 🔍 Detecção de Ambiente

O código **detecta automaticamente** se está no:
- 📱 **Android:** Usa comando `am start` (sistema nativo)
- 💻 **PC Windows:** Usa `os.startfile()` (abre com app padrão)

---

## 📊 Comportamento por Plataforma

### **Android:**
```
Clica atualizar
    ↓
Verifica GitHub (API)
    ↓
Encontra versão v1.0.1
    ↓
Baixa APK (~30-50 MB em ~2 minutos)
    ↓
Abre tela nativa: "Atualizar Conversor Eronsfire?"
    ↓
Usuário clica "Instalar"
    ↓
Sistema instala no lugar
    ↓
Thread em background aguarda 30s
    ↓
APK é deletado ✓
    ↓
Pasta Download limpa! 🎉
```

### **PC Windows:**
```
Clica atualizar
    ↓
Verifica GitHub (API)
    ↓
Encontra versão v1.0.1
    ↓
Baixa arquivo (~50 MB)
    ↓
Abre com programa padrão (Explorador de Arquivos ou Instalador)
    ↓
Usuário confirma instalação
    ↓
Thread em background aguarda 30s
    ↓
Arquivo é deletado ✓
    ↓
Downloads limpo! 🎉
```

---

## 🔧 Arquivos Modificados

### **updater.py** - Sistema de Atualização

**Novas Funcionalidades:**

1. `_chamar_instalador_sistema()`
   - Detecta Android vs PC
   - Abre instalador apropriado

2. `_limpar_apk_apos_instalacao()`
   - Thread separada que monitora
   - Aguarda 30 segundos
   - Tenta deletar com retry
   - Não trava o app

**Melhorias:**

- ✅ Logs detalhados (DEBUG, INFO, SUCCESS, ERROR)
- ✅ Tratamento de PermissionError
- ✅ Retry automático
- ✅ Funciona em PC e Android

---

## 📥 Como Usar

### **Para o Usuário:**

1. Abra o app
2. Clique no botão 🔄 "Buscar Atualização"
3. Sistema faz tudo automaticamente:
   - Baixa
   - Instala
   - Limpa arquivo

**Pronto!** Sem precisar fazer nada manualmente.

### **Para Você (Desenvolvedor):**

Para lançar uma nova versão:

1. Crie uma tag no GitHub: `v1.0.1`
2. Faça o release no GitHub
3. Anexe o arquivo `.apk` ao release
4. Pronto! Usuários receberão atualização automática

---

## ⚡ Tempo Estimado

| Etapa | Tempo |
|-------|-------|
| Verificar GitHub | 2-3 segundos |
| Baixar APK (30 MB) | 1-3 minutos (depende conexão) |
| Instalação | 10-30 segundos |
| Limpeza automática | ~30 segundos |
| **Total** | ~2-4 minutos |

---

## 🆘 Troubleshooting

### **Q: APK não é deletado**
**A:** Isso pode significar:
- Arquivo ainda está em uso
- O sistema está instalando (demore mais)
- Permissão negada (não crítico, app continua funcionando)

### **Q: Instalador não abre**
**A:**
- No Android: Verifique se "Instalar de fontes desconhecidas" está ativado
- No PC: Verifique permissões de arquivo

### **Q: "Erro ao consultar GitHub"**
**A:** 
- Sem conexão à internet
- GitHub está indisponível
- Limite de requisições da API excedido

---

## 🔐 Segurança

✅ Busca apenas releases oficiais do GitHub  
✅ Valida token de versão  
✅ Baixa apenas arquivos `.apk`  
✅ Não requer permissões especiais  
✅ APK deletado automaticamente  

---

## ✨ Benefícios

| Antes | Depois |
|-------|--------|
| ❌ Usuário baixa manualmente | ✅ App baixa automaticamente |
| ❌ Procura Downloads | ✅ Abre instalador direto |
| ❌ Clica arquivo APK | ✅ Confirmação simples |
| ❌ Instala | ✅ Instala automaticamente |
| ❌ Volta para Download | ✅ APK deletado sozinho |
| ❌ Deleta arquivo manualmente | ✅ Zero trabalho manual |

---

## 🎯 Próximas Versões

Para manter os usuários sempre atualizados, você pode:

1. **Checar automaticamente** ao abrir app (opcional)
2. **Notificar** quando versão nova estiver disponível
3. **Forçar atualização** para versão crítica (se necessário)

---

**Desenvolvido com ❤️ por Eronsfire Team**

Sistema automático de atualização já está ativo! 🚀
