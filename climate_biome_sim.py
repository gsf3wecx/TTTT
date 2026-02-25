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
import heapq
import math
import random
from pathlib import Path
from typing import List

Grid = List[List[float]]
BiomeGrid = List[List[str]]
SUPPORTED_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg"}

BIOME_COLORS: dict[str, tuple[int, int, int]] = {
    "OCEAN": (30, 90, 180),
    "Calotta polare": (230, 245, 255),
    "Tundra": (190, 215, 220),
    "Taiga": (58, 95, 62),
    "Foresta decidua": (88, 148, 70),
    "Steppa e prateria": (180, 200, 95),
    "Foresta pluviale temperata": (25, 120, 78),
    "Foresta pluviale equatoriale": (13, 94, 45),
    "Foresta e macchia mediterranea": (125, 150, 85),
    "Giungla": (15, 125, 40),
    "Deserto sabbioso": (237, 201, 140),
    "Deserto roccioso": (193, 163, 128),
    "Deserto semiarido": (199, 186, 132),
    "Steppa arida": (171, 170, 104),
    "Savana erbosa": (156, 180, 75),
    "Savana alberata": (118, 160, 72),
    "Foresta subtropicale arida": (92, 132, 74),
    "Tundra alpina": (200, 210, 210),
    "Vegetazione alpina": (170, 185, 155),
}


class ClimateBiomeSimulator:
    def __init__(
        self,
        sea_level: float = 0.45,
        lapse_rate: float = 0.65,
        mountain_threshold: float = 0.75,
        equator_temp: float = 1.0,
        north_pole_temp: float = 0.0,
        south_pole_temp: float = 0.0,
    ) -> None:
        self.sea_level = sea_level
        self.lapse_rate = lapse_rate
        self.mountain_threshold = mountain_threshold
        self.equator_temp = equator_temp
        self.north_pole_temp = north_pole_temp
        self.south_pole_temp = south_pole_temp

    def simulate(self, heightmap: Grid) -> tuple[Grid, Grid, BiomeGrid]:
        self._validate_heightmap(heightmap)

        temperature = self._compute_temperature(heightmap)
        moisture = self._compute_moisture(heightmap)

        # Smussa leggermente i campi climatici prima della classificazione
        # per ridurre i bordi netti a pixel singolo.
        temperature_for_biome = self._blur(temperature)
        moisture_for_biome = self._blur(moisture)

        biomes = self._classify_biomes(heightmap, temperature_for_biome, moisture_for_biome)
        return temperature, moisture, biomes

    def _compute_temperature(self, heightmap: Grid) -> Grid:
        rows = len(heightmap)
        cols = len(heightmap[0])
        coast_distance = self._distance_to_water(heightmap)
        result: Grid = [[0.0 for _ in range(cols)] for _ in range(rows)]

        for r in range(rows):
            # Profilo latitudinale asimmetrico configurabile:
            # Polo Nord -> Equatore -> Polo Sud.
            if rows <= 1:
                latitude_temp = self.equator_temp
            else:
                pos = r / (rows - 1)  # 0=nord, 1=sud
                if pos <= 0.5:
                    mix = pos / 0.5
                    latitude_temp = self.north_pole_temp + (self.equator_temp - self.north_pole_temp) * mix
                else:
                    mix = (pos - 0.5) / 0.5
                    latitude_temp = self.equator_temp + (self.south_pole_temp - self.equator_temp) * mix

            for c in range(cols):
                elevation = heightmap[r][c]
                altitude_penalty = max(0.0, elevation - self.sea_level) * self.lapse_rate
                continentality_penalty = coast_distance[r][c] * 0.07
                temp = latitude_temp - altitude_penalty - continentality_penalty
                result[r][c] = min(1.0, max(0.0, temp))

        return result

    def _compute_moisture(self, heightmap: Grid) -> Grid:
        rows = len(heightmap)
        cols = len(heightmap[0])

        coast_distance = self._distance_to_water(heightmap)
        lat_moisture: Grid = [[0.0 for _ in range(cols)] for _ in range(rows)]

        for r in range(rows):
            latitude = abs((r / (rows - 1)) * 2 - 1) if rows > 1 else 0.0

            # Fasce climatiche semplificate (più realistiche globalmente):
            # equatore umido, subtropicale più secca, medie latitudini più umide.
            equatorial_wet = max(0.0, 1.0 - abs(latitude - 0.0) / 0.33)
            subtropical_dry = max(0.0, 1.0 - abs(latitude - 0.33) / 0.18)
            temperate_wet = max(0.0, 1.0 - abs(latitude - 0.58) / 0.24)

            band_value = 0.30 + 0.50 * equatorial_wet + 0.25 * temperate_wet - 0.28 * subtropical_dry
            band_value = min(1.0, max(0.0, band_value))
            for c in range(cols):
                lat_moisture[r][c] = band_value

        # Advezione bidirezionale per non confinare la pioggia alle sole coste ovest.
        adv_west_to_east = self._advection_moisture(heightmap, west_to_east=True)
        adv_east_to_west = self._advection_moisture(heightmap, west_to_east=False)

        moisture: Grid = [[0.0 for _ in range(cols)] for _ in range(rows)]
        for r in range(rows):
            for c in range(cols):
                h = heightmap[r][c]
                if h < self.sea_level:
                    moisture[r][c] = 1.0
                    continue

                coast_factor = math.exp(-2.1 * coast_distance[r][c])
                adv = (adv_west_to_east[r][c] + adv_east_to_west[r][c]) * 0.5

                # Peso importante alle fasce latitudinali: l'equatore resta piovoso
                # anche in zone non strettamente costiere.
                m = 0.18 * coast_factor + 0.56 * lat_moisture[r][c] + 0.26 * adv
                moisture[r][c] = min(1.0, max(0.0, m))

        # Diffusione orizzontale leggera per far penetrare l'umidità nell'interno.
        for _ in range(7):
            blurred = self._blur(moisture)
            for r in range(rows):
                for c in range(cols):
                    if heightmap[r][c] < self.sea_level:
                        moisture[r][c] = 1.0
                    else:
                        moisture[r][c] = min(
                            1.0,
                            max(
                                0.0,
                                0.58 * moisture[r][c] + 0.30 * blurred[r][c] + 0.12 * lat_moisture[r][c],
                            ),
                        )

        return moisture

    def _advection_moisture(self, heightmap: Grid, west_to_east: bool) -> Grid:
        rows = len(heightmap)
        cols = len(heightmap[0])
        result: Grid = [[0.0 for _ in range(cols)] for _ in range(rows)]

        indices = range(cols) if west_to_east else range(cols - 1, -1, -1)

        for r in range(rows):
            carried_humidity = 0.0
            for c in indices:
                h = heightmap[r][c]
                is_water = h < self.sea_level

                if is_water:
                    carried_humidity = min(1.0, carried_humidity + 0.34)
                    result[r][c] = 1.0
                    continue

                rain = carried_humidity * 0.34
                result[r][c] = min(1.0, rain + 0.05)

                if h > self.mountain_threshold:
                    carried_humidity *= 0.30
                elif h > self.sea_level + 0.08:
                    carried_humidity *= 0.66
                else:
                    carried_humidity *= 0.84

        return result

    def _classify_biomes(self, heightmap: Grid, temperature: Grid, moisture: Grid) -> BiomeGrid:
        rows = len(heightmap)
        cols = len(heightmap[0])
        biomes: BiomeGrid = [["" for _ in range(cols)] for _ in range(rows)]

        for r in range(rows):
            latitude = abs((r / (rows - 1)) * 2 - 1) if rows > 1 else 0.0
            for c in range(cols):
                h = heightmap[r][c]
                t = temperature[r][c]
                m = moisture[r][c]

                if h < self.sea_level:
                    biomes[r][c] = "OCEAN"
                    continue

                # Biomi montani/alpini
                if h > 0.93:
                    biomes[r][c] = "Tundra alpina" if t < 0.35 else "Vegetazione alpina"
                    continue
                if h > 0.86 and t < 0.30:
                    biomes[r][c] = "Tundra alpina"
                    continue

                # Fascia polare
                if t < 0.08:
                    biomes[r][c] = "Calotta polare"
                elif t < 0.18:
                    biomes[r][c] = "Tundra"
                # Freddo
                elif t < 0.34:
                    if m < 0.28:
                        biomes[r][c] = "Steppa e prateria"
                    else:
                        biomes[r][c] = "Taiga"
                # Temperato
                elif t < 0.56:
                    if m < 0.16:
                        biomes[r][c] = "Steppa arida"
                    elif m < 0.30:
                        biomes[r][c] = "Steppa e prateria"
                    elif m < 0.55:
                        biomes[r][c] = "Foresta e macchia mediterranea"
                    elif m < 0.72:
                        biomes[r][c] = "Foresta decidua"
                    else:
                        biomes[r][c] = "Foresta pluviale temperata"
                # Caldo / subtropicale / tropicale
                else:
                    if m < 0.08:
                        biomes[r][c] = "Deserto roccioso" if h > self.sea_level + 0.2 else "Deserto sabbioso"
                    elif m < 0.16:
                        biomes[r][c] = "Deserto semiarido"
                    elif m < 0.26:
                        biomes[r][c] = "Foresta subtropicale arida"
                    elif m < 0.36:
                        biomes[r][c] = "Steppa arida"
                    elif m < 0.48:
                        biomes[r][c] = "Savana erbosa"
                    elif m < 0.62:
                        biomes[r][c] = "Savana alberata"
                    else:
                        # Equatore umido -> foresta pluviale equatoriale / giungla
                        if latitude < 0.18 and m > 0.78:
                            biomes[r][c] = "Giungla"
                        elif latitude < 0.24:
                            biomes[r][c] = "Foresta pluviale equatoriale"
                        else:
                            biomes[r][c] = "Foresta pluviale temperata"

        return biomes

    def _distance_to_water(self, heightmap: Grid) -> Grid:
        rows = len(heightmap)
        cols = len(heightmap[0])
        inf = float("inf")
        dist = [[inf for _ in range(cols)] for _ in range(rows)]
        heap: list[tuple[float, int, int]] = []

        for r in range(rows):
            for c in range(cols):
                if heightmap[r][c] < self.sea_level:
                    dist[r][c] = 0.0
                    heapq.heappush(heap, (0.0, r, c))

        if not heap:
            return [[1.0 for _ in range(cols)] for _ in range(rows)]

        neighbors = (
            (1, 0, 1.0),
            (-1, 0, 1.0),
            (0, 1, 1.0),
            (0, -1, 1.0),
            (1, 1, math.sqrt(2.0)),
            (1, -1, math.sqrt(2.0)),
            (-1, 1, math.sqrt(2.0)),
            (-1, -1, math.sqrt(2.0)),
        )

        while heap:
            current, r, c = heapq.heappop(heap)
            if current > dist[r][c]:
                continue
            for dr, dc, cost in neighbors:
                rr, cc = r + dr, c + dc
                if 0 <= rr < rows and 0 <= cc < cols:
                    candidate = current + cost
                    if candidate < dist[rr][cc]:
                        dist[rr][cc] = candidate
                        heapq.heappush(heap, (candidate, rr, cc))

        max_dist = max(max(row) for row in dist)
        if not math.isfinite(max_dist) or max_dist <= 0.0:
            return [[0.0 for _ in range(cols)] for _ in range(rows)]

        return [[d / max_dist for d in row] for row in dist]

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

    if input_path and input_path.suffix.lower() in SUPPORTED_IMAGE_SUFFIXES:
        auto_level = quantile(flatten_grid(heightmap), sea_level_quantile)
        return auto_level, f"auto-quantile({sea_level_quantile:.2f})"

    return 0.45, "default"


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
    raise ValueError("Formato heightmap non supportato. Usa CSV, PNG, JPG o JPEG.")


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

    for _ in range(3):
        grid = ClimateBiomeSimulator._blur(grid)

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
    parser.add_argument(
        "--temp-equator",
        type=float,
        default=1.0,
        help="Temperatura normalizzata all'equatore (0..1).",
    )
    parser.add_argument(
        "--temp-north-pole",
        type=float,
        default=0.0,
        help="Temperatura normalizzata al polo nord (0..1).",
    )
    parser.add_argument(
        "--temp-south-pole",
        type=float,
        default=0.0,
        help="Temperatura normalizzata al polo sud (0..1).",
    )
    parser.add_argument("--rows", type=int, default=64, help="Righe per heightmap casuale.")
    parser.add_argument("--cols", type=int, default=96, help="Colonne per heightmap casuale.")
    parser.add_argument("--seed", type=int, default=42, help="Seed generatore casuale.")
    parser.add_argument(
        "--export-png",
        action="store_true",
        help="Esporta anche PNG per heightmap/temperature/moisture/biome (richiede Pillow).",
    )
    return parser.parse_args()


def validate_cli_args(args: argparse.Namespace) -> None:
    if args.sea_level is not None and not 0.0 <= args.sea_level <= 1.0:
        raise ValueError("--sea-level deve essere compreso tra 0 e 1.")
    if not 0.0 <= args.sea_level_quantile <= 1.0:
        raise ValueError("--sea-level-quantile deve essere compreso tra 0 e 1.")
    if args.rows <= 0 or args.cols <= 0:
        raise ValueError("--rows e --cols devono essere interi positivi.")

    for option_name, option_value in (
        ("--temp-equator", args.temp_equator),
        ("--temp-north-pole", args.temp_north_pole),
        ("--temp-south-pole", args.temp_south_pole),
    ):
        if not 0.0 <= option_value <= 1.0:
            raise ValueError(f"{option_name} deve essere compreso tra 0 e 1.")


def main() -> None:
    args = parse_args()
    validate_cli_args(args)

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

    simulator = ClimateBiomeSimulator(
        sea_level=effective_sea_level,
        equator_temp=args.temp_equator,
        north_pole_temp=args.temp_north_pole,
        south_pole_temp=args.temp_south_pole,
    )
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
    print(
        f"Sea level effettivo: {effective_sea_level:.4f} "
        f"(mode={sea_level_mode}, oceano={ocean_ratio(heightmap, effective_sea_level) * 100:.1f}%)"
    )
    print(
        "Temperature: "
        f"north={args.temp_north_pole:.2f}, equator={args.temp_equator:.2f}, south={args.temp_south_pole:.2f}"
    )
    if args.export_png:
        print("PNG esportati (heightmap/temperature/moisture/biome).")
    print("Distribuzione biomi:")
    for biome, count in summarize_biomes(biomes).items():
        print(f" - {biome:28s}: {count}")


if __name__ == "__main__":
    main()
