/*
 * ==============================================================================
 * Sistema FIND — Firmware ESP32 + PN532 (NFC/RFID)
 * ==============================================================================
 *
 *  HARDWARE:
 *    LED Verde    → GPIO 2
 *    LED Vermelho → GPIO 4
 *    PN532 SDA    → GPIO 21
 *    PN532 SCL    → GPIO 22
 *
 *  COMPORTAMENTO DOS LEDS (NOVO):
 *    Repouso (sem tag)      → LEDs APAGADOS
 *    Tag detectada          → "Jogo de luzes": chase/alternância acelerando
 *                              enquanto consulta o servidor
 *    Tag cadastrada         → Verde fixo 2s ✅ (depois apaga)
 *    Tag NÃO cadastrada     → Vermelho fixo 2s ❌ (depois apaga)
 *    Erro de autenticação/HTTP → Vermelho pisca (⚠️) (depois apaga)
 *    PN532 não encontrado   → Vermelho pisca rápido para sempre (erro de hardware)
 *
 *  CONFIGURAÇÕES PARA MUDAR:
 *    ssid, password → rede Wi-Fi
 *    token          → token do dispositivo cadastrado no painel IoT do Find
 * ==============================================================================
 */
#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_PN532.h>
#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <HTTPClient.h>

// ── Wi-Fi ─────────────────────────────────────────────────────────────────────
const char* ssid     = "Internet-G2";
const char* password = "20022013";

// ── API do Projeto FIND no Render ─────────────────────────────────────────────
const char* apiUrl = "https://projeto-find.onrender.com/api/iot/scan/";
const char* token  = "IFpDKNOyTYDmVi0gZbY5z3NVIleYLTkZIoquBZgqc6NeR0a9";

// ── Pinos ─────────────────────────────────────────────────────────────────────
#define SDA_PIN      21
#define SCL_PIN      22
#define LED_VERDE    2
#define LED_VERMELHO 4

Adafruit_PN532 nfc(SDA_PIN, SCL_PIN);

// ── Utilitário: apaga os dois LEDs (estado de repouso) ────────────────────────
void ledsApagados() {
  digitalWrite(LED_VERDE,    LOW);
  digitalWrite(LED_VERMELHO, LOW);
}

// ── "Jogo de luzes": efeito de chase/alternância enquanto processa a tag ──────
// Alterna Verde/Vermelho, acelerando a cada passo, dando a sensação de
// "sorteio" que vai até a luz final quando o resultado chega.
void animacaoProcessando() {
  int atrasos[] = {160, 160, 130, 130, 100, 100, 75, 75, 55, 55, 40, 40, 30, 30};
  int total = sizeof(atrasos) / sizeof(atrasos[0]);
  for (int i = 0; i < total; i++) {
    digitalWrite(LED_VERDE,    i % 2 == 0);
    digitalWrite(LED_VERMELHO, i % 2 != 0);
    delay(atrasos[i]);
  }
  ledsApagados();
}

// ── Pisca de erro (⚠️) e volta ao repouso ─────────────────────────────────────
void piscaErro() {
  for (int i = 0; i < 4; i++) {
    digitalWrite(LED_VERMELHO, LOW);  delay(120);
    digitalWrite(LED_VERMELHO, HIGH); delay(120);
  }
  ledsApagados();
}

// ── Envia UID para o servidor ─────────────────────────────────────────────────
void enviarTagParaWeb(String uidHex) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("[ERRO] Wi-Fi desconectado!");
    piscaErro();
    return;
  }

  WiFiClientSecure *client = new WiFiClientSecure;
  if (client) {
    client->setInsecure(); // Ignora a verificação do certificado SSL para facilitar a conexão

    HTTPClient http;
    http.begin(*client, apiUrl);
    http.addHeader("Content-Type", "application/json");
    http.addHeader("Authorization", "Hardware-Token " + String(token));

    String payload = "{\"rfid_uid\":\"" + uidHex + "\"}";
    Serial.println("[HTTP] POST → " + payload);

    int code = http.POST(payload);

    if (code > 0) {
      String body = http.getString();
      Serial.printf("[HTTP] Resposta %d: %s\n", code, body.c_str());

      if (code == 200 || code == 201) {
        // ✅ Tag cadastrada e identificada → Verde
        digitalWrite(LED_VERMELHO, LOW);
        digitalWrite(LED_VERDE, HIGH);
        delay(2000);
        ledsApagados();
      } else if (code == 404) {
        // ❌ Tag lida mas sem item cadastrado → Vermelho fixo
        Serial.println("[INFO] Tag nao cadastrada. Veja o painel IoT para registrar.");
        digitalWrite(LED_VERDE, LOW);
        digitalWrite(LED_VERMELHO, HIGH);
        delay(2000);
        ledsApagados();
      } else {
        // ⚠️ Outro erro (403 token ruim, 400 payload, 500 servidor) → Vermelho pisca
        Serial.printf("[ERRO] Codigo inesperado: %d\n", code);
        http.end();
        delete client;
        piscaErro();
        return;
      }
    } else {
      Serial.printf("[ERRO] Falha HTTP: %s\n", http.errorToString(code).c_str());
        http.end();
        delete client;
        piscaErro();
        return;
    }

    http.end();
    delete client;
  } else {
    Serial.println("[ERRO] Nao foi possivel criar o cliente seguro.");
    piscaErro();
  }
}

// ── Setup ─────────────────────────────────────────────────────────────────────
void setup() {
  Serial.begin(115200);
  delay(1000);

  pinMode(LED_VERDE,    OUTPUT);
  pinMode(LED_VERMELHO, OUTPUT);
  ledsApagados(); // repouso: apagado desde o início

  // Conecta ao Wi-Fi
  Serial.printf("\n[WIFI] Conectando a: %s\n", ssid);
  WiFi.begin(ssid, password);
  int t = 0;
  while (WiFi.status() != WL_CONNECTED && t < 30) {
    delay(500);
    Serial.print(".");
    t++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n[WIFI] Conectado! IP: " + WiFi.localIP().toString());
  } else {
    Serial.println("\n[WIFI] Falhou. Rodando sem Wi-Fi...");
  }

  // Inicia PN532
  Wire.begin(SDA_PIN, SCL_PIN);
  nfc.begin();
  uint32_t versao = nfc.getFirmwareVersion();

  if (!versao) {
    Serial.println("[ERRO] PN532 nao encontrado! Verifique a fiacao I2C.");
    // Pisca rápido para sempre — erro de hardware
    while (true) {
      digitalWrite(LED_VERMELHO, !digitalRead(LED_VERMELHO));
      delay(100);
    }
  }

  Serial.printf("[NFC] PN532 OK — Firmware v%d.%d\n",
                (versao >> 16) & 0xFF,
                (versao >>  8) & 0xFF);

  nfc.SAMConfig();
  Serial.println("\n=== Sistema FIND Pronto. Aguardando Tags... ===\n");
}

// ── Loop ──────────────────────────────────────────────────────────────────────
void loop() {
  // Repouso: LEDs apagados (só acordam quando uma tag é detectada)
  ledsApagados();

  uint8_t uid[7]    = {0};
  uint8_t uidLength = 0;
  bool leu = nfc.readPassiveTargetID(PN532_MIFARE_ISO14443A, uid, &uidLength, 300);

  if (leu) {
    // Monta o UID em formato HEX maiúsculo (ex: "04EAB122")
    String uidHex = "";
    for (uint8_t i = 0; i < uidLength; i++) {
      if (uid[i] < 0x10) uidHex += "0";
      uidHex += String(uid[i], HEX);
    }
    uidHex.toUpperCase();
    Serial.println(">>> Tag detectada: " + uidHex);

    animacaoProcessando();     // 🎇 jogo de luzes enquanto consulta o servidor
    enviarTagParaWeb(uidHex);  // resultado final: verde, vermelho ou erro

    delay(1500); // Debounce: evita ler a mesma tag múltiplas vezes
  }
}
