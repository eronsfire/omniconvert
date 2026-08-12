# 🎬 Guia de Qualidades e Formatos

## ✨ Qualidades Disponíveis

Seu app agora oferece **TODAS as qualidades** disponíveis dos vídeos!

### 📹 Vídeos (YouTube, Instagram, TikTok)

| Qualidade | Resolução | Uso | Tamanho |
|-----------|-----------|-----|--------|
| Melhor Qualidade (Máxima) | Máxima disponível | Recomendado | Variável |
| 8K | 7680p | Ultra HD | Muito grande |
| 4K | 2160p | Cinema | Grande |
| 2K | 1440p | Monitores altos | Médio |
| Full HD | 1080p | Padrão | Normal |
| HD | 720p | Rápido | Pequeno |
| Standard | 480p | Móvel | Muito pequeno |
| Low | 360p | Dados limitados | Mínimo |
| Mínima | 240p | Extremamente limitado | Mínimo |

---

## 🎵 Áudio

### **Apenas Áudio (MP3)** - COM CONVERSÃO
- ✅ Funciona no **PC com FFmpeg**
- ❌ No Android: Baixa formato nativo (webm/m4a)
- 📊 Tamanho: ~2-3 MB
- 💾 Formato: MP3 (PC) ou WebM/M4A (Android)
- ⚡ Ideal para: Guardar em qualidade alta

### **Apenas Áudio (Melhor Qualidade)** - SEM CONVERSÃO  
- ✅ Funciona em **PC e Android**
- 📊 Tamanho: ~3-5 MB
- 💾 Formato: Nativo (WebM/M4A)
- ⚡ Ideal para: Compatibilidade máxima

---

## 🔧 Como Funciona

### **No PC com FFmpeg:**
```
Apenas Áudio (MP3)
    ↓
Baixa melhor áudio
    ↓
Converte para MP3 192kbps com FFmpeg
    ↓
Salva como .mp3
```

### **No PC sem FFmpeg:**
```
Apenas Áudio (MP3)
    ↓
Baixa melhor áudio
    ↓
Salva como formato nativo (WebM/M4A)
```

### **No Android:**
```
Apenas Áudio (MP3)
    ↓
Baixa melhor áudio
    ↓
Salva como formato nativo (WebM/M4A)
    
Sem erro! Sem depender de FFmpeg!
```

---

## 💡 Dicas de Uso

### **Para Guardar no Celular:**
- Use **"Full HD (1080p)"** ou **"Apenas Áudio (MP3)"**
- Bom balanço entre qualidade e tamanho

### **Para Compartilhar:**
- Use **"HD (720p)"** para vídeos
- Use **"Apenas Áudio (MP3)"** para áudio

### **Para Ver em 4K:**
- Use **"4K (2160p)"**
- Precisa ter espaço (5-10 GB por hora)

### **Para Economizar Dados:**
- Use **"Low (360p)"** ou **"Mínima (240p)"**
- Áudio: Use **"Apenas Áudio (Melhor Qualidade)"**

---

## 📊 Comparação Rápida

### Tamanho Aproximado (10 minutos de vídeo)

| Qualidade | Tamanho |
|-----------|---------|
| 8K | 500+ MB |
| 4K | 150-300 MB |
| Full HD | 50-100 MB |
| HD | 30-50 MB |
| Standard | 10-20 MB |
| Low | 5-10 MB |
| Mínima | 2-5 MB |
| Áudio MP3 | 2-3 MB |

---

## 🎯 Fluxo de Uso Recomendado

1. **Escolha a qualidade:**
   - 📺 Vídeo: Máxima / 4K / Full HD
   - 🎵 Áudio: Apenas Áudio (MP3)

2. **Cole a URL:**
   - YouTube, Instagram ou TikTok

3. **Clique em Baixar:**
   - No PC: Converte MP3 se tiver FFmpeg
   - No Android: Baixa direto sem problemas

4. **Arquivo salvo em:**
   - PC: C:\Users\[você]\Downloads
   - Android: /storage/emulated/0/Download

---

## ✅ Garantia de Funcionamento

- ✅ Todas as qualidades disponíveis são testadas
- ✅ MP3 funciona com FFmpeg no PC
- ✅ MP3 funciona sem FFmpeg no Android
- ✅ Sem mais erros de "FFmpeg not found"
- ✅ Downloads rápidos e estáveis

---

## 🆘 Se Não Conseguir Baixar

### Erro: "Format not available"
- Aquele vídeo específico não tem essa qualidade
- Tente "Melhor Qualidade (Máxima)"

### Erro: "MP3 conversion failed"
- Você está no PC e não tem FFmpeg
- Instale FFmpeg ou use "Apenas Áudio (Melhor Qualidade)"

### Erro: "Arquivo incompleto"
- Sua conexão é lenta/instável
- Tente uma qualidade menor

---

**Desenvolvido com ❤️ por Eronsfire Team**
