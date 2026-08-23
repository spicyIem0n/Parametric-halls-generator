"""
RoofLightFactory - swietliki, klapy dymowe i pasma swietlne na dachu.

ZASADA ROZMIESZCZANIA (zgodna z praktyka projektowa):

1. PASMA SWIETLNE biegna wzdluz hali (rownolegle do kalenicy). Szerokosc
   strefy dzielona jest na N ROWNYCH PASM (bands), a pasmo siedzi w SRODKU
   swojego pasma -> rowne odstepy od krawedzi dachu i miedzy pasmami.
   Pozycja jest delikatnie przyciagana do platwi (maks. 1/4 rozstawu),
   zeby krawedz opierala sie na konstrukcji, bez psucia rownomiernosci.

2. ELEMENTY PUNKTOWE (swietliki, klapy) montowane sa w PASACH WOLNYCH -
   fragmentach szerokosci nie zajetych przez pasma. Kolumny siatki = wolne
   pasy (naturalne miejsca montazu), wiersze = rowne podzialy calej
   dlugosci strefy. Element siedzi w srodku swojego pasa i wiersza, wiec
   rozklada sie rownomiernie w obu kierunkach. Kolumny sa mapowane na pasy
   rownomiernie po szerokosci hali.

3. Brak nachodzenia jest gwarantowany geometrycznie: pasma zajmuja
   rozlaczne bands, elementy punktowe rozlaczne komorki w pasach wolnych,
   miedzy pasmem a pasem wolnym jest margines EDGE_MARGIN, a szerokosc
   elementu jest ograniczana do szerokosci pasa i komorki.

4. Zaden element nie jest pomijany: pasma zwezaja sie do swojego pasma,
   a liczba wierszy rosnie tak, by pomiescic wszystkie elementy punktowe.
"""

import math
from typing import List, Tuple
from models import Component3D, HallParameters, RoofLightZoneConfig, RoofLightItem
from core.grid_system import GridSystem3D

EDGE_MARGIN = 0.35      # margines miedzy krawedzia elementu a granica pasa/komorki [m]
ROOF_CLEARANCE = 0.5    # wystawanie ponad pokrycie dachu [m]


class RoofLightFactory:

    @staticmethod
    def generate(grid: GridSystem3D, params: HallParameters) -> list:
        elements = []
        if not params.roof_lights:
            return elements
        dock_enabled = getattr(params, "dock_zone_enabled", False)
        dock_side = getattr(params, "dock_zone_side", "left")
        for zone_config in params.roof_lights:
            # Gdy strefa dokowa z obu stron -> dzielimy elementy na pol
            # i generujemy osobno dla lewej i prawej strefy dokowej
            if (zone_config.zone_id == "dock_zone"
                    and dock_enabled and dock_side == "both"):
                from copy import deepcopy
                items = zone_config.items or []
                left_items, right_items = [], []
                for it in items:
                    qty = max(1, it.quantity)
                    qty_left = qty // 2 + qty % 2
                    qty_right = qty - qty_left
                    if qty_left > 0:
                        it_l = deepcopy(it)
                        it_l.quantity = qty_left
                        it_l.item_id = it.item_id + "_L"
                        left_items.append(it_l)
                    if qty_right > 0:
                        it_r = deepcopy(it)
                        it_r.quantity = qty_right
                        it_r.item_id = it.item_id + "_R"
                        right_items.append(it_r)
                if left_items:
                    left_cfg = RoofLightZoneConfig(
                        zone_id="dock_zone_left", items=left_items)
                    elements.extend(
                        RoofLightFactory._generate_zone(grid, params, left_cfg))
                if right_items:
                    right_cfg = RoofLightZoneConfig(
                        zone_id="dock_zone_right", items=right_items)
                    elements.extend(
                        RoofLightFactory._generate_zone(grid, params, right_cfg))
            else:
                elements.extend(
                    RoofLightFactory._generate_zone(grid, params, zone_config))
        return elements

    # ---------------- GRANICE STREFY ----------------

    @staticmethod
    def _get_zone_bounds(grid, params, zone_id: str) -> Tuple[float, float, float, float]:
        z_min, z_max = -grid.half_length, grid.half_length
        dock_enabled = getattr(params, "dock_zone_enabled", False)
        dock_side = getattr(params, "dock_zone_side", "left")
        dock_w = getattr(params, "dock_zone_width", 12.0)

        if zone_id == "dock_zone" and dock_enabled:
            if dock_side == "right":
                return (grid.half_width - dock_w, grid.half_width, z_min, z_max)
            if dock_side == "both":
                # Fallback: cala lewa strona (nie powinno byc wywolywane przy both)
                return (-grid.half_width, -grid.half_width + dock_w, z_min, z_max)
            return (-grid.half_width, -grid.half_width + dock_w, z_min, z_max)

        if zone_id == "dock_zone_left" and dock_enabled:
            return (-grid.half_width, -grid.half_width + dock_w, z_min, z_max)

        if zone_id == "dock_zone_right" and dock_enabled:
            return (grid.half_width - dock_w, grid.half_width, z_min, z_max)

        if dock_enabled:
            if dock_side == "left":
                return (-grid.half_width + dock_w, grid.half_width, z_min, z_max)
            if dock_side == "right":
                return (-grid.half_width, grid.half_width - dock_w, z_min, z_max)
            if dock_side == "both":
                return (-grid.half_width + dock_w, grid.half_width - dock_w, z_min, z_max)
        return (-grid.half_width, grid.half_width, z_min, z_max)

    # ---------------- POMOCNICZE ----------------

    @staticmethod
    def _soft_snap_to_purlin(x: float, grid: GridSystem3D, width: float) -> float:
        max_shift = max(0.15, grid.params.purlin_spacing * 0.25)
        best, best_d = x, max_shift
        for px in grid.get_purlin_xs():
            for cand in (px + width / 2.0, px - width / 2.0):
                d = abs(cand - x)
                if d < best_d:
                    best_d, best = d, cand
        return best

    @staticmethod
    def _free_segments(x_min, x_max, occupied: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        if not occupied:
            return [(x_min, x_max)]
        occupied = sorted(occupied)
        free, cursor = [], x_min
        for a, b in occupied:
            a, b = max(a, x_min), min(b, x_max)
            if a - cursor > 0.6:
                free.append((cursor, a))
            cursor = max(cursor, b)
        if x_max - cursor > 0.6:
            free.append((cursor, x_max))
        return free

    # ---------------- GLOWNA LOGIKA ----------------

    @staticmethod
    def _generate_zone(grid, params, zone_config: RoofLightZoneConfig) -> list:
        elements = []
        x_min, x_max, z_min, z_max = RoofLightFactory._get_zone_bounds(grid, params, zone_config.zone_id)
        items = zone_config.items or []
        zone_w = x_max - x_min
        zone_len = z_max - z_min
        if not items or zone_w <= 0.5 or zone_len <= 0.5:
            return elements

        strip_items = [i for i in items if i.item_type in ("light_strip", "light_strip_with_vents")]
        point_items = [i for i in items if i.item_type in ("skylight", "smoke_vent")]

        # ---- FAZA 1: PASMA - rowne bands, pasmo w srodku swojego bandu ----
        strip_instances: List[RoofLightItem] = []
        for it in strip_items:
            strip_instances.extend([it] * max(1, it.quantity))

        occupied: List[Tuple[float, float]] = []
        n_strips = len(strip_instances)
        if n_strips > 0:
            # Reprezentatywne wymiary (max, zeby siatka byla bezpieczna dla wszystkich)
            rep_len = max(max(1.0, min(it.length, zone_len - 2 * EDGE_MARGIN))
                          for it in strip_instances)
            rep_w = max(it.width for it in strip_instances)
            coverage = rep_len / zone_len if zone_len > 0 else 1.0

            max_cols = max(1, int(zone_w // max(rep_w + 2 * EDGE_MARGIN, 0.1)))
            max_rows = max(1, int(zone_len // max(rep_len + 2 * EDGE_MARGIN, 0.1)))

            if coverage >= 0.6 or max_rows <= 1:
                # Klasyczne pasma ciagle: kazda instancja dostaje wlasny pas
                # na calej dlugosci hali (jeden rzad).
                cols = n_strips
                rows = 1
            else:
                # Pasma krotkie wzgledem hali -> rozkladamy je rowniez WZDLUZ
                # dlugosci, zeby swiatlo bylo rozprowadzone po calym budynku,
                # a nie skupione miedzy srodkowymi ramami.
                cols = max(1, min(n_strips, max_cols,
                                  int(math.ceil(math.sqrt(n_strips * zone_w / zone_len)))))
                rows = int(math.ceil(n_strips / cols))
                if rows > max_rows:
                    rows = max_rows
                    cols = int(math.ceil(n_strips / rows))

            band_w = zone_w / cols
            row_h = zone_len / rows

            for idx, it in enumerate(strip_instances):
                col = idx % cols
                row = idx // cols
                if row >= rows:
                    row = rows - 1

                band_x0 = x_min + col * band_w
                band_center = band_x0 + band_w / 2.0

                strip_w = min(it.width, max(0.4, band_w - 2 * EDGE_MARGIN))
                cx = RoofLightFactory._soft_snap_to_purlin(band_center, grid, strip_w)
                lo = band_x0 + strip_w / 2.0 + EDGE_MARGIN * 0.5
                hi = band_x0 + band_w - strip_w / 2.0 - EDGE_MARGIN * 0.5
                cx = band_center if lo > hi else max(lo, min(hi, cx))

                if rows > 1:
                    strip_len = max(1.0, min(it.length, row_h - 2 * EDGE_MARGIN))
                    cz = z_min + (row + 0.5) * row_h
                else:
                    strip_len = max(1.0, min(it.length, zone_len - 2 * EDGE_MARGIN))
                    cz = (z_min + z_max) / 2.0

                y = grid.get_roof_height_at(cx) + ROOF_CLEARANCE

                elements.append(Component3D(
                    type="light_strip",
                    position=[cx, y, cz],
                    rotation=[0, 0, 0],
                    scale=[strip_w, 0.30, strip_len],
                    meta={"element_type": it.item_type, "item_id": it.item_id},
                ))

                if it.item_type == "light_strip_with_vents" and it.vent_count > 0:
                    gap = strip_len / (it.vent_count + 1)
                    vlen = max(0.5, min(it.vent_length, gap * 0.8))
                    for v in range(it.vent_count):
                        vz = cz - strip_len / 2.0 + (v + 1) * gap
                        elements.append(Component3D(
                            type="smoke_vent",
                            position=[cx, y + 0.20, vz],
                            rotation=[0, 0, 0],
                            scale=[strip_w * 0.9, 0.15, vlen],
                            meta={"element_type": "strip_smoke_vent", "item_id": it.item_id},
                        ))

                # Pas uznajemy za zajety na calej dlugosci (bezpiecznie wzgledem
                # elementow punktowych, nawet gdy pasma stoja w kilku rzedach).
                occupied.append((cx - strip_w / 2.0 - EDGE_MARGIN,
                                 cx + strip_w / 2.0 + EDGE_MARGIN))
        # ---- FAZA 2 + 3: WOLNE PASY i ELEMENTY PUNKTOWE ----
        if point_items:
            free_segments = RoofLightFactory._free_segments(x_min, x_max, occupied)
            if not free_segments:
                free_segments = [(x_min, x_max)]
            elements.extend(RoofLightFactory._layout_points(
                grid, point_items, free_segments, z_min, z_max))

        return elements

    # ---------------- ELEMENTY PUNKTOWE ----------------

    @staticmethod
    def _layout_points(grid, point_items: List[RoofLightItem],
                       free_segments: List[Tuple[float, float]],
                       z_min: float, z_max: float) -> list:
        elements = []

        # Przeplot typow (round-robin) - swietliki i klapy przemieszane
        queues = [[it] * max(1, it.quantity) for it in point_items]
        seq: List[RoofLightItem] = []
        k = 0
        left = sum(len(q) for q in queues)
        while left > 0:
            q = queues[k % len(queues)]
            if q:
                seq.append(q.pop(0))
                left -= 1
            k += 1

        n_total = len(seq)
        if n_total == 0:
            return elements

        zone_len = z_max - z_min

        # Wolne pasy miedzy pasmami. SZEROKI pas jest dzielony na wiele kolumn,
        # zeby elementy pokrywaly cala szerokosc, a nie stalyy w jednej linii.
        bands = [(a, b) for (a, b) in free_segments if (b - a) > 0.8]
        if not bands:
            bands = list(free_segments)
        if not bands:
            return elements

        max_item_w = max(it.width for it in seq)
        min_col_w = max_item_w + 2 * EDGE_MARGIN

        # Uklad zblizony do kwadratowego
        rows = max(1, int(math.ceil(math.sqrt(n_total))))
        cols_wanted = max(1, int(math.ceil(n_total / rows)))

        # Pojemnosc kolumnowa kazdego pasa
        band_capacity = [max(1, int((b - a) / min_col_w)) if (b - a) >= min_col_w else 1
                         for (a, b) in bands]
        total_capacity = sum(band_capacity)
        cols = min(cols_wanted, total_capacity)
        rows = max(1, int(math.ceil(n_total / cols)))

        # Rozdanie kolumn miedzy pasy PROPORCJONALNIE do szerokosci pasa.
        # Kryterium: minimalizacja najwiekszej nieoswietlonej przerwy - kolumny
        # trafiaja tam, gdzie jest najwiecej wolnej szerokosci (najszersze pasy),
        # a przy nadwyzce kolumn kazdy pas dostaje co najmniej jedna.
        band_widths = [b - a for (a, b) in bands]
        S = len(bands)
        total_bw = sum(band_widths) or 1.0
        cols_per_band = [0] * S

        if cols >= S:
            for i in range(S):
                cols_per_band[i] = 1
            extra = cols - S
            order = sorted(range(S), key=lambda i: -band_widths[i])
            pos = 0
            while extra > 0 and any(cols_per_band[i] < band_capacity[i] for i in range(S)):
                i = order[pos % S]
                if cols_per_band[i] < band_capacity[i]:
                    cols_per_band[i] += 1
                    extra -= 1
                pos += 1
        else:
            for i in range(S):
                cols_per_band[i] = min(band_capacity[i],
                                       int(round(cols * band_widths[i] / total_bw)))
            while sum(cols_per_band) < cols:
                best = max(range(S),
                           key=lambda i: (band_capacity[i] - cols_per_band[i], band_widths[i]))
                if cols_per_band[best] >= band_capacity[best]:
                    break
                cols_per_band[best] += 1
            while sum(cols_per_band) > cols:
                best = max(range(S), key=lambda i: cols_per_band[i])
                cols_per_band[best] -= 1

        if sum(cols_per_band) == 0:
            cols_per_band[S // 2] = 1
        # Rzeczywiste pozycje kolumn: w kazdym pasie kolumny rozlozone rownomiernie
        col_slots: List[Tuple[float, float]] = []  # (x_center, dostepna_szerokosc)
        for (a, b), k in zip(bands, cols_per_band):
            if k <= 0:
                continue
            seg_w = (b - a) / k
            for j in range(k):
                col_slots.append((a + (j + 0.5) * seg_w, seg_w))
        if not col_slots:
            return elements

        cols = len(col_slots)
        rows = max(1, int(math.ceil(n_total / cols)))

        cell_l = zone_len / rows
        idx_item = 0
        for row in range(rows):
            cz = z_min + (row + 0.5) * cell_l
            for col in range(cols):
                if idx_item >= n_total:
                    break
                it = seq[idx_item]
                idx_item += 1

                col_center, col_w = col_slots[col]

                w = min(it.width, max(0.3, col_w - 2 * EDGE_MARGIN))
                l = min(it.length, max(0.3, cell_l - 2 * EDGE_MARGIN))
                cx = col_center

                y = grid.get_roof_height_at(cx) + ROOF_CLEARANCE
                ctype = "skylight" if it.item_type == "skylight" else "smoke_vent"
                thick = 0.35 if ctype == "skylight" else 0.40

                elements.append(Component3D(
                    type=ctype,
                    position=[cx, y, cz],
                    rotation=[0, 0, 0],
                    scale=[w, thick, l],
                    meta={"element_type": it.item_type, "item_id": it.item_id},
                ))

        return elements
