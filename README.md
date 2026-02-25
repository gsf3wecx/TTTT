# Simulatore clima + biomi da heightmap

Programma iniziale (semplice ma estendibile) che, data una **heightmap** normalizzata `[0..1]`, calcola:

- temperatura
- umidità / precipitazione relativa
- bioma risultante per ogni cella

## Formati input supportati

- **CSV** rettangolare con valori numerici tra `0` e `1`
- **PNG / JPG / JPEG** (convertiti in scala di grigi; `0`=nero=quota bassa, `255`=bianco=quota alta)

> Per PNG/JPG e per l'export PNG è richiesta la libreria **Pillow**:
>
> ```bash
> pip install pillow
> ```

## Livello del mare

Per le **immagini** il livello del mare può essere:

- manuale con `--sea-level`
- automatico via quantile con `--sea-level-quantile` (default `0.72`)

Esempio:

```bash
python3 climate_biome_sim.py data/mia_heightmap.jpg --out-prefix output/mondo1 --sea-level-quantile 0.70 --export-png
```

## Temperature personalizzate (nuovo)

Ora puoi impostare il profilo termico globale in modo indipendente:

- `--temp-equator` (default `1.0`)
- `--temp-north-pole` (default `0.0`)
- `--temp-south-pole` (default `0.0`)

Esempio:

```bash
python3 climate_biome_sim.py data/mia_heightmap.jpg \
  --out-prefix output/mondo1 \
  --temp-equator 0.95 \
  --temp-north-pole 0.10 \
  --temp-south-pole 0.05 \
  --export-png
```

## Modello climatico (versione 2)

- **Temperatura** = gradiente latitudinale asimmetrico (Nord→Equatore→Sud, personalizzabile) + penalità altitudine + continentalità.
- **Umidità** = fasce latitudinali + advezione bidirezionale + distanza dal mare + diffusione interna, per far penetrare meglio le precipitazioni anche all'interno dei continenti.
- **Transizioni biome** = smoothing climatico pre-classificazione per ridurre artefatti a blocchi.

## Biomi disponibili

- Calotta polare
- Tundra
- Taiga
- Foresta decidua
- Steppa e prateria
- Foresta pluviale temperata
- Foresta pluviale equatoriale
- Foresta e macchia mediterranea
- Giungla
- Deserto sabbioso
- Deserto roccioso
- Deserto semiarido
- Steppa arida
- Savana erbosa
- Savana alberata
- Foresta subtropicale arida
- Tundra alpina
- Vegetazione alpina

## Output PNG

Con `--export-png` vengono salvati:

- `output/mondo1_heightmap.png`
- `output/mondo1_temperature.png`
- `output/mondo1_moisture.png`
- `output/mondo1_biome.png`

## Output CSV

Con prefisso `output/mondo1` ottieni:

- `output/mondo1_heightmap.csv`
- `output/mondo1_temperature.csv`
- `output/mondo1_moisture.csv`
- `output/mondo1_biome.csv`
