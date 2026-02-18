# TURKPATENT MCP Server

Türk Patent ve Marka Kurumu (turkpatent.gov.tr) veritabanında marka, patent ve endüstriyel tasarım araması yapan MCP sunucusu.

## Özellikler

- **Marka arama ve detay**: Ad, sahip, Nice sınıfına göre arama; başvuru detaylarını getirme
- **Patent arama ve detay**: Başlık, özet, başvuru sahibi, IPC/CPC sınıfına göre arama; patent detaylarını getirme
- **Tasarım arama ve detay**: Ad, tasarımcı, başvuru sahibi, Locarno sınıfına göre arama; tasarım detaylarını getirme
- **Sayfalama**: Tüm arama araçlarında limit/offset desteği
- **Önbellekleme**: Bellek içi TTL cache (arama: 10 dk, detay: 1 saat)
- **reCAPTCHA**: Capsolver ile otomatik v3 token çözümü

## Araçlar

| Araç | Açıklama |
|------|----------|
| `search_trademarks` | Ada, sahibe, Nice sınıfına göre marka arama |
| `get_trademark_details` | Başvuru numarasına göre marka detayı |
| `search_patents` | Başlık, özet, başvuru sahibi, IPC/CPC ile patent arama |
| `get_patent_details` | Başvuru numarasına göre patent detayı |
| `search_designs` | Ada, tasarımcıya, başvuru sahibine, Locarno sınıfına göre tasarım arama |
| `get_design_details` | Dosya ID'sine göre tasarım detayı (arama sonuçlarından alınır) |

## Gereksinimler

- Python 3.11+
- [Capsolver](https://www.capsolver.com/) API anahtarı

## Kurulum

```bash
# Klonla ve kur
git clone <repo-url>
cd patent-mcp
uv sync

# Ortam değişkenini ayarla
export CAPSOLVER_API_KEY="capsolver-api-anahtarin"
```

## Kullanım

### Stdio (doğrudan)

```bash
uv run python mcp_server.py
```

### HTTP (ASGI)

```bash
uv run uvicorn app:app --host 0.0.0.0 --port 8000
```

### Claude Code

`~/.claude.json` dosyasında `mcpServers` altına ekle:

```json
{
  "turkpatent-mcp": {
    "type": "stdio",
    "command": "uv",
    "args": [
      "run",
      "--directory",
      "/path/to/patent-mcp",
      "python",
      "mcp_server.py"
    ],
    "env": {
      "CAPSOLVER_API_KEY": "capsolver-api-anahtarin"
    }
  }
}
```

### Docker

```bash
docker build -t patent-mcp .
docker run -e CAPSOLVER_API_KEY="anahtar" -p 8000:8000 patent-mcp
```

