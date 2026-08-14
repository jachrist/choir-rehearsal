# Prosjektbrief: Skreddersydd OMR-pipeline for kornoter

## Bakgrunn og mål

Jeg dirigerer/administrerer et kor og har i dag en tung manuell prosess for å gå fra
PDF-noter til ferdige øvingsfiler:

1. Skanner/importerer PDF med et kommersielt OMR-produkt (optisk notegjenkjenning)
2. Programmet er dårlig på tekstgjenkjenning (sangtekst), som krever mye manuell retting
3. Retter og redigerer i MuseScore
4. Eksporterer som MusicXML
5. Laster inn i **Cantamus**, som produserer gode lydfiler per stemme med sunget tekst

Cantamus-steget fungerer godt og skal beholdes som det er (ingen kjent API, men det er
ikke noe problem – dette gjøres manuelt som i dag).

**Målet med dette prosjektet** er å bygge en bedre, mer skreddersydd og åpen
erstatning for steg 1–4: en pipeline som går fra PDF til korrekt MusicXML
(inkludert riktig plassert sangtekst), med et moderne og effektivt
korrigeringsgrensesnitt, som til slutt eksporteres til MuseScore/Cantamus som i dag.

Konteksten er at eksisterende verktøy (både det kommersielle produktet og det
gratis Audiveris) har svake punkter: dårlig tekstgjenkjenning og/eller et
tungvint, gammeldags brukergrensesnitt.

## Diskuterte byggeklosser

### PDF → sidebilder
- Ren, veletablert teknologi: **PyMuPDF (fitz)** eller **pdf2image/poppler**
- Rendre i høy oppløsning (start med ca. 300 dpi)
- Siden kildematerialet ofte er rene, digitalt eksporterte PDF-er (ikke skannet
  papir), bør bildekvaliteten være vesentlig bedre enn typisk kamera-/skann-input

### Notegjenkjenning (OMR)
- **[homr](https://github.com/liebharc/homr)** (Christian Liebhardt) – vurdert som
  det beste åpne alternativet:
  - Bygget på vision transformers, viderefører/forbedrer oemer
  - Håndterer partiturer med flere stavesystemer per gruppe (relevant for kor: SATB)
  - Kan kjøres uten GPU (går bare tregere – ingen kvalitetsforskjell, bare
    hastighet)
  - **Viktig begrensning:** fokuserer på tonehøyde og rytme, håndterer *ikke*
    sangtekst eller dynamikk/artikulasjon i dag
- Alternativ/referanse: **[oemer](https://github.com/BreezeWhite/oemer)**
  (forgjengeren homr bygger videre på)
- Til sammenligning: **Audiveris** (Java/Swing) er mer moden og velprøvd, men har
  et tungvint grensesnitt og er ikke like moderne i selve motoren

### Sammenslåing av sider til én sammenhengende partitur
- **[relieur](https://github.com/papoteur-mga/relieur)** – lite Python-verktøy
  laget spesifikt for å slå sammen flere MusicXML-filer (én per side) til én
  sammenhengende fil
  - Trenger trolig tilpasning for korpartiturer med repetisjoner, 1./2. voltaer
    osv. – må testes grundig
  - Alternativ referanse: **MusicXML-Merger** (diedeno) – GUI-basert
    sammenslåingsverktøy med litt annen tilnærming (separate stemmer vs.
    sammenhengende takter)

### Sangtekst-gjenkjenning og -plassering (det mest krevende steget)
Ingen ferdig løsning funnet. Dette må bygges fra bunnen. Viktig avgrensning: dette
er et **bilde-til-struktur-problem** (plassere tekst romlig riktig under notene),
ikke et lyd-til-tekst-alignment-problem (som eksisterende "lyrics alignment"-verktøy
løser – de justerer tekst mot innspilt lyd, ikke mot et bilde).

To mulige tilnærminger å utforske:

1. **Tradisjonell pipeline:** OCR med posisjonsdata (bounding box per stavelse) →
   koble til nærmeste note basert på horisontal (x-)posisjon per stavesystem →
   sette inn i riktig `<lyric>`-element i MusicXML, med korrekt håndtering av
   bindestrek-delte stavelser og elisjoner
2. **Vision-modell-tilnærming:** gi en vision-modell (f.eks. Claude) sidebildet
   sammen med noteposisjonene fra homr, og be den returnere
   stavelse-til-note-kobling direkte – kan vise seg enklere og mer robust enn
   en tradisjonell OCR+matching-pipeline, spesielt for norsk/flerspråklig tekst
   med spesialtegn

Inspirasjon: en fork av Audiveris kalt **ScanScore (Rockman6)** har lagt til
RapidOCR (ONNX-basert, bedre flerspråklig støtte enn Tesseract) og til og med
en lokal LLM (Ollama) for instrumentgjenkjenning fra OCR-tekst. Koden deres
(`app/src/main/java/org/audiveris/omr/text/`) kan være verdt å se på for
inspirasjon til strukturen, selv om den er Java-basert og fortsatt bruker det
gamle Audiveris-grensesnittet.

### Korrigeringsgrensesnitt
Et sentralt mål er et **moderne, effektivt** grensesnitt for manuell korrigering
etter automatisk gjenkjenning – i sterk kontrast til Audiveris' gammeldagse
Swing-UI. Trolig mest praktisk som en enkel webapplikasjon.

## Foreslått faseinndeling

1. **Fase 1 – valider kjernemotoren:** Skript som kjører homr på en enkelt
   PDF-side (via PDF→bilde-konvertering) og gir rå MusicXML. Vurder
   gjenkjenningskvaliteten på faktiske kornoter før mer tid investeres.
2. **Fase 2 – flersidig sammenslåing:** Integrer/tilpass relieur for å slå sammen
   flere sider til én sammenhengende fil. Test med repetisjoner og voltaer.
3. **Fase 3 – tekstlag:** Bygg og test sangtekst-gjenkjenning og
   note-kobling (prøv gjerne begge tilnærmingene over og sammenlign).
4. **Fase 4 – korrigeringsgrensesnitt:** Bygg et enkelt webbasert UI for manuell
   gjennomgang og retting før eksport.
5. **Fase 5 – sluttbrukerflyt:** Eksporter ferdig MusicXML klar for MuseScore
   (for evt. siste finpuss) og videre inn i Cantamus som i dag.

## Åpne spørsmål å avklare underveis

- Hvor mange stemmer/stavesystemer er typisk i partiturene (SATB, med/uten
  klaverledsagelse)?
- Hvor stort er typisk volum – enkeltstykker eller hele sangbøker/programmer?
- Skal verktøyet kun brukes av meg, eller også av andre i koret/andre kor?
- GPU er ikke nødvendig, men vil gi raskere behandling – vurder om det er
  aktuelt for produksjonsbruk ved høyere volum.

## Referanser (åpen kildekode)

- homr: https://github.com/liebharc/homr
- oemer: https://github.com/BreezeWhite/oemer
- relieur: https://github.com/papoteur-mga/relieur
- MusicXML-Merger: https://github.com/diedeno/MusicXML-Merger
- ScanScore (Audiveris-fork med moderne OCR): https://github.com/Rockman6/ScanScore
- Audiveris (referanse/sammenligning): https://github.com/Audiveris/audiveris
