# SYSAV Nästa Tömning (inofficiell)

Hämtar nästa tömningsdatum för Kärl 1 och Kärl 2 från SYSAV:s "Min sophämtning" (Kävlinge, Lomma, Svedala).

> **Viktigt:** SYSAV exponerar ingen dokumenterad publik API och byter ibland bas-URL. Den här integreringen har\
> 1) auto-detektering av API-bas via kommun-sidan, 2) manuell override (Options) om det behövs.

## Installation (HACS)
1. Lägg till detta repo som **Custom repository** i HACS (Integrationer).
2. Installera **SYSAV Nästa Tömning**.
3. Gå till **Inställningar → Enheter & tjänster → Lägg till integration** och sök på "SYSAV".

## Konfiguration
- **Kommun**: `kavlinge`, `lomma`, `svedala`
- **Gata/Nummer/Ort**: exakt som på SYSAV:s söksida.
- **API-bas (valfritt)**: lämna tomt för auto. Om auto misslyckas, öppna kommun-sidan, gör en sökning och kopiera bas-URL för nätverksanropet som sker (brukar sluta på `/api`).

## Sensorer
Skapar två sensorer:
- `sensor.karl_1_nasta_tomning`
- `sensor.karl_2_nasta_tomning`

Datumet är `YYYY-MM-DD`. Attribut innehåller ursprunglig etikett.

## Felsökning
- Aktivera debug:
```yaml
logger:
  default: warning
  logs:
    custom_components.sysav_next: debug
