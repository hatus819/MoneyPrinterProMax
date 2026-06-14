# Money Printer Pro Max 💸 — Gerador Automático de Vídeos Curtos

[English](README.md) | **Português (Brasil)**

Transforme um tema em texto num vídeo curto pronto e legendado (vertical ou horizontal) — roteiro, narração, imagens de banco, legendas e metadados prontos para colar, tudo gerado automaticamente.

Este é um fork aprimorado do [FujiwaraChoki/MoneyPrinter](https://github.com/FujiwaraChoki/MoneyPrinter), com vários recursos adicionais (veja [Recursos](#-recursos)).

> ⚠️ **Ele não publica em lugar nenhum por você.** Cada vídeo é salvo como um arquivo que você mesmo publica. Veja [Observações importantes](#-observações-importantes).

---

## ✨ Recursos

- **Tema → vídeo completo** usando um LLM local (Ollama) para o roteiro — sem necessidade de API de IA paga.
- **Várias proporções de tela**: `9:16` (Shorts/TikTok/Reels), `16:9` (YouTube), `1:1` (Instagram), `4:5` (feed).
- **Controle de duração mínima** — garante que os vídeos tenham pelo menos N segundos (ex.: 60s).
- **Metadados gerados automaticamente** — cada vídeo ganha um `.txt` com Título, Descrição, Hashtags e Palavras-chave, prontos para colar na hora de publicar.
- **Legendas precisas** via AssemblyAI (opcional) ou tempo estimado localmente.
- **Modo em lote** — coloque uma lista inteira de temas num arquivo de texto e deixe rodando.
- **Saída persistente** — cada vídeo é salvo com um nome único em `output/`, então um trabalho nunca sobrescreve o outro.
- **Fila confiável** — uma fila de trabalhos baseada em banco de dados (Postgres) com um worker separado, que sobrevive a reinicializações.

## 🧱 Como funciona

```
Seu tema → Ollama (roteiro) → Pexels (imagens de banco) → TikTok TTS (narração)
        → legendas → montagem do vídeo (9:16/16:9/…) → output/<nome>.mp4 + <nome>.txt
```

Os componentes rodam em Docker: um **frontend** (interface web), uma **API backend**, um **worker** que renderiza os vídeos e o **Postgres** para a fila. O **Ollama** roda na sua máquina (host).

---

## ✅ Pré-requisitos

| Ferramenta | Para quê | Observações |
|---|---|---|
| **Docker + Docker Compose** | Roda toda a stack | [Instalar o Docker](https://docs.docker.com/get-docker/) |
| **Ollama** | Gera o roteiro localmente | [Instalar o Ollama](https://ollama.com/download) |
| **Chave de API da Pexels** | Imagens de banco (grátis) | https://www.pexels.com/api/ |
| **`sessionid` do TikTok** | Voz da narração (grátis) | Dos cookies do navegador em tiktok.com |
| **Chave de API da AssemblyAI** | *Opcional* — legendas mais precisas (plano grátis) | https://www.assemblyai.com/ |

> O ImageMagick e o FFmpeg **já estão incluídos** na imagem Docker — você não precisa instalá-los.

---

## 🚀 Instalação

### 1. Clonar e configurar

```bash
git clone <url-do-seu-repositorio> MoneyPrinter
cd MoneyPrinter
cp .env.example .env
```

Edite o `.env` e preencha:

```env
PEXELS_API_KEY="sua_chave_pexels"
TIKTOK_SESSION_ID="seu_sessionid_tiktok"
ASSEMBLY_AI_API_KEY=""          # opcional, para legendas melhores

# Permite que os contêineres Docker acessem o Ollama rodando no seu host:
OLLAMA_BASE_URL="http://host.docker.internal:11434"
OLLAMA_MODEL="llama3.1:8b"
```

**Como obter as chaves:**
- **Pexels:** cadastre-se em https://www.pexels.com/api/ → copie "Your API Key".
- **`sessionid` do TikTok:** faça login em tiktok.com → abra as DevTools (`F12` / `Cmd+Opt+I`) → **Application → Cookies → tiktok.com** → copie o valor do cookie `sessionid`.

### 2. Iniciar o Ollama (no seu host)

O Ollama precisa escutar em todas as interfaces para que os contêineres Docker consigam acessá-lo:

```bash
OLLAMA_HOST=0.0.0.0:11434 ollama serve     # deixe rodando em um terminal
ollama pull llama3.1:8b                     # em outro terminal, apenas uma vez
```

> 🔒 Expor o Ollama em `0.0.0.0` o deixa acessível na sua rede local. Isso é necessário para o acesso Docker → host. Numa máquina confiável tudo bem; caso contrário, restrinja com o seu firewall.

### 3. Iniciar o aplicativo

```bash
docker compose up -d --build
```

A **primeira build leva alguns minutos** (ela compila o ImageMagick). Depois que subir:

- **Interface web:** http://localhost:8001
- **API backend:** http://localhost:8080

Para parar: `docker compose down`.

---

## 🎬 Como usar

### Opção A — Interface web (um vídeo)

1. Abra http://localhost:8001
2. Digite um **tema do vídeo**.
3. Expanda as opções e defina:
   - **Aspect Ratio** (proporção) — 9:16 / 16:9 / 1:1 / 4:5
   - **Min Duration** (duração mínima) — em segundos (ex.: `60`; use `0` para usar a contagem de Parágrafos)
   - **Posição / cor da legenda**, **Threads** (velocidade de renderização), etc.
4. Escolha o **modelo do Ollama** na lista.
5. Clique em **Generate** e acompanhe o log ao vivo.
6. O vídeo pronto + seus metadados aparecem na pasta [`output/`](output/).

### Opção B — Modo em lote (vários vídeos)

Edite o `topics.txt` (um tema por linha) e rode:

```bash
python3 batch_generate.py
```

Formato do `topics.txt`:

```text
# Linhas começando com '#' são ignoradas
3 fatos surpreendentes sobre o oceano profundo
A história do café em 60 segundos
A ciência por trás dos sonhos | 16:9      # proporção opcional por linha
```

Opções úteis:

```bash
python3 batch_generate.py meustemas.txt \
  --aspect 16:9 \          # proporção padrão para todas as linhas
  --min-duration 60 \      # segundos mínimos por vídeo
  --threads 6 \            # threads de renderização
  --voice en_us_001 \
  --wait                   # espera cada um terminar (mostra o caminho do resultado)
```

Os vídeos entram na fila e são renderizados **um de cada vez** em segundo plano — feche o notebook e volte com a pasta `output/` cheia.

---

## 📁 Saída (output)

Cada vídeo gerado produz dois arquivos em `output/`:

```
a-historia-do-cafe-6517a129.mp4   ← o vídeo
a-historia-do-cafe-6517a129.txt   ← TÍTULO / DESCRIÇÃO / HASHTAGS / PALAVRAS-CHAVE
```

Abra o `.txt` e copie/cole o título, a descrição e as hashtags na hora de publicar.

---

## ⚙️ Referência de configuração (`.env`)

| Variável | Obrigatória | Descrição |
|---|---|---|
| `PEXELS_API_KEY` | ✅ | Chave da API de vídeos da Pexels |
| `TIKTOK_SESSION_ID` | ✅ | Cookie `sessionid` do TikTok (para a voz/TTS) |
| `OLLAMA_BASE_URL` | ✅ (Docker) | `http://host.docker.internal:11434` para os contêineres acessarem o Ollama no host |
| `OLLAMA_MODEL` | – | Modelo padrão (default `llama3.1:8b`) |
| `ASSEMBLY_AI_API_KEY` | – | Opcional; ativa as legendas da AssemblyAI |
| `IMAGEMAGICK_BINARY` | – | Deixe vazio (tratado dentro do Docker) |
| `POSTGRES_DB` / `POSTGRES_USER` / `POSTGRES_PASSWORD` | – | Padrões do Postgres |
| `DATABASE_URL` | – | Deixe vazio para usar o Postgres incluído |

---

## 🛠️ Solução de problemas

- **A interface não mostra modelos / "could not connect to Ollama":** confirme que o Ollama está rodando com `OLLAMA_HOST=0.0.0.0:11434` e que `OLLAMA_BASE_URL` no `.env` é `http://host.docker.internal:11434`. Teste: `curl http://localhost:8080/api/models`.
- **A renderização falha no fim / erro de legenda:** geralmente é um caso específico de legenda/tempo — tente outro tema ou configure uma `ASSEMBLY_AI_API_KEY`.
- **A narração falha:** o TTS do TikTok é sensível à região; atualize seu `TIKTOK_SESSION_ID` (ele expira) ou use uma sessão dos EUA.
- **Renderização lenta:** vídeos mais longos demoram mais — o gargalo é gravar as legendas quadro a quadro, então o tempo de renderização depende mais da duração do vídeo do que das `Threads`.
- **Ver a fila / logs:** `docker compose logs -f worker`.

---

## 📝 Observações importantes

- **Sem publicação automática.** O app gera um arquivo; você publica manualmente. Publicar automaticamente no TikTok via cookies de sessão viola os Termos de Serviço e arrisca o banimento da conta, por isso isso não está incluído de propósito.
- **Qualidade do conteúdo e regras das plataformas.** As plataformas limitam cada vez mais conteúdo de IA repetitivo e produzido em massa. Aposte num nicho específico e varie o formato.
- **Qualidade da voz.** O TTS do TikTok embutido soa robótico. Para qualidade profissional, considere integrar um provedor de TTS licenciado.

---

## 🙏 Créditos e Licença

- Baseado no [FujiwaraChoki/MoneyPrinter](https://github.com/FujiwaraChoki/MoneyPrinter).
- Licenciado sob a **Licença MIT** — veja [`LICENSE`](LICENSE). Você é livre para usar, modificar e distribuir, inclusive comercialmente.
