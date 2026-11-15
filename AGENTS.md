# AGENTS.md — werkwijze voor elke AI in deze repo (ChatGPT, Codex, Claude)

1. **Lees eerst `OUTCOME.md`.** Dat is het doel en de definitie van klaar. Bekijk daarna het actuele resultaat (laatste run, laatste output).
2. **Draai en kijk.** Geen wijziging zonder dat je het resultaat hebt gedraaid en bekeken. De acceptatietoets moet slagen.
3. **Kleinste stap naar het doel.** Verwijderen en vervangen hebben de voorkeur boven toevoegen. Herbouwen mag als het goedkoper is dan repareren; zeg dan waarom.
4. **Productkeuzes en alles onder "Alleen met akkoord van de eigenaar"** in `OUTCOME.md`: stel de eigenaar een korte vraag met opties. Al het andere beslis je zelf.
5. **Controles alleen op de uitkomst.** Elke controle noemt de concrete fout die ze voorkomt. Geen gesimuleerde rollen, certificeringsstappen, poorten op het proces of bewijsbestanden als doel.
6. **Documentatie:** alleen `OUTCOME.md` (incl. één regel per besluit), `AGENTS.md`, `README.md` en hooguit twee technische READMEs. Geen plan-, status- of controledocumenten. Werk in uitvoering leeft in een PR.
7. **Twee keer vast op hetzelfde?** Stop, vereenvoudig of vraag. Voeg geen bewaker toe.
8. **Eerlijk rapporteren:** zeg wat kapot is. Onderscheid gedraaid / gecontroleerd / aangenomen. Nooit succes melden zonder bewijs uit de run zelf.
9. **Geen nieuwe besturingslagen** (wachtrijen, autorisaties, holders, missiecontracten). Het project en zijn acceptatietoets zijn genoeg.

---

## Projectspecifieke regels (eerdere versie)

Deze regels blijven gelden voor zover ze over het product gaan (data, privacy, correctheid). Bij strijd gaan de regels 1–9 hierboven en `OUTCOME.md` voor. Leesvolgordes en procesregels hieronder worden in ronde B opgeschoond.

# AGENTS.md

## CACHE-FIRST CONTROL — MANDATORY

Before starting **any** strategy test, market-data audit, FX research programme, cross-pair study, or Dukascopy acquisition in this repository:

1. Read `REPOSITORY_CONTROL.md`.
2. Read `docs/PERMANENT_MARKET_DATA_CACHE.md`.
3. Read `data/private_market_data_cache_registry.json`.
4. Search the canonical private Google Drive cache first.
5. Verify the registered SHA-256 values and reuse the qualified cached data.
6. For the ten-pair cash-FX dataset, read `research_registry/DUKASCOPY_FX_CASH_RESEARCH_STANDARD.md` and search `research_registry/dukascopy_fx_cash/INDEX.md` before defining a new hypothesis.

Canonical dataset folder:

- `FX_M1_BID_ASK_2015_2025_PLUS_2026YTD`
- Drive folder ID: `160qGdjm9Gi6pr05nRHuUXaTZc9EgJOOU`
- Ten pairs: EURUSD, GBPUSD, USDCHF, AUDUSD, NZDUSD, USDCAD, USDJPY, EURJPY, GBPJPY, EURGBP
- Coverage: complete 2015–2025 plus 2026 YTD ending exclusive 2026-07-24
- Format: Dukascopy M1, separate BID and ASK, UTC, qualified and checksummed

**Never reacquire full historic data that is already registered.**

A download is allowed only for a proven missing/corrupt partition, a materially different data construction, or an explicitly requested incremental extension. Record the exception in the work package, changelog, and registry before acquisition. Upload and verify the permanent copy before deleting temporary files.

Raw market data must never be committed to the public repository.

The canonical research name for the ten-pair source is **Dukascopy FX Cash**. A Dukascopy FX Cash study is not durably complete until its methodology and result are registered in `research_registry/dukascopy_fx_cash/` and the registry validator passes.

## Research operating rules

- Treat `REPOSITORY_CONTROL.md` as the repository-wide authority.
- Treat strategy-specific status files as subordinate to repository-wide data controls.
- Preserve holdout boundaries and preregistration.
- Separate discovery, validation, holdout and monitoring periods.
- Preserve negative results and do not rescue failed hypotheses through retrospective variants.
- Verify dataset checksums before performance execution.
- Do not generalize a pair-specific result without cross-pair evidence.
- Do not release Pine, alerts, sizing or deployment guidance before the relevant scientific and operational gates pass.
- Every Dukascopy FX Cash study must preserve its exact source commit, data windows, holdout state, null/placebo design, scientific disposition and negative findings in the central research registry.
