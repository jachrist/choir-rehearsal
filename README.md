# choir-rehearsal

Prosjektet skal planlegge, utvikle og teste programvare for å produsere øvefilene
for et kor: en OMR-pipeline fra PDF-noter til korrekt MusicXML (med riktig plassert
sangtekst), klar for MuseScore/Cantamus.

Se [`omr-kor-prosjekt-brief.md`](./omr-kor-prosjekt-brief.md) for bakgrunn og
[`implementeringsplan.md`](./implementeringsplan.md) for vurdering og faseplan.

## Status

| Fase | Hva | Status |
|------|-----|--------|
| 1 | PDF → bilde → homr → rå MusicXML | ✅ validert på ekte kornoter |
| 2 | Slå sammen sider til ett partitur | ✅ |
| 3 | Sangtekst: hent fra tekstlag, del i stavelser, plasser | ✅ kjerne (82–94 % mot fasit) |
| 4 | Lokalt web-verktøy for sangtekstretting | ✅ |
| 5 | Sluttflyt: én kommando PDF → ferdig MusicXML | 🔜 planlagt |

## Oppsett

```bash
python3 -m pip install -e ".[dev]"      # kjerne + testverktøy (lett, ingen tunge libs)
```

Ekstra avhengigheter installeres per behov:

```bash
# Fase 1 – OMR-motoren homr (tung: torch m.m.)
python3 -m pip install -e ".[omr]"
# Debian-miljøer: sett SETUPTOOLS_USE_DISTUTILS=stdlib hvis antlr4 feiler å bygge.
homr --init                              # last ned modellene (engangs)

# Fase 4 – web-verktøyet (fastapi + uvicorn + verovio)
python3 -m pip install -e ".[ui]"
```

## Bruk

### Fase 1 – PDF → rå MusicXML

```bash
choir-omr fase1 noter.pdf --out-dir output/ --dpi 300   # valgfritt: --pages 0,1
```

Skriver én `.musicxml` per side og en kvalitetsrapport: velformet utdata, antall
takter/stemmer/noter, og flagg for tomme sider og divisi. Grunnlaget for å vurdere
om homr er «godt nok til å rette».

### Fase 2 – slå sammen sider

```bash
choir-omr fase2 output/noter/ --out output/noter_merged.musicxml
```

Slår sammen per-side MusicXML til ett sammenhengende partitur (løpende takter).
Sider med avvikende stemmestruktur grupperes og rapporteres framfor å slås sammen
blindt.

### Fase 3 – sangtekst (bibliotek)

Sangtekst hentes fra PDF-tekstlaget (for innkjøpte, digitale PDF-er), renses for
musikkglyffer/ligaturer/melisme, deles i stavelser og plasseres på notene med
melisme-håndtering (legatobuer). Se `choir_rehearsal.lyrics`. Nøyaktigheten måles
mot en manuelt rettet fasit med `pytest -m slow`.

### Fase 4 – rette sangteksten (web)

Hybrid arbeidsflyt: **noter/struktur rettes i MuseScore, sangteksten i dette
verktøyet.** Det rører kun `<lyric>`; resten av partituret bevares.

```bash
choir-omr ui "partitur.musicxml"         # åpne http://127.0.0.1:8000
```

Panel per stemme med «forskyv ±1 note» (fikser at teksten ligger én note feil),
tøm og fri tekstredigering, og live Verovio-gjengivelse. Alt kjører lokalt.

## Tester

```bash
pytest                # raske tester (mocker homr; ingen torch)
pytest -m slow        # ekte ende-til-ende (homr / golden-file mot rettet MusicXML)
ruff check .          # lint
```

De trege testene hoppes over hvis de nødvendige (opphavsrettsbeskyttede) filene
ikke ligger lokalt.

## Prosjektstruktur

```
src/choir_rehearsal/
  cli.py       kommandolinje: fase1 / fase2 / ui
  config.py    konstanter (dpi, terskler)
  pdf/         PDF → bilde + tekstlag-deteksjon (Fase 1 og 3)
  omr/         homr-wrapper: bilde → rå MusicXML (Fase 1)
  merge/       slå sammen sider til ett partitur (Fase 2)
  lyrics/      sangtekst: rens, stavelser, plassering, evaluering (Fase 3)
  musicxml/    validering og hjelpefunksjoner (alle faser)
  pipeline/    orkestrering per fase (phase1, phase2)
  ui/          web-verktøy for sangtekstretting (Fase 4)
  export/      eksport for MuseScore/Cantamus (Fase 5)
```

## Merk om opphavsrett

Kornoter (PDF/MusicXML) er ofte opphavsrettsbeskyttet og skal ikke committes –
`*.pdf`, `*.musicxml` og `*.mxl` er i `.gitignore`. Last dem opp lokalt kun ved
testing.
