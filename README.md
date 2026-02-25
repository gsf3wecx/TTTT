# Simulatore clima + biomi da heightmap

Programma iniziale (semplice ma estendibile) che, data una **heightmap** normalizzata `[0..1]`, calcola:

- temperatura
- umidità
- biome risultante per ogni cella

## Esecuzione rapida

```bash
python3 climate_biome_sim.py --out-prefix output/demo
```

Senza input genera una heightmap casuale smussata.

## Input personalizzato

Puoi passare un CSV (rettangolare) con valori tra `0` e `1`:

```bash
python3 climate_biome_sim.py data/mia_heightmap.csv --out-prefix output/mondo1
```

## File output

Con prefisso `output/mondo1` otterrai:

- `output/mondo1_heightmap.csv`
- `output/mondo1_temperature.csv`
- `output/mondo1_moisture.csv`
- `output/mondo1_biome.csv`

## Modello climatico (versione 0)

- **Temperatura** = gradiente latitudinale - penalità altitudine.
- **Umidità** = venti prevalenti Ovest→Est, evaporazione dal mare, effetto rain shadow dietro montagne.
- **Bioma** = classificazione a soglia usando altitudine, temperatura e umidità.

## Idee per i prossimi step

- supporto immagini heightmap (`.png`, `.tif`)
- stagionalità e venti dinamici
- correnti oceaniche
- erosione e fiumi
- visualizzazione grafica (matplotlib / web)
