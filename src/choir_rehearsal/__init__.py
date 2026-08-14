"""OMR-pipeline for kornoter: fra PDF til korrekt MusicXML.

Pakken er organisert etter fasene i implementeringsplanen:

- ``pdf``       – PDF → bilde og tekstlag-deteksjon (Fase 1 og 3)
- ``omr``       – homr-wrapper: bilde → rå MusicXML (Fase 1)
- ``merge``     – slå sammen sider til ett partitur (Fase 2)
- ``lyrics``    – sangtekst-gjenkjenning og -plassering (Fase 3)
- ``musicxml``  – validering og hjelpefunksjoner for MusicXML (alle faser)
- ``ui``        – rette-grensesnitt (Fase 4)
- ``export``    – eksport klar for MuseScore/Cantamus (Fase 5)
"""

__version__ = "0.0.1"
