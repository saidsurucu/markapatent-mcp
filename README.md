# Marka Patent MCP: TÜRKPATENT Marka, Patent ve Tasarım Araştırma MCP Sunucusu

Bu proje, Türk Patent ve Marka Kurumu'na ait araştırma portalına (`turkpatent.gov.tr`) erişimi kolaylaştıran bir [FastMCP](https://gofastmcp.com/) sunucusu oluşturur. Bu sayede, TÜRKPATENT veritabanında marka, patent ve endüstriyel tasarım araması yapma işlemleri, Model Context Protocol (MCP) destekleyen LLM uygulamaları (örneğin Claude Desktop veya [5ire](https://5ire.app)) ve diğer istemciler tarafından araç (tool) olarak kullanılabilir hale gelir.

🎯 **Temel Özellikler**

* TÜRKPATENT araştırma portalına programatik erişim için standart bir MCP arayüzü.
* **6 araç** ile kapsamlı fikri mülkiyet araştırması:
    * **Marka** — Ada, sahibe, Nice sınıfına göre arama ve detay
    * **Patent** — Başlık, özet, buluş sahibi, başvuru sahibi, IPC/CPC sınıfına göre arama ve detay
    * **Endüstriyel Tasarım** — Ada, tasarımcıya, başvuru sahibine, Locarno sınıfına göre arama ve detay
* Gelişmiş özellikler:
    * Tüm arama araçlarında sayfalama (limit/offset) desteği
    * In-memory caching (arama: 10 dk, detay: 1 saat)
    * reCAPTCHA v3 otomatik token çözümü (Capsolver ile)
    * Arama operatörleri: içinde geçen, ile başlayan, eşit (marka aramasında)

---
🌐 **En Kolay Yol: Ücretsiz Remote MCP (Claude Desktop için)**

Hiçbir kurulum gerektirmeyen, doğrudan kullanıma hazır MCP sunucusu:

1. Claude Desktop'ı açın
2. **Settings > Connectors > Add custom connector**
3. Açılan pencerede:
   * **Name:** `Marka Patent MCP`
   * **URL:** `https://markapatent-mcp.fastmcp.app/mcp`
4. **Save** butonuna basın

Hepsi bu kadar! Artık Marka Patent MCP ile konuşabilirsiniz.

> **Not:** Bu ücretsiz sunucu topluluk için sağlanmaktadır. Yoğun kullanım için kendi sunucunuzu kurmanız önerilir.

### Google Antigravity ile Kullanım

1. **Agent session** açın ve editörün yan panelindeki **"…"** dropdown menüsüne tıklayın
2. **MCP Servers** seçeneğini seçin - MCP Store açılacak
3. Üstteki **Manage MCP Servers** butonuna tıklayın
4. **View raw config** seçeneğine tıklayın
5. `mcp_config.json` dosyasına aşağıdaki yapılandırmayı ekleyin:

```json
{
  "mcpServers": {
    "markapatent-mcp": {
      "serverUrl": "https://markapatent-mcp.fastmcp.app/mcp/",
      "headers": {
        "Content-Type": "application/json"
      }
    }
  }
}
```

---
🚀 **Claude Haricindeki Modellerle Kullanmak İçin Kolay Kurulum (Örnek: 5ire için)**

Bu bölüm, Marka Patent MCP aracını 5ire gibi Claude Desktop dışındaki MCP istemcileriyle kullanmak isteyenler içindir.

* **Python Kurulumu:** Sisteminizde Python 3.11 veya üzeri kurulu olmalıdır. Kurulum sırasında "**Add Python to PATH**" seçeneğini işaretlemeyi unutmayın. [Buradan](https://www.python.org/downloads/) indirebilirsiniz.
* **Git Kurulumu (Windows):** Bilgisayarınıza [git](https://git-scm.com/downloads/win) yazılımını indirip kurun.
* **`uv` Kurulumu:**
    * **Windows (PowerShell):** `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`
    * **Mac/Linux (Terminal):** `curl -LsSf https://astral.sh/uv/install.sh | sh`
* [5ire](https://5ire.app) MCP istemcisini indirip kurun.
* 5ire'ı açın. **Workspace -> Providers** menüsünden kullanmak istediğiniz LLM servisinin API anahtarını girin.
* **Tools** menüsüne girin. **+Local** veya **New** yazan butona basın.
    * **Tool Key:** `markapatentmcp`
    * **Name:** `Marka Patent MCP`
    * **Command:**
        ```
        uvx --from git+https://github.com/saidsurucu/markapatent-mcp markapatent-mcp
        ```
    * **Save** butonuna basarak kaydedin.
* **Tools** altında **Marka Patent MCP**'yi etkinleştirin (yeşil ışık yanmalı).

> **Not:** `CAPSOLVER_API_KEY` ortam değişkeninin ayarlanmış olması gerekir. [Capsolver](https://www.capsolver.com/) üzerinden API anahtarı alabilirsiniz.

---
⚙️ **Claude Desktop Manuel Kurulumu**

1. **Ön Gereksinimler:** Python 3.11+, `uv`, ve bir Capsolver API anahtarı.
2. Claude Desktop **Settings -> Developer -> Edit Config**.
3. Açılan `claude_desktop_config.json` dosyasına `mcpServers` altına ekleyin:

    ```json
    {
      "mcpServers": {
        "Marka Patent MCP": {
          "command": "uvx",
          "args": [
            "--from",
            "git+https://github.com/saidsurucu/markapatent-mcp",
            "markapatent-mcp"
          ],
          "env": {
            "CAPSOLVER_API_KEY": "capsolver-api-anahtariniz"
          }
        }
      }
    }
    ```
4. Claude Desktop'ı kapatıp yeniden başlatın.

---
🔑 **API Anahtarı**

### Capsolver (Zorunlu)

TÜRKPATENT portalı reCAPTCHA v3 koruması kullanmaktadır. Bu korumayı aşmak için Capsolver API anahtarı gereklidir:

1. [Capsolver](https://www.capsolver.com/) üzerinden hesap oluşturun ve API anahtarı alın
2. Environment variable olarak ayarlayın:
   ```bash
   export CAPSOLVER_API_KEY="your_api_key_here"
   ```

---
🛠️ **Kullanılabilir Araçlar (MCP Tools)**

Bu FastMCP sunucusu LLM modelleri için **6 araç** sunar.

### Marka Araçları

#### **`search_trademarks`** — Marka Arama
Türkiye'de tescilli markaları arar.
* `trademark_name`: Marka adı
* `name_operator`: Arama operatörü — `contains` (içinde geçen, varsayılan), `startsWith` (ile başlayan), `equals` (eşit)
* `holder_name`: Marka sahibi/başvuru sahibi adı
* `holder_name_operator`: Sahip adı arama operatörü — `startsWith` (varsayılan), `equals`
* `nice_classes`: Nice sınıflandırma kodları, virgülle ayrılmış (örn. `"9,35,42"`)
* `limit`: Sayfa başına sonuç sayısı (varsayılan: 20, maks: 100)
* `offset`: Sayfalama ofseti

#### **`get_trademark_details`** — Marka Detayı
Belirli bir marka başvurusunun detaylı bilgilerini getirir.
* `application_number`: Marka başvuru numarası (örn. `"T/01853"`, `"2020/12345"`)

**Dönen bilgiler:** Marka adı, sahibi, Nice sınıfları, başvuru tarihi, tescil durumu, bülten numaraları, koruma tarihleri.

### Patent Araçları

#### **`search_patents`** — Patent Arama
Türkiye'de tescilli patentleri arar.
* `title`: Buluş başlığı
* `abstract`: Buluş özeti anahtar kelimeleri
* `owner`: Buluş sahibi (mucit) adı
* `applicant`: Başvuru sahibi adı
* `application_number`: Patent başvuru numarası
* `ipc_class`: IPC sınıflandırma kodu (örn. `"G06F"`, `"H01Q"`)
* `cpc_class`: CPC sınıflandırma kodu
* `attorney`: Patent vekili adı
* `limit`: Sayfa başına sonuç sayısı (varsayılan: 20, maks: 100)
* `offset`: Sayfalama ofseti

#### **`get_patent_details`** — Patent Detayı
Belirli bir patent başvurusunun detaylı bilgilerini getirir.
* `application_number`: Patent başvuru numarası

**Dönen bilgiler:** Başlık, özet, buluş sahipleri, başvuru sahibi, IPC/CPC sınıfları, rüçhan bilgileri, yayın tarihleri, vekil bilgisi, işlem geçmişi.

### Tasarım Araçları

#### **`search_designs`** — Endüstriyel Tasarım Arama
Türkiye'de tescilli endüstriyel tasarımları arar.
* `design_name`: Tasarım adı
* `designer`: Tasarımcı adı
* `applicant`: Başvuru sahibi adı
* `registration_no`: Tasarım tescil numarası
* `locarno_class`: Locarno sınıflandırma kodu (örn. `"06-01"`)
* `attorney`: Tasarım vekili adı
* `limit`: Sayfa başına sonuç sayısı (varsayılan: 20, maks: 100)
* `offset`: Sayfalama ofseti

#### **`get_design_details`** — Tasarım Detayı
Belirli bir tasarım başvurusunun detaylı bilgilerini getirir.
* `file_id`: Tasarım dosya ID'si (`search_designs` sonuçlarından alınır)

**Dönen bilgiler:** Tasarım adı, tasarımcı, başvuru sahibi, Locarno sınıfı, tescil detayları, bülten tarihleri, işlem geçmişi.

---
📜 **Lisans**

Bu proje MIT Lisansı altında lisanslanmıştır.
