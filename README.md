# Vegetariska Soppor

**Från nybörjare till mästerliga smaker i vardagsköket**

Författare: Erland Lindmark

Detta är ett standardiserat bokprojekt för en svensk praktisk lärobok/kokbok om vegetariska soppor för nybörjare som vill utvecklas mot mästerlig smakförståelse.

## Projektstruktur

- `chapters/` innehåller manus.
- `docs/` innehåller bokspecifikation, kapitelplan, status och metadata.
- `assets/cover/` är reserverad för omslagsbild.
- `assets/image-prompts/` innehåller prompt för omslag.
- `scripts/` och `styles/` innehåller lokal exportpipeline.
- `exports/` är målplats för skapade EPUB/PDF-filer.

## Rekommenderat arbetsflöde

1. Skriv eller uppdatera ett kapitel i taget.
2. Uppdatera `docs/projektstatus.md`.
3. Kontrollera `docs/terminologi.md` och `docs/pedagogisk-canon.md`.
4. Exportera lokalt med `scripts/export-book.sh` när manus är redo.
