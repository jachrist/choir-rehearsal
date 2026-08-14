# Testdata

Her legges **fasit-korpuset**: noen få ekte korsider med håndverifisert forventet
utdata. Dette er prosjektets høyest verdsatte testaktivum – nesten alle tester i
Fase 1–4 avhenger av det.

Foreslått innhold etter hvert:

- `pdf/` – ekte enkeltstykker (SATB med klaver, gjerne ett med divisi/lukket partitur,
  ett innkjøpt med tekstlag og ett skannet uten).
- `expected/` – håndverifisert forventet MusicXML per side (golden files).
- `lyrics/` – forventet stavelse-til-note-kobling for sangtekst-testene.

Hold binærfilene små og få. Store/mange noter bør ev. håndteres utenfor git.

> Grunntestene (`tests/`) genererer i dag sine egne små PDF-er i minnet, så de
> kjører uten innsjekkede filer. Fasit-korpuset kommer inn i Fase 1.
