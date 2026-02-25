# Simulatore clima + biomi da heightmap

Programma iniziale (semplice ma estendibile) che, data una **heightmap** normalizzata `[0..1]`, calcola:

- temperatura
- umidità
- biome risultante per ogni cella

## Formati input supportati

- **CSV** rettangolare con valori numerici tra `0` e `1`
- **PNG / JPG / JPEG** (convertiti in scala di grigi; `0`=nero=quota bassa, `255`=bianco=quota alta)

> Per PNG/JPG e per l'export PNG è richiesta la libreria **Pillow**:
>
> ```bash
> pip install pillow
> ```

<<<<<<< codex/create-climate-and-biome-simulation-program-bthtwi
## Livello del mare (fix principale)

Per le **immagini** ora il livello del mare viene stimato **automaticamente** se non passi `--sea-level`.
La stima usa un quantile (`--sea-level-quantile`, default `0.72`) per evitare il problema tipico di mappe con terre troppo sottili.

- `--sea-level 0.40` → forza soglia assoluta (comportamento manuale)
- `--sea-level-quantile 0.72` → auto-stima su immagini (circa 72% oceano)

=======
>>>>>>> main
## Esecuzione rapida

```bash
python3 climate_biome_sim.py --out-prefix output/demo
```

Senza input genera una heightmap casuale smussata.

<<<<<<< codex/create-climate-and-biome-simulation-program-bthtwi
## Input immagine (consigliato)

```bash
python3 climate_biome_sim.py data/mia_heightmap.jpg --out-prefix output/mondo1 --export-png
```

Per aumentare/diminuire il mare in auto:

```bash
python3 climate_biome_sim.py data/mia_heightmap.jpg --out-prefix output/mondo1 --sea-level-quantile 0.68 --export-png
```

## Output PNG

Con `--export-png` vengono salvati:
=======
## Input CSV personalizzato

```bash
python3 climate_biome_sim.py data/mia_heightmap.csv --out-prefix output/mondo_csv
```

## Input immagine personalizzato

```bash
python3 climate_biome_sim.py data/mia_heightmap.png --out-prefix output/mondo_img
```

## Output PNG (nuovo)

Per esportare anche immagini PNG (heightmap, temperatura, umidità, biome):

```bash
python3 climate_biome_sim.py data/mia_heightmap.jpg --out-prefix output/mondo1 --export-png
```

File aggiuntivi prodotti:
>>>>>>> main

- `output/mondo1_heightmap.png`
- `output/mondo1_temperature.png`
- `output/mondo1_moisture.png`
- `output/mondo1_biome.png`

## File output CSV

<<<<<<< codex/create-climate-and-biome-simulation-program-bthtwi
Con prefisso `output/mondo1` ottieni sempre:
=======
Con prefisso `output/mondo1` otterrai sempre:
>>>>>>> main

- `output/mondo1_heightmap.csv`
- `output/mondo1_temperature.csv`
- `output/mondo1_moisture.csv`
- `output/mondo1_biome.csv`

## Modello climatico (versione 0)

- **Temperatura** = gradiente latitudinale - penalità altitudine.
- **Umidità** = venti prevalenti Ovest→Est, evaporazione dal mare, effetto rain shadow dietro montagne.
- **Bioma** = classificazione a soglia usando altitudine, temperatura e umidità.

## Idee per i prossimi step

- stagionalità e venti dinamici
- correnti oceaniche
- erosione e fiumi
- visualizzazione grafica (matplotlib / web)
