#!/usr/bin/env python3
"""Simulatore semplice di clima e biomi basato su una heightmap.

Input heightmap supportato:
- CSV con valori numerici normalizzati in [0, 1]
- Immagini PNG/JPG/JPEG (convertite in scala di grigi e normalizzate in [0, 1])

Output:
- *_temperature.csv : temperatura normalizzata [0, 1]
- *_moisture.csv    : umidità normalizzata [0, 1]
- *_biome.csv       : etichette biome per cella
- opzionale: PNG per heightmap/temperature/moisture/biome
"""

from __future__ import annotations

import argparse
import csv
import random
from pathlib import Path
from typing import List

Grid = List[List[float]]
BiomeGrid = List[List[str]]
SUPPORTED_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg"}

BIOME_COLORS: dict[str, tuple[int, int, int]] = {
    "OCEAN": (30, 90, 180),
    "ALPINE": (180, 180, 180),
    "TUNDRA": (210, 230, 230),
    "DESERT": (237, 201, 175),
    "GRASSLAND": (124, 179, 66),
    "TEMPERATE_FOREST": (34, 139, 34),
    "TROPICAL_FOREST": (0, 100, 0),
}


class ClimateBiomeSimulator:
    def __init__(
        self,
        sea_level: float = 0.45,
        lapse_rate: float = 0.65,
        mountain_threshold: float = 0.75,
    ) -> None:
        self.sea_level = sea_level
        self.lapse_rate = lapse_rate
        self.mountain_threshold = mountain_threshold

    def simulate(self, heightmap: Grid) -> tuple[Grid, Grid, BiomeGrid]:
        self._validate_heightmap(heightmap)

        temperature = self._compute_temperature(heightmap)
        moisture = self._compute_moisture(heightmap)
        biomes = self._classify_biomes(heightmap, temperature, moisture)
        return temperature, moisture, biomes

    def _compute_temperature(self, heightmap: Grid) -> Grid:
        rows = len(heightmap)
        cols = len(heightmap[0])
        result: Grid = [[0.0 for _ in range(cols)] for _ in range(rows)]

        for r in range(rows):
            latitude = abs((r / (rows - 1)) * 2 - 1) if rows > 1 else 0
<<<<<<< codex/create-climate-and-biome-simulation-program-bthtwi
            latitude_factor = 1.0 - latitude
=======
            latitude_factor = 1.0 - latitude  # caldo all'equatore, freddo ai poli
>>>>>>> main
            for c in range(cols):
                elevation = heightmap[r][c]
                altitude_penalty = max(0.0, elevation - self.sea_level) * self.lapse_rate
                temp = latitude_factor - altitude_penalty
                result[r][c] = min(1.0, max(0.0, temp))

        return result

    def _compute_moisture(self, heightmap: Grid) -> Grid:
        rows = len(heightmap)
        cols = len(heightmap[0])
        moisture: Grid = [[0.0 for _ in range(cols)] for _ in range(rows)]

<<<<<<< codex/create-climate-and-biome-simulation-program-bthtwi
=======
        # Venti prevalenti da ovest verso est (scan da sinistra a destra).
>>>>>>> main
        for r in range(rows):
            carried_humidity = 0.0
            for c in range(cols):
                h = heightmap[r][c]
                is_water = h < self.sea_level

                if is_water:
                    carried_humidity = min(1.0, carried_humidity + 0.35)
                    moisture[r][c] = 1.0
                    continue

<<<<<<< codex/create-climate-and-biome-simulation-program-bthtwi
                rain = carried_humidity * 0.3
                moisture[r][c] = rain

=======
                # Precipitazione su terra: parte dell'umidità cade.
                rain = carried_humidity * 0.3
                moisture[r][c] = rain

                # Rain shadow dietro montagne elevate.
>>>>>>> main
                if h > self.mountain_threshold:
                    carried_humidity *= 0.35
                else:
                    carried_humidity *= 0.82

<<<<<<< codex/create-climate-and-biome-simulation-program-bthtwi
                moisture[r][c] = min(1.0, moisture[r][c] + 0.05)

=======
                # Evapotraspirazione locale minima.
                moisture[r][c] = min(1.0, moisture[r][c] + 0.05)

        # Smussamento leggero locale.
>>>>>>> main
        return self._blur(moisture)

    def _classify_biomes(self, heightmap: Grid, temperature: Grid, moisture: Grid) -> BiomeGrid:
        rows = len(heightmap)
        cols = len(heightmap[0])
        biomes: BiomeGrid = [["" for _ in range(cols)] for _ in range(rows)]

        for r in range(rows):
            for c in range(cols):
                h = heightmap[r][c]
                t = temperature[r][c]
                m = moisture[r][c]

                if h < self.sea_level:
                    biomes[r][c] = "OCEAN"
                elif h > 0.90:
                    biomes[r][c] = "ALPINE"
                elif t < 0.2:
                    biomes[r][c] = "TUNDRA"
                elif m < 0.15:
                    biomes[r][c] = "DESERT"
                elif m < 0.35:
                    biomes[r][c] = "GRASSLAND"
                elif t > 0.65 and m > 0.6:
                    biomes[r][c] = "TROPICAL_FOREST"
                else:
                    biomes[r][c] = "TEMPERATE_FOREST"

        return biomes

    @staticmethod
    def _blur(grid: Grid) -> Grid:
        rows = len(grid)
        cols = len(grid[0])
        result: Grid = [[0.0 for _ in range(cols)] for _ in range(rows)]

        for r in range(rows):
            for c in range(cols):
                acc = 0.0
                count = 0
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        rr, cc = r + dr, c + dc
                        if 0 <= rr < rows and 0 <= cc < cols:
                            acc += grid[rr][cc]
                            count += 1
                result[r][c] = acc / count
        return result

    @staticmethod
    def _validate_heightmap(heightmap: Grid) -> None:
        if not heightmap or not heightmap[0]:
            raise ValueError("La heightmap è vuota.")
        width = len(heightmap[0])
        for row in heightmap:
            if len(row) != width:
                raise ValueError("La heightmap deve essere rettangolare.")
            for value in row:
                if not 0.0 <= value <= 1.0:
                    raise ValueError("I valori della heightmap devono essere in [0, 1].")


def _require_pillow():
    try:
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError(
            "Per leggere/scrivere PNG/JPG serve Pillow. Installa con: pip install pillow"
        ) from exc
    return Image


<<<<<<< codex/create-climate-and-biome-simulation-program-bthtwi
def flatten_grid(grid: Grid) -> list[float]:
    return [v for row in grid for v in row]


def quantile(values: list[float], q: float) -> float:
    if not values:
        raise ValueError("Impossibile calcolare il quantile su lista vuota.")
    q = min(1.0, max(0.0, q))
    sorted_values = sorted(values)
    idx = int((len(sorted_values) - 1) * q)
    return sorted_values[idx]


def ocean_ratio(heightmap: Grid, sea_level: float) -> float:
    values = flatten_grid(heightmap)
    sea_cells = sum(1 for v in values if v < sea_level)
    return sea_cells / max(1, len(values))


def choose_effective_sea_level(
    heightmap: Grid,
    input_path: Path | None,
    sea_level: float | None,
    sea_level_quantile: float,
) -> tuple[float, str]:
    if sea_level is not None:
        return sea_level, "manual"

    # Per immagini reali il range utile spesso è sbilanciato: scegliamo un livello
    # mare automatico basato su quantile (target oceano).
    if input_path and input_path.suffix.lower() in SUPPORTED_IMAGE_SUFFIXES:
        auto_level = quantile(flatten_grid(heightmap), sea_level_quantile)
        return auto_level, f"auto-quantile({sea_level_quantile:.2f})"

    return 0.45, "default"


=======
>>>>>>> main
def read_heightmap_csv(path: Path) -> Grid:
    with path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        grid = [[float(cell.strip()) for cell in row] for row in reader if row]
    return grid


def read_heightmap_image(path: Path) -> Grid:
    Image = _require_pillow()

    with Image.open(path) as img:
        gray = img.convert("L")
        width, height = gray.size
        flatten_fn = getattr(gray, "get_flattened_data", None)
        if callable(flatten_fn):
            pixels = list(flatten_fn())
        else:
            pixels = list(gray.getdata())

    if width == 0 or height == 0:
        raise ValueError("L'immagine della heightmap è vuota.")

    grid: Grid = []
    for r in range(height):
        start = r * width
        row = pixels[start : start + width]
        grid.append([value / 255.0 for value in row])
    return grid


def read_heightmap(path: Path) -> Grid:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return read_heightmap_csv(path)
    if suffix in SUPPORTED_IMAGE_SUFFIXES:
        return read_heightmap_image(path)
<<<<<<< codex/create-climate-and-biome-simulation-program-bthtwi
    raise ValueError("Formato heightmap non supportato. Usa CSV, PNG, JPG o JPEG.")
=======
    raise ValueError(
        "Formato heightmap non supportato. Usa CSV, PNG, JPG o JPEG."
    )
>>>>>>> main


def write_float_grid_csv(path: Path, grid: Grid) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        for row in grid:
            writer.writerow([f"{value:.4f}" for value in row])


def write_biome_grid_csv(path: Path, grid: BiomeGrid) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(grid)


def write_float_grid_png(path: Path, grid: Grid) -> None:
    Image = _require_pillow()
    rows = len(grid)
    cols = len(grid[0])
    pixels = [int(max(0.0, min(1.0, v)) * 255.0) for row in grid for v in row]
    image = Image.new("L", (cols, rows))
    image.putdata(pixels)
    image.save(path)


def write_biome_grid_png(path: Path, grid: BiomeGrid) -> None:
    Image = _require_pillow()
    rows = len(grid)
    cols = len(grid[0])

    pixels: list[tuple[int, int, int]] = []
    for row in grid:
        for biome in row:
            pixels.append(BIOME_COLORS.get(biome, (255, 0, 255)))

    image = Image.new("RGB", (cols, rows))
    image.putdata(pixels)
    image.save(path)


def generate_random_heightmap(rows: int, cols: int, seed: int | None = None) -> Grid:
    rng = random.Random(seed)
    grid: Grid = [[rng.random() for _ in range(cols)] for _ in range(rows)]

<<<<<<< codex/create-climate-and-biome-simulation-program-bthtwi
    for _ in range(3):
        grid = ClimateBiomeSimulator._blur(grid)

=======
    # Smussa per ottenere forme più naturali.
    for _ in range(3):
        grid = ClimateBiomeSimulator._blur(grid)

    # Normalizza dopo smussamento.
>>>>>>> main
    min_v = min(min(row) for row in grid)
    max_v = max(max(row) for row in grid)
    span = max(1e-9, max_v - min_v)
    return [[(v - min_v) / span for v in row] for row in grid]


def summarize_biomes(biome_grid: BiomeGrid) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in biome_grid:
        for biome in row:
            counts[biome] = counts.get(biome, 0) + 1
    return dict(sorted(counts.items(), key=lambda kv: kv[0]))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Simula clima e biomi da una heightmap CSV o immagine.")
    parser.add_argument(
        "input",
        nargs="?",
        help="Path heightmap: CSV (0..1) oppure PNG/JPG/JPEG in scala di grigi.",
    )
    parser.add_argument("--out-prefix", default="output/world", help="Prefisso file di output.")
<<<<<<< codex/create-climate-and-biome-simulation-program-bthtwi
    parser.add_argument(
        "--sea-level",
        type=float,
        default=None,
        help="Livello del mare assoluto (0..1). Se omesso, su immagini viene stimato automaticamente.",
    )
    parser.add_argument(
        "--sea-level-quantile",
        type=float,
        default=0.72,
        help="Quantile usato per auto-stima livello mare su immagini (es. 0.72 ≈ 72%% oceano).",
    )
=======
    parser.add_argument("--sea-level", type=float, default=0.45, help="Livello del mare (0..1).")
>>>>>>> main
    parser.add_argument("--rows", type=int, default=64, help="Righe per heightmap casuale.")
    parser.add_argument("--cols", type=int, default=96, help="Colonne per heightmap casuale.")
    parser.add_argument("--seed", type=int, default=42, help="Seed generatore casuale.")
    parser.add_argument(
        "--export-png",
        action="store_true",
        help="Esporta anche PNG per heightmap/temperature/moisture/biome (richiede Pillow).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

<<<<<<< codex/create-climate-and-biome-simulation-program-bthtwi
    input_path: Path | None = Path(args.input) if args.input else None
    if input_path:
        heightmap = read_heightmap(input_path)
    else:
        heightmap = generate_random_heightmap(args.rows, args.cols, args.seed)

    effective_sea_level, sea_level_mode = choose_effective_sea_level(
        heightmap=heightmap,
        input_path=input_path,
        sea_level=args.sea_level,
        sea_level_quantile=args.sea_level_quantile,
    )

    simulator = ClimateBiomeSimulator(sea_level=effective_sea_level)
=======
    if args.input:
        heightmap = read_heightmap(Path(args.input))
    else:
        heightmap = generate_random_heightmap(args.rows, args.cols, args.seed)

    simulator = ClimateBiomeSimulator(sea_level=args.sea_level)
>>>>>>> main
    temperature, moisture, biomes = simulator.simulate(heightmap)

    out_prefix = Path(args.out_prefix)
    out_prefix.parent.mkdir(parents=True, exist_ok=True)

    write_float_grid_csv(Path(f"{out_prefix}_heightmap.csv"), heightmap)
    write_float_grid_csv(Path(f"{out_prefix}_temperature.csv"), temperature)
    write_float_grid_csv(Path(f"{out_prefix}_moisture.csv"), moisture)
    write_biome_grid_csv(Path(f"{out_prefix}_biome.csv"), biomes)

    if args.export_png:
        write_float_grid_png(Path(f"{out_prefix}_heightmap.png"), heightmap)
        write_float_grid_png(Path(f"{out_prefix}_temperature.png"), temperature)
        write_float_grid_png(Path(f"{out_prefix}_moisture.png"), moisture)
        write_biome_grid_png(Path(f"{out_prefix}_biome.png"), biomes)

    print("Simulazione completata.")
    print(f"Output scritto con prefisso: {out_prefix}")
<<<<<<< codex/create-climate-and-biome-simulation-program-bthtwi
    print(
        f"Sea level effettivo: {effective_sea_level:.4f} "
        f"(mode={sea_level_mode}, oceano={ocean_ratio(heightmap, effective_sea_level) * 100:.1f}%)"
    )
=======
>>>>>>> main
    if args.export_png:
        print("PNG esportati (heightmap/temperature/moisture/biome).")
    print("Distribuzione biomi:")
    for biome, count in summarize_biomes(biomes).items():
        print(f" - {biome:18s}: {count}")


if __name__ == "__main__":
    main()
