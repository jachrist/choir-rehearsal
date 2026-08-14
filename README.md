# choir-rehearsal

Prosjektet skal planlegge, utvikle og teste programvare for å produsere øvefilene
for et kor: en OMR-pipeline fra PDF-noter til korrekt MusicXML (med riktig plassert
sangtekst), klar for MuseScore/Cantamus.

Se [`omr-kor-prosjekt-brief.md`](./omr-kor-prosjekt-brief.md) for bakgrunn og
[`implementeringsplan.md`](./implementeringsplan.md) for vurdering og faseplan.

## Oppsett

```bash
python3 -m pip install -e ".[dev]"      # kjerne + testverktøy
```

OMR-motoren homr (Fase 1) er tung (torch m.m.) og installeres separat:

```bash
python3 -m pip install -e ".[omr]"
# Debian-miljøer: sett SETUPTOOLS_USE_DISTUTILS=stdlib hvis antlr4 feiler å bygge.
homr --init                              # last ned modellene (engangs)
```

## Fase 1: PDF → rå MusicXML

Kjør homr på en PDF og få en kvalitetsrapport per side:

```bash
choir-omr fase1 noter.pdf --out-dir output/ --dpi 300
# valgfritt: --pages 0,1  for bare enkelte sider
```

Rapporten viser per side om utdata er velformet, antall takter/stemmer/noter, og
flagger tomme sider (homr traff neppe) og divisi (flere stemmer enn stavesystemer).
Dette er grunnlaget for å vurdere om homr er «godt nok til å rette» før mer bygges.

## Tester

```bash
pytest                # raske tester (mocker homr; krever ikke torch)
pytest -m slow        # ekte ende-til-ende mot homr + PDF-er i testdata/pdf/
```

## Prosjektstruktur

```
src/choir_rehearsal/
  pdf/        PDF → bilde + tekstlag-deteksjon (Fase 1 og 3)
  omr/        homr-wrapper: bilde → rå MusicXML (Fase 1)
  merge/      slå sammen sider til ett partitur (Fase 2)
  lyrics/     sangtekst-gjenkjenning og -plassering (Fase 3)
  musicxml/   validering og hjelpefunksjoner (alle faser)
  pipeline/   orkestrering per fase
  ui/         rette-grensesnitt (Fase 4)
  export/     eksport for MuseScore/Cantamus (Fase 5)
```
