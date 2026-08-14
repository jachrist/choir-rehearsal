# Implementeringsplan: OMR-pipeline for kornoter

Dette dokumentet er en vurdering og en fasedelt implementeringsplan for pipelinen
skissert i [`omr-kor-prosjekt-brief.md`](./omr-kor-prosjekt-brief.md): fra PDF-noter
til korrekt MusicXML (med riktig plassert sangtekst), klar for MuseScore/Cantamus.

Status: **Fase 0 – fundament er satt opp.** Ingen gjenkjenningskode er skrevet ennå.

## Avklarte forutsetninger

Disse svarene fra dirigenten styrer arkitekturen konkret:

1. **Besetning:** SATB med klaver. Stemmene kan være delt i 1./2. stemme, så det kan
   være **opptil 8 korstemmer**. Ekstra utfordring: notene noterer ofte
   **damestemmer på én notelinje og herrestemmer på én** (lukket partitur / divisi
   på delt stav). Dette er en kjent hard sak for OMR og krever eksplisitt testing.
2. **Volum:** Kun **enkeltstykker** (ikke hele sangbøker). → LLM-kostnad per side er
   ikke en flaskehals; vi kan tillate oss dyrere/tregere behandling per side.
3. **Brukere:** **Kun dirigenten selv** i første omgang. → UI kan være et lokalt
   verktøy; ingen flerbruker, autentisering eller hosting nå.
4. **PDF-kilder:** To typer. **(a) Innkjøpte** PDF-er som kan ha eget tekstlag, og
   **(b) skannede** papirkopier som er rene bilder. → Pipelinen må forgrene seg tidlig
   basert på om siden har et brukbart tekstlag.

### Konsekvenser for design

- **Tekstlag-forgrening (pkt. 4):** For innkjøpte PDF-er med ekte tekstlag kan
  sangteksten trekkes ut med eksakt posisjon rett fra PDF-en (via PyMuPDF) – helt
  uten OCR og uten gjenkjenningsfeil. For skannede sider må vi bruke OCR/vision.
  Dette er en stor forenkling for en del av materialet og bygges inn fra start
  (`pdf/textlayer.py`).
- **Divisi/lukket partitur (pkt. 1):** Både OMR-steget (homr) og sangtekst-koblingen
  må håndtere at én notelinje kan inneholde to stemmer (voice 1/2) og at en
  stavelse kan gjelde flere noter. Dette får dedikerte testtilfeller allerede i
  Fase 1 og Fase 3.
- **Enbruker + enkeltstykker (pkt. 2–3):** Vi optimaliserer for korrekthet og et
  effektivt rettegrensesnitt, ikke for skala. Ingen kø, database eller
  batch-arkitektur nødvendig i første versjon.

## Vurdering av byggeklossene

| Komponent | Verktøy | Risiko | Kommentar |
|-----------|---------|--------|-----------|
| PDF → bilde | PyMuPDF | Lav | Godt etablert. Rendrer i 300 dpi. |
| Tekstlag-uttrekk | PyMuPDF | Lav | Gratis eksakt sangtekst for innkjøpte PDF-er. |
| OMR | homr | **Middels** | Beste åpne valg, SATB-kapabel, CPU-ok. Må kvalitetsvalideres på ekte kornoter (Fase 1). Håndterer ikke sangtekst/dynamikk. |
| Sidesammenslåing | relieur | **Høy** | Trolig ikke bygget for repetisjoner/voltaer. Regn med patching eller egen rutine. |
| Sangtekst | *bygges selv* | **Høyest** | Ingen ferdig løsning. Hybrid OCR + vision anbefales. Divisi kompliserer. |
| Rette-UI | Verovio/OSMD + eget lag | Middels | **Ikke tegn noter selv** – bruk Verovio/OSMD for gjengivelse. |
| Eksport | MusicXML → MuseScore/Cantamus | Lav | MusicXML som gjennomgående kontrakt; valider mot XSD på hver overgang. |

### Nøkkelanbefalinger

1. **Sjekk tekstlaget først.** For innkjøpte PDF-er kan hele OCR-problemet forsvinne.
2. **Ikke bygg notegjengivelse selv.** Verovio (MIT) gjengir MusicXML i nettleser;
   rette-UI blir da et redigeringslag oppå ferdige noter i stedet for en egen
   noteeditor. Trolig den enkeltbeslutningen som sparer mest tid.
3. **Hybrid sangtekst-kobling.** OCR/tekstlag gir bounding-box per stavelse
   (deterministisk); vision-modell (Claude) gjør den vanskelige koblingen
   stavelse→note og håndterer bindestrek/elisjon. Bruk vision til å lage
   fasit-korpus uansett produksjonsvei.
4. **Beslutningsporter mellom faser.** Særlig Fase 1: hvis homr ikke holder på
   deres materiale, vil dere vite det etter noen dager – ikke måneder.

## Teknologistack

- **Pipeline:** Python 3.11+ (matcher homr, relieur, PyMuPDF).
- **MusicXML:** lxml for parsing/validering.
- **Backend for UI (senere):** FastAPI.
- **Frontend for UI (senere):** Verovio/OSMD + tynt JS-redigeringslag.
- **Test:** pytest + XSD-validering + golden-file-korpus.
- **Lint/format:** ruff.

Tunge avhengigheter (homr, torch) installeres først i Fase 1 og holdes utenfor
kjerneinstallasjonen slik at grunnoppsettet og testene er raske.

## Faseplan

| Fase | Mål | Beslutningsport |
|------|-----|-----------------|
| **0. Fundament** ✅ | Repo-struktur, Python-miljø, pytest, SessionStart-hook, testdata-mappe | – |
| **1. Valider homr** | Skript: 1 PDF-side → bilde → homr → rå MusicXML. Mål kvalitet manuelt på ekte kornoter, inkl. divisi | Tonehøyde/rytme er «godt nok til å rette», ikke «må gjøres på nytt» |
| **2. Flersidig sammenslåing** | Integrer/erstatt relieur. Test repetisjoner + 1./2. volta + opptakt over sidebytte | Takter sammenhengende over sidebytter |
| **3. Tekstlag** | Tekstlag-forgrening (innkjøpt vs. skannet). OCR+vision-hybrid. Bygg fasit-korpus, mål nøyaktighet, håndter divisi | Stavelse-note-treff høyt nok til at retting < å skrive på nytt |
| **4. Rette-UI** | Verovio/OSMD + redigeringslag: last inn → rett → eksporter | Full runde PDF → rettet MusicXML fungerer |
| **5. Sluttflyt** | Eksport klar for MuseScore → Cantamus | – |

## Teststrategi (bygges opp fase for fase)

Sangtekst-plassering og sidesammenslåing er de mest feilutsatte stegene og skal ha
strengest testdekning.

- **Fasit-korpus:** noen få ekte korsider med håndverifisert forventet MusicXML og
  stavelse-note-kobling. Dette er det høyest verdsatte aktivumet – nesten alle
  tester avhenger av det. Legges i `testdata/` (store binærfiler holdes små/få).
- **MusicXML-validering:** velformethet + strukturell/XSD-sjekk på hver
  faseovergang.
- **Golden-file-tester:** fast inn-side → innsjekket forventet `.musicxml`,
  sammenlignet strukturelt (ikke byte-for-byte).
- **Divisi-tester:** eksplisitte tilfeller med to stemmer på én stav og delt
  dame/herre-notasjon.
- **Rask vs. treg:** unit-tester (ingen tunge modeller) kjører på hver push;
  homr/vision-tunge tester merkes og kjøres sjeldnere.

## Neste steg

- **Fase 1:** kjørbart skript `pdf → bilde → homr → rå MusicXML`, så gjenkjennings-
  kvaliteten på ekte kornoter kan måles. Legg 1–2 ekte enkeltstykker i `testdata/`.

## Åpne punkter for senere

- Nøyaktig strategi for divisi-oppsplitting i MusicXML (`<voice>`-håndtering).
- Om relieur patches eller erstattes helt.
- Valg mellom ren OCR-vei og LLM-vei for sangtekst i produksjon (etter måling i Fase 3).
