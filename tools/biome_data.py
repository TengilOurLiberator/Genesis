"""Catalogue of overworld country (BIOMES) and creatures (ANIMALS) for Eden, Minecraft Java 26.3.

Pure data plus a checker:

    D:\\voice-assistant\\.venv\\Scripts\\python.exe -I tools\\biome_data.py --check

The checker validates every block id (and block-state property) against work\\mcdata\\out\\reports\\blocks.json,
every feature id against data/minecraft/worldgen/feature/**.json inside work\\mcdata\\inner.jar, every entity id
against reports\\registries.json, and variant ids against the vanilla *_variant registries in the jar.

Things in 26.3 that differ from older versions (found by reading the jar, not from memory):
  * New biome dappled_forest (an autumn wood; its own surface rule makes patches of coarse_dirt) and sulfur_caves
    (underground, not used here). New tree features red_poplar / orange_poplar / yellow_poplar (+ _leaf_litter
    forms) and fallen_poplar_tree. New blocks/features: leaf_litter, wildflowers, bush, firefly_bush,
    short_dry_grass / tall_dry_grass (feature dry_grass), cactus_flower, closed_eyeblossom, pale_moss_*.
  * Feature ids live in worldgen/feature (the old "configured_feature" folder); corals are in a sub-folder
    (coral/tube_block ...) and are reached through warm_ocean_vegetation.
  * Farm animals (cow, pig, chicken) and frogs have a "variant" field (cold / temperate / warm); cats have
    "variant" with 11 values; wolves have 9 variants; all are stored as "minecraft:<name>" strings.
    Biome rules for those variants are in the jar tags spawns_cold_variant_farm_animals etc. and are
    copied below (COLD / WARM sets).
  * A /summon with extra NBT does NOT run finalizeSpawn, so every animal comes out with its DEFAULT variant
    (brown rabbit, white horse, red-blue parrot, red fox ...) unless the variant is written in `nbt`.
    Hence the explicit variant fields and the optional "variants" lists below.
  * Legacy integer fields still in use: Rabbit RabbitType, Horse Variant (colour + 256 * markings),
    Llama / Parrot / Axolotl Variant, TropicalFish Variant (packed), Sheep Color. String fields: Fox Type,
    Mooshroom Type, Salmon type, Panda MainGene / HiddenGene.

Extension to the requested schema: an ANIMALS entry may carry an optional "variants": a list of nbt strings
from which the integrator may pick one at random per creature (used when the biome has no by_biome entry).
"nbt" is always a valid single default.

Notes for the integrator
  * ground chances are per column and add up to at most 0.6 for each biome.
  * For biomes with deep_snow=True put decorations on columns first and only lay snow on columns that got none
    (a snow layer on top of a flower pops the flower off).
  * Iceberg features (frozen_ocean extras) ignore the y you give them and build at sea level.
  * Do not use pale_garden_vegetation / pale_oak_creaking: they spawn the hostile Creaking.
  * tree features here are single configured trees (oak, spruce ...), not the trees_* selectors, which carry
    their own placement modifiers.
"""
import json
import os
import re
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MC = os.path.join(ROOT, "work", "mcdata")
REG_PATH = os.path.join(MC, "out", "reports", "registries.json")
BLOCKS_PATH = os.path.join(MC, "out", "reports", "blocks.json")
JAR_PATH = os.path.join(MC, "inner.jar")

# ------------------------------------------------------------------ shared lists
FLOWERS_PLAIN = ["dandelion", "poppy", "azure_bluet", "oxeye_daisy", "cornflower", "red_tulip", "orange_tulip",
                 "white_tulip", "pink_tulip"]
FLOWERS_MEADOW = ["cornflower", "dandelion", "azure_bluet", "allium", "oxeye_daisy"]
FLOWERS_FOREST = ["dandelion", "poppy", "lily_of_the_valley", "oxeye_daisy"]
FLOWERS_RICH = ["allium", "poppy", "azure_bluet", "red_tulip", "orange_tulip", "white_tulip", "pink_tulip",
                "oxeye_daisy", "cornflower", "lily_of_the_valley", "dandelion"]
FLOWERS_WARM = ["dandelion", "poppy", "orange_tulip"]
FLOWERS_COLD = ["dandelion", "poppy", "azure_bluet"]
BADLANDS_BANDS = ["orange_terracotta", "terracotta", "yellow_terracotta", "terracotta", "brown_terracotta",
                  "orange_terracotta", "white_terracotta", "light_gray_terracotta", "red_terracotta", "terracotta"]


def _biome(bare, green, under, look, deep_snow=False, trees=(), spacing=0, chance=0.0, ground=(), extras=(),
           terraces=None):
    d = {"bare": bare, "green": green, "under": under, "deep_snow": deep_snow, "trees": list(trees),
         "tree_spacing": spacing, "tree_chance": chance, "ground": list(ground), "extras": list(extras),
         "look": look}
    if terraces is not None:
        d["terraces"] = list(terraces)
    return d


# ------------------------------------------------------------------ Part 1: BIOMES
BIOMES = {
    "plains": _biome(
        "dirt", "grass_block", "dirt",
        "Wide open country of short green grass under a big sky, with a lone tree here and there and small flowers dotted about.",
        trees=[("oak", 5), ("fancy_oak", 1), ("oak_bees_005", 1)], spacing=12, chance=0.04,
        ground=[(0.28, "short_grass"), (0.06, FLOWERS_PLAIN), (0.04, "feature:tall_grass"), (0.002, "pumpkin")],
        extras=[(0.0008, "feature:fallen_oak_tree")]),
    "sunflower_plains": _biome(
        "dirt", "grass_block", "dirt",
        "Wide open grassland where tall plants with great golden faces on thick stems stand in drifts, all turned toward the sun.",
        trees=[("oak", 5), ("fancy_oak", 1)], spacing=14, chance=0.03,
        ground=[(0.26, "short_grass"), (0.09, "feature:sunflower"), (0.04, FLOWERS_PLAIN), (0.03, "feature:tall_grass")]),
    "meadow": _biome(
        "dirt", "grass_block", "dirt",
        "High soft pastures of green grass and many small flowers in bright colours, with a few pale-trunked trees and the hum of small winged creatures.",
        trees=[("super_birch_bees", 1), ("fancy_oak_bees", 1)], spacing=14, chance=0.03,
        ground=[(0.30, "short_grass"), (0.07, FLOWERS_MEADOW), (0.05, "feature:tall_grass"), (0.05, "feature:wildflower")]),
    "forest": _biome(
        "dirt", "grass_block", "dirt",
        "Land thick with tall trees whose leaves make a green roof, with soft grass and a few flowers on the ground below.",
        trees=[("oak", 4), ("birch", 2), ("fancy_oak", 1), ("oak_bees_005", 1), ("birch_bees_005", 1)],
        spacing=6, chance=0.5,
        ground=[(0.18, "short_grass"), (0.05, FLOWERS_FOREST), (0.03, "fern"), (0.008, ["red_mushroom", "brown_mushroom"]),
                (0.004, "feature:bush")],
        extras=[(0.0015, "feature:fallen_oak_tree"), (0.0008, "feature:fallen_birch_tree")]),
    "flower_forest": _biome(
        "dirt", "grass_block", "dirt",
        "A wood so full of flowers of every colour that the ground looks painted, with tall flowering plants as high as a person between the trees.",
        trees=[("oak_bees_002", 3), ("birch_bees_002", 2), ("fancy_oak_bees_002", 1)], spacing=7, chance=0.35,
        ground=[(0.22, FLOWERS_RICH), (0.16, "short_grass"), (0.03, "feature:tall_grass")],
        extras=[(0.002, "feature:forest_flowers"), (0.0008, "feature:fallen_birch_tree")]),
    "birch_forest": _biome(
        "dirt", "grass_block", "dirt",
        "A bright wood of slender pale trees with white bark marked in black, and light falling softly through thin leaves.",
        trees=[("birch", 8), ("birch_bees_0002", 1), ("fancy_oak", 1)], spacing=6, chance=0.5,
        ground=[(0.22, "short_grass"), (0.04, "feature:wildflower"), (0.03, FLOWERS_FOREST), (0.03, "feature:tall_grass")],
        extras=[(0.0015, "feature:fallen_birch_tree")]),
    "old_growth_birch_forest": _biome(
        "dirt", "grass_block", "dirt",
        "A wood of very tall, slender pale trees with white bark, standing close, so that their tops make a high green roof.",
        trees=[("birch_tall", 5), ("super_birch_bees_0002", 1), ("birch", 1)], spacing=6, chance=0.55,
        ground=[(0.22, "short_grass"), (0.04, "feature:wildflower"), (0.03, FLOWERS_FOREST), (0.03, "feature:tall_grass")],
        extras=[(0.0015, "feature:fallen_super_birch_tree")]),
    "dark_forest": _biome(
        "dirt", "grass_block", "dirt",
        "A gloomy wood of huge thick trees whose crowns join together so that little light reaches the ground, with giant mushrooms as tall as trees.",
        trees=[("dark_oak", 5), ("dark_oak_leaf_litter", 3), ("oak_leaf_litter", 1), ("birch_leaf_litter", 1)],
        spacing=6, chance=0.85,
        ground=[(0.10, "short_grass"), (0.03, ["red_mushroom", "brown_mushroom"]), (0.03, "feature:leaf_litter"),
                (0.02, "feature:bush")],
        extras=[(0.004, "feature:huge_red_mushroom"), (0.003, "feature:huge_brown_mushroom"),
                (0.001, "feature:fallen_oak_tree")]),
    "dappled_forest": _biome(
        "dirt", "grass_block", "dirt",
        "A wood in autumn, where the leaves have turned red, orange and yellow, and the ground is covered in fallen leaves.",
        trees=[("red_poplar_leaf_litter", 200), ("orange_poplar_leaf_litter", 240), ("yellow_poplar_leaf_litter", 90),
               ("spruce", 27)], spacing=6, chance=0.5,
        ground=[(0.18, "feature:leaf_litter"), (0.15, "short_grass"), (0.03, "feature:red_shrub"),
                (0.01, "brown_mushroom"), (0.03, "feature:dry_grass")],
        extras=[(0.004, "feature:fallen_poplar_tree")]),
    "pale_garden": _biome(
        "dirt", "grass_block", "dirt",
        "A hushed grey-white wood of crooked pale trees and pale moss, where flowers close up like shut eyes and the air feels watchful.",
        trees=[("pale_oak", 1)], spacing=6, chance=0.6,
        ground=[(0.12, "short_grass"), (0.10, "feature:pale_moss_vegetation"), (0.03, "closed_eyeblossom"),
                (0.01, "feature:bush")],
        extras=[(0.006, "feature:pale_moss_patch")]),
    "cherry_grove": _biome(
        "dirt", "grass_block", "dirt",
        "A gentle hillside of trees with twisted trunks, all covered in pale pink blossom that drifts down onto pink-strewn grass.",
        trees=[("cherry", 8), ("cherry_bees_005", 1)], spacing=7, chance=0.8,
        ground=[(0.14, "pink_petals"), (0.12, "short_grass"), (0.04, FLOWERS_MEADOW), (0.03, "feature:wildflower")]),
    "taiga": _biome(
        "dirt", "grass_block", "dirt",
        "Cold damp woodland of dark, narrow, pointed evergreen trees, with ferns, mossy stones and low berry bushes among them.",
        trees=[("spruce", 6), ("pine", 3)], spacing=6, chance=0.5,
        ground=[(0.20, "feature:taiga_grass"), (0.03, "feature:large_fern"), (0.012, "sweet_berry_bush[age=3]"),
                (0.01, ["red_mushroom", "brown_mushroom"])],
        extras=[(0.0015, "feature:fallen_spruce_tree"), (0.0008, "feature:forest_rock")]),
    "old_growth_pine_taiga": _biome(
        "dirt", "podzol", "dirt",
        "A dim cold forest of giant evergreen trees with thick trunks, over dark ash-coloured soil, with ferns and mushrooms.",
        trees=[("mega_pine", 3), ("pine", 3), ("spruce", 3), ("mega_spruce", 1)], spacing=8, chance=0.5,
        ground=[(0.12, "feature:taiga_grass"), (0.03, "feature:large_fern"), (0.03, ["red_mushroom", "brown_mushroom"]),
                (0.01, "sweet_berry_bush[age=3]")],
        extras=[(0.002, "feature:forest_rock"), (0.002, "feature:fallen_spruce_tree")]),
    "old_growth_spruce_taiga": _biome(
        "dirt", "podzol", "dirt",
        "A dim cold forest of giant dark evergreen trees with thick trunks, with moss, ferns and mushrooms on the dark ground.",
        trees=[("spruce", 3), ("mega_spruce", 3), ("pine", 3)], spacing=8, chance=0.5,
        ground=[(0.12, "feature:taiga_grass"), (0.03, "feature:large_fern"), (0.03, ["red_mushroom", "brown_mushroom"]),
                (0.01, "sweet_berry_bush[age=3]")],
        extras=[(0.002, "feature:forest_rock"), (0.002, "feature:fallen_spruce_tree"), (0.003, "feature:moss_patch")]),
    "snowy_taiga": _biome(
        "dirt", "grass_block", "dirt",
        "A cold woodland of dark pointed evergreen trees weighed down with snow, over ground that lies deep in white.",
        deep_snow=True, trees=[("spruce", 6), ("pine", 2)], spacing=6, chance=0.45,
        ground=[(0.05, "fern"), (0.012, "sweet_berry_bush[age=3]"), (0.04, "feature:large_fern")],
        extras=[(0.0015, "feature:fallen_spruce_tree")]),
    "snowy_plains": _biome(
        "dirt", "grass_block", "dirt",
        "A wide flat country covered in white snow, with only a few dark pointed trees standing alone.",
        deep_snow=True, trees=[("spruce", 1)], spacing=14, chance=0.04,
        ground=[],
        extras=[(0.0015, "feature:ice_patch"), (0.0008, "feature:fallen_spruce_tree")]),
    "ice_spikes": _biome(
        "snow_block", None, "dirt",
        "A white frozen plain from which tall sharp spikes of clear blue-white ice rise like giant thorns.",
        extras=[(0.012, "feature:ice_spike"), (0.003, "feature:ice_patch")]),
    "grove": _biome(
        "snow_block", None, "dirt",
        "A steep snowy hillside of dark pointed trees standing in deep soft snow, just below the high white mountains.",
        trees=[("spruce", 3), ("pine", 1)], spacing=7, chance=0.5,
        extras=[(0.001, "feature:fallen_spruce_tree")]),
    "snowy_slopes": _biome(
        "snow_block", None, "stone",
        "Steep mountain sides buried in deep white snow, bare of trees, with grey rock showing through where it is too steep for snow to rest.",
        extras=[(0.002, "feature:ice_patch")]),
    "frozen_peaks": _biome(
        "snow_block", None, "packed_ice",
        "Great mountain tops of ice and snow, glittering blue and white, where nothing grows.",
        extras=[(0.012, "feature:ice_patch")]),
    "jagged_peaks": _biome(
        "snow_block", None, "stone",
        "Sharp, steep summits of grey rock with white snow upon their points, so high that clouds pass below them."),
    "stony_peaks": _biome(
        "stone", None, "stone",
        "High bare mountaintops of grey and white stone, with no plants at all."),
    "windswept_hills": _biome(
        "dirt", "grass_block", "dirt",
        "Rough high hills with steep sides of bare stone, bent trees and patches of grass among the rocks.",
        trees=[("spruce", 5), ("oak", 1), ("fancy_oak", 1)], spacing=12, chance=0.12,
        ground=[(0.20, "short_grass"), (0.02, FLOWERS_COLD), (0.01, "feature:bush")],
        extras=[(0.003, "feature:forest_rock")]),
    "windswept_forest": _biome(
        "dirt", "grass_block", "dirt",
        "Rough high hills, steep and stony, with dark pointed trees growing thick in the shelter of the rocks.",
        trees=[("spruce", 6), ("oak", 1), ("fancy_oak", 1)], spacing=7, chance=0.5,
        ground=[(0.20, "short_grass"), (0.03, "fern"), (0.02, FLOWERS_COLD)],
        extras=[(0.003, "feature:forest_rock"), (0.001, "feature:fallen_spruce_tree")]),
    "windswept_gravelly_hills": _biome(
        "gravel", None, "stone",
        "Bare rough hills of loose stones and gravel, steep and grey, with only a few small plants.",
        trees=[("spruce", 1)], spacing=14, chance=0.05),
    "savanna": _biome(
        "dirt", "grass_block", "dirt",
        "Warm, dry, yellow-green grassland with flat-topped trees that spread their branches wide and crooked.",
        trees=[("acacia", 8), ("oak", 1)], spacing=11, chance=0.5,
        ground=[(0.42, "short_grass"), (0.05, "feature:tall_grass"), (0.015, FLOWERS_WARM)]),
    "savanna_plateau": _biome(
        "dirt", "grass_block", "dirt",
        "A high flat-topped tableland of dry yellow-green grass with a few wide crooked trees, ending in sudden cliffs.",
        trees=[("acacia", 8), ("oak", 1)], spacing=12, chance=0.4,
        ground=[(0.42, "short_grass"), (0.04, "feature:tall_grass"), (0.015, FLOWERS_WARM)]),
    "windswept_savanna": _biome(
        "dirt", "grass_block", "dirt",
        "Dry rough hills of dust-coloured soil and stone with a few crooked flat-topped trees and tufts of dry grass.",
        trees=[("acacia", 1)], spacing=12, chance=0.3,
        ground=[(0.30, "short_grass"), (0.03, "feature:dry_grass"), (0.02, FLOWERS_WARM)],
        extras=[(0.002, "feature:forest_rock")]),
    "desert": _biome(
        "sand", None, "sand",
        "Hot dry land of loose pale yellow sand in long drifts, with prickly green plants that have no leaves, and dry dead brush.",
        ground=[(0.05, "feature:dry_grass"), (0.015, "dead_bush"), (0.012, "feature:cactus")],
        extras=[(0.0008, "feature:desert_well")]),
    "badlands": _biome(
        "red_sand", None, "terracotta",
        "A red, dry land of hills and cliffs banded in stripes of orange, red, yellow, white and brown clay, with almost no plants.",
        ground=[(0.03, "feature:dry_grass"), (0.012, "dead_bush"), (0.005, "feature:cactus")],
        terraces=BADLANDS_BANDS),
    "wooded_badlands": _biome(
        "dirt", "grass_block", "terracotta",
        "High banded cliffs of red, orange and yellow clay with green grass and a few trees growing on the tops.",
        trees=[("oak", 1)], spacing=7, chance=0.45,
        ground=[(0.20, "short_grass"), (0.03, "feature:dry_grass"), (0.01, "dead_bush")],
        terraces=BADLANDS_BANDS),
    "eroded_badlands": _biome(
        "red_sand", None, "terracotta",
        "A red land worn by wind and rain into tall thin pillars and steep spires of clay in stripes of orange, red and white.",
        ground=[(0.02, "feature:dry_grass"), (0.01, "dead_bush")],
        terraces=BADLANDS_BANDS),
    "jungle": _biome(
        "dirt", "grass_block", "dirt",
        "Hot wet forest so thick with giant trees, vines and ferns that the air is green and heavy and you cannot see far.",
        trees=[("jungle_tree_no_vine", 5), ("jungle_tree", 2), ("mega_jungle_tree", 1), ("jungle_bush", 3)],
        spacing=6, chance=1.0,
        ground=[(0.26, "feature:grass_jungle"), (0.10, "fern"), (0.03, "feature:bamboo_no_podzol"), (0.010, "melon")],
        extras=[(0.003, "feature:fallen_jungle_tree")]),
    "sparse_jungle": _biome(
        "dirt", "grass_block", "dirt",
        "Hot wet woodland, open enough to walk through, of tall leafy trees, bushes and thick ferns.",
        trees=[("jungle_tree_no_vine", 2), ("jungle_bush", 5), ("fancy_oak", 1)], spacing=9, chance=0.4,
        ground=[(0.30, "feature:grass_jungle"), (0.02, FLOWERS_WARM), (0.006, "melon")],
        extras=[(0.002, "feature:fallen_jungle_tree")]),
    "bamboo_jungle": _biome(
        "dirt", "podzol", "dirt",
        "A hot wet forest filled with thousands of tall, straight green canes, standing close like a wall.",
        trees=[("jungle_tree_no_vine", 1), ("mega_jungle_tree", 1), ("jungle_bush", 3)], spacing=9, chance=0.3,
        ground=[(0.09, "feature:bamboo_no_podzol"), (0.05, "feature:bamboo_some_podzol"), (0.20, "feature:grass_jungle"),
                (0.05, "fern")],
        extras=[(0.004, "feature:bamboo_vegetation")]),
    "swamp": _biome(
        "dirt", "grass_block", "dirt",
        "Low wet ground of dark murky pools and mud under crooked trees hung with vines, with blue flowers on the banks.",
        trees=[("swamp_oak", 1)], spacing=8, chance=0.3,
        ground=[(0.20, "short_grass"), (0.03, "blue_orchid"), (0.02, ["red_mushroom", "brown_mushroom"]),
                (0.01, "dead_bush"), (0.01, "feature:firefly_bush")]),
    "mangrove_swamp": _biome(
        "mud", None, "mud",
        "A drowned wood of trees standing on tall tangled roots in warm soft mud and shallow water.",
        trees=[("mangrove", 3), ("tall_mangrove", 2)], spacing=6, chance=0.5,
        ground=[(0.12, "short_grass"), (0.01, "dead_bush"), (0.01, "feature:firefly_bush")]),
    "mushroom_fields": _biome(
        "dirt", "mycelium", "dirt",
        "A strange pale purple-grey land with no trees, where giant mushrooms taller than a house grow from soft threaded soil.",
        ground=[(0.04, "red_mushroom"), (0.04, "brown_mushroom")],
        extras=[(0.010, "feature:mushroom_island_vegetation")]),
    "beach": _biome(
        "sand", None, "sand",
        "A smooth band of pale warm sand where the land ends and the water begins."),
    "snowy_beach": _biome(
        "sand", None, "sand",
        "A pale shore of sand dusted with snow, where the cold water meets the land.",
        deep_snow=True),
    "stony_shore": _biome(
        "stone", None, "stone",
        "A rough shore of grey rock and stones where cold water breaks on the land, with no sand and no plants."),
    "river": _biome(
        "sand", None, "gravel",
        "A moving stretch of water between two banks, flowing over a sandy and stony bottom with green weed swaying under it.",
        ground=[(0.20, "feature:seagrass_short"), (0.10, "feature:seagrass_mid")]),
    "frozen_river": _biome(
        "gravel", None, "gravel",
        "A river frozen over, its surface a sheet of pale ice, with cold water moving slowly beneath."),
    "warm_ocean": _biome(
        "sand", None, "sand",
        "Clear, shallow, warm water of bright blue-green, with colourful stony growths shaped like branches, fans and tubes on the bottom.",
        ground=[(0.20, "feature:seagrass_short"), (0.05, "feature:seagrass_tall"), (0.008, "feature:sea_pickle")],
        extras=[(0.020, "feature:warm_ocean_vegetation")]),
    "lukewarm_ocean": _biome(
        "sand", None, "sand",
        "Mild deep blue water over a sandy bottom, with long green weed and spiky green tufts growing up from the floor.",
        ground=[(0.20, "feature:seagrass_short"), (0.04, "feature:seagrass_tall"), (0.05, "feature:kelp"),
                (0.01, "feature:sea_pickle")]),
    "ocean": _biome(
        "sand", None, "sand",
        "The great water, deep blue, stretching to the edge of sight, with long swaying weed rooted on the floor.",
        ground=[(0.15, "feature:seagrass_short"), (0.05, "feature:seagrass_tall"), (0.06, "feature:kelp")]),
    "cold_ocean": _biome(
        "gravel", None, "gravel",
        "Cold grey-blue deep water with thick forests of tall slimy brown-green weed rooted on the stony floor.",
        ground=[(0.10, "feature:seagrass_mid"), (0.10, "feature:kelp")]),
    "frozen_ocean": _biome(
        "gravel", None, "gravel",
        "The great water frozen near its surface, with huge floating mountains of white and blue ice drifting in it.",
        extras=[(0.0006, "feature:iceberg_packed"), (0.0003, "feature:iceberg_blue")]),
}


# ------------------------------------------------------------------ Part 2: ANIMALS
def tf(size, pattern, base, pattern_colour):
    """Packed TropicalFish Variant: size (0 small / 1 large), pattern 0-5, then dye ids of body and pattern."""
    return size | (pattern << 8) | (base << 16) | (pattern_colour << 24)


def horse(colour, markings):
    """Horse Variant: colour 0-6 (white creamy chestnut brown black gray dark_brown) + 256 * markings 0-4."""
    return colour + 256 * markings


# biome sets that decide the farm-animal and frog variant (copied from the jar's worldgen/biome tags,
# restricted to the biomes of this catalogue)
COLD = ["snowy_plains", "ice_spikes", "frozen_peaks", "jagged_peaks", "snowy_slopes", "frozen_ocean", "grove",
        "frozen_river", "snowy_taiga", "snowy_beach", "cold_ocean", "old_growth_pine_taiga", "old_growth_spruce_taiga",
        "taiga", "windswept_forest", "windswept_gravelly_hills", "windswept_hills", "stony_peaks", "dappled_forest"]
WARM = ["desert", "warm_ocean", "jungle", "sparse_jungle", "bamboo_jungle", "savanna", "savanna_plateau",
        "windswept_savanna", "badlands", "eroded_badlands", "wooded_badlands", "mangrove_swamp", "lukewarm_ocean"]


def _temp(biomes):
    """by_biome overrides giving cold / warm variants of cow, pig, chicken to the right biomes."""
    out = {}
    for b in biomes:
        if b in COLD:
            out[b] = 'variant:"minecraft:cold"'
        elif b in WARM:
            out[b] = 'variant:"minecraft:warm"'
    return out


_FARM_BIOMES = ["plains", "sunflower_plains", "forest", "flower_forest", "birch_forest", "dark_forest", "dappled_forest",
                "taiga", "snowy_taiga", "windswept_hills", "savanna", "swamp", "jungle", "wooded_badlands"]
_SHEEP_COLOURS = ["Color:0b"] * 10 + ["Color:8b", "Color:7b", "Color:15b", "Color:12b", "Color:6b"]
_TF = [tf(0, 0, 1, 0), tf(0, 1, 11, 4), tf(0, 2, 4, 14), tf(0, 3, 14, 0), tf(0, 4, 9, 6), tf(0, 5, 4, 11),
       tf(1, 0, 3, 4), tf(1, 1, 6, 7), tf(1, 2, 10, 0), tf(1, 3, 14, 4), tf(1, 4, 5, 15), tf(1, 5, 11, 3)]
_CATS = ["all_black", "black", "british_shorthair", "calico", "jellie", "persian", "ragdoll", "red", "siamese", "tabby",
         "white"]
_PANDA = [("normal", "normal"), ("normal", "normal"), ("lazy", "lazy"), ("worried", "worried"), ("playful", "playful"),
          ("brown", "brown"), ("weak", "weak")]
_CAT_BIOMES = ["plains", "sunflower_plains", "meadow", "taiga", "savanna", "desert", "swamp"]
_PUFF_FISH = ["warm_ocean", "lukewarm_ocean"]

ANIMALS = {
    # ---------------------------------------------------------------- cattle: grazing herd animals (day six)
    "cow": {
        "look": "large and heavy, four legs, a patched hide, horns, a deep lowing voice",
        "group": "cattle", "biomes": _FARM_BIOMES, "count": 14, "where": "land",
        "nbt": 'variant:"minecraft:temperate"', "by_biome": _temp(_FARM_BIOMES)},
    "mooshroom": {
        "look": "like a large patched grazing beast, but red or brown with pale spots, and with little mushrooms growing on its back",
        "group": "cattle", "biomes": ["mushroom_fields"], "count": 6, "where": "land",
        "nbt": 'Type:"red"', "by_biome": {},
        "variants": ['Type:"red"', 'Type:"red"', 'Type:"brown"']},
    "pig": {
        "look": "pink, stout, a flat snout, grunts, roots in the ground",
        "group": "cattle", "biomes": _FARM_BIOMES + ["cherry_grove"], "count": 12, "where": "land",
        "nbt": 'variant:"minecraft:temperate"', "by_biome": _temp(_FARM_BIOMES + ["cherry_grove"])},
    "sheep": {
        "look": "round and woolly, four thin legs, bleats, eats the grass",
        "group": "cattle", "biomes": _FARM_BIOMES + ["meadow", "cherry_grove"], "count": 18, "where": "land",
        "nbt": "Color:0b", "by_biome": {}, "variants": _SHEEP_COLOURS},
    "horse": {
        "look": "tall and swift, long legs, a mane and a long tail",
        "group": "cattle", "biomes": ["plains", "sunflower_plains", "meadow", "savanna", "savanna_plateau"],
        "count": 10, "where": "land",
        "nbt": "Variant:%d" % horse(3, 0), "by_biome": {},
        "variants": ["Variant:%d" % horse(c, m) for c, m in
                     [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0), (5, 0), (6, 0), (0, 1), (3, 2), (2, 3), (4, 4), (5, 3)]]},
    "donkey": {
        "look": "stocky and sure-footed, grey-brown, with very long ears and a loud braying voice",
        "group": "cattle", "biomes": ["plains", "sunflower_plains", "meadow", "savanna", "savanna_plateau", "windswept_savanna"],
        "count": 6, "where": "land", "nbt": "", "by_biome": {}},
    "mule": {
        "look": "strong and patient, bigger than the long-eared one but with a tall swift beast's build, with long ears and a harsh voice, and it has no young",
        "group": "cattle", "biomes": ["plains", "savanna", "savanna_plateau"],
        "count": 4, "where": "land", "nbt": "", "by_biome": {}},
    "goat": {
        "look": "sure-footed, horned, thick-coated, leaps on steep rock and sometimes lowers its head to charge",
        "group": "cattle", "biomes": ["jagged_peaks", "frozen_peaks", "snowy_slopes", "grove"],
        "count": 10, "where": "land", "nbt": "IsScreamingGoat:0b", "by_biome": {},
        "variants": ["IsScreamingGoat:0b"] * 9 + ["IsScreamingGoat:1b"]},
    # ---------------------------------------------------------------- fowl: birds and winged things of the air (day five)
    "chicken": {
        "look": "a small bird that walks more than it flies, clucks, pecks at seeds",
        "group": "fowl", "biomes": _FARM_BIOMES, "count": 14, "where": "land",
        "nbt": 'variant:"minecraft:temperate"', "by_biome": _temp(_FARM_BIOMES)},
    "parrot": {
        "look": "a bright bird of many colours that flies and copies sounds",
        "group": "fowl", "biomes": ["jungle", "bamboo_jungle", "sparse_jungle"], "count": 20, "where": "air",
        "nbt": "Variant:0", "by_biome": {}, "variants": ["Variant:0", "Variant:1", "Variant:2", "Variant:3", "Variant:4"]},
    "bat": {
        "look": "a tiny dark winged creature of dusk and gloom, with no feathers, that flutters in jerks and squeaks",
        "group": "fowl", "biomes": ["dark_forest", "pale_garden", "windswept_hills"], "count": 8, "where": "air",
        "nbt": "", "by_biome": {}},
    "allay": {
        "look": "a small pale-blue glowing spirit with delicate wings and a high happy hum, that hovers and follows those it likes",
        "group": "fowl", "biomes": ["meadow", "cherry_grove", "flower_forest"], "count": 6, "where": "air",
        "nbt": "", "by_biome": {}},
    "happy_ghast": {
        "look": "an enormous pale floating creature like a great soft cloud with a gentle face and trailing arms, that drifts slowly and calmly through the sky",
        "group": "fowl", "biomes": ["meadow", "plains", "sunflower_plains", "cherry_grove"], "count": 4, "where": "air",
        "nbt": "", "by_biome": {}},
    # ---------------------------------------------------------------- creeping: small ground creatures and insects (day six)
    "rabbit": {
        "look": "small, long ears, hops, very quick",
        "group": "creeping",
        "biomes": ["meadow", "flower_forest", "cherry_grove", "dappled_forest", "taiga", "old_growth_pine_taiga",
                   "old_growth_spruce_taiga", "snowy_taiga", "snowy_plains", "ice_spikes", "snowy_slopes", "grove",
                   "desert"],
        "count": 16, "where": "land", "nbt": "RabbitType:0",
        "by_biome": {"snowy_taiga": "RabbitType:1", "snowy_plains": "RabbitType:1", "ice_spikes": "RabbitType:1",
                     "snowy_slopes": "RabbitType:1", "grove": "RabbitType:1", "desert": "RabbitType:4"},
        "variants": ["RabbitType:0", "RabbitType:0", "RabbitType:2", "RabbitType:5"]},
    "frog": {
        "look": "small, wet skin, leaps, croaks, a long tongue",
        "group": "creeping", "biomes": ["swamp", "mangrove_swamp", "jungle", "river", "frozen_river"], "count": 12,
        "where": "shore", "nbt": 'variant:"minecraft:temperate"',
        "by_biome": {"mangrove_swamp": 'variant:"minecraft:warm"', "jungle": 'variant:"minecraft:warm"',
                     "frozen_river": 'variant:"minecraft:cold"'}},
    "turtle": {
        "look": "carries a round shell on its back, slow on land, graceful in water",
        "group": "creeping", "biomes": ["beach"], "count": 8, "where": "shore", "nbt": "", "by_biome": {}},
    "armadillo": {
        "look": "small, covered in hard plates, rolls into a ball",
        "group": "creeping",
        "biomes": ["savanna", "savanna_plateau", "windswept_savanna", "badlands", "wooded_badlands", "eroded_badlands"],
        "count": 8, "where": "land", "nbt": "", "by_biome": {}},
    "bee": {
        "look": "tiny, striped, hums, goes from flower to flower",
        "group": "creeping", "biomes": ["meadow", "flower_forest", "sunflower_plains", "plains", "forest", "cherry_grove"],
        "count": 14, "where": "air", "nbt": "", "by_biome": {}},
    # ---------------------------------------------------------------- beast: wild beasts of the earth (day six)
    "llama": {
        "look": "tall with a long woolly neck, proud, sometimes spits",
        "group": "beast",
        "biomes": ["windswept_hills", "windswept_forest", "windswept_gravelly_hills", "savanna_plateau", "stony_peaks"],
        "count": 8, "where": "land", "nbt": "Variant:0", "by_biome": {},
        "variants": ["Variant:0", "Variant:1", "Variant:2", "Variant:3"]},
    "camel": {
        "look": "very tall, a hump on its back, long legs, kneels to rest",
        "group": "beast", "biomes": ["desert", "savanna"], "count": 6, "where": "land", "nbt": "", "by_biome": {}},
    "wolf": {
        "look": "lean and grey-furred, long-legged, with a sharp muzzle and upright ears, hunts in packs, howls",
        "group": "beast",
        "biomes": ["forest", "grove", "old_growth_pine_taiga", "old_growth_spruce_taiga", "savanna_plateau", "snowy_taiga",
                   "sparse_jungle", "taiga", "wooded_badlands"],
        "count": 12, "where": "land", "nbt": 'variant:"minecraft:pale"',
        "by_biome": {"forest": 'variant:"minecraft:woods"', "grove": 'variant:"minecraft:snowy"',
                     "old_growth_pine_taiga": 'variant:"minecraft:black"',
                     "old_growth_spruce_taiga": 'variant:"minecraft:chestnut"',
                     "savanna_plateau": 'variant:"minecraft:spotted"', "snowy_taiga": 'variant:"minecraft:ashen"',
                     "sparse_jungle": 'variant:"minecraft:rusty"', "taiga": 'variant:"minecraft:pale"',
                     "wooded_badlands": 'variant:"minecraft:striped"'}},
    "fox": {
        "look": "small and quick, rust-red or white, with a thick bushy tail, pointed ears and a sharp face, sleeps curled up by day",
        "group": "beast",
        "biomes": ["dappled_forest", "grove", "old_growth_pine_taiga", "old_growth_spruce_taiga", "snowy_taiga", "taiga"],
        "count": 8, "where": "land", "nbt": 'Type:"red"',
        "by_biome": {"grove": 'Type:"snow"', "snowy_taiga": 'Type:"snow"'}},
    "cat": {
        "look": "small and soft-pawed, with a long tail and bright eyes, walks silently, purrs, and sits and watches",
        "group": "beast", "biomes": _CAT_BIOMES, "count": 8, "where": "land",
        "nbt": 'variant:"minecraft:tabby"', "by_biome": {"swamp": 'variant:"minecraft:all_black"'},
        "variants": ['variant:"minecraft:%s"' % c for c in _CATS if c != "all_black"]},
    "ocelot": {
        "look": "a lean spotted hunter of the dense hot forest, yellow with dark markings, shy and quick, creeping low among the leaves",
        "group": "beast", "biomes": ["jungle", "bamboo_jungle", "sparse_jungle"], "count": 6, "where": "land",
        "nbt": "", "by_biome": {}},
    "panda": {
        "look": "big, round, black and white, sits and eats, rolls over",
        "group": "beast", "biomes": ["jungle", "bamboo_jungle"], "count": 6, "where": "land",
        "nbt": 'MainGene:"normal",HiddenGene:"normal"', "by_biome": {},
        "variants": ['MainGene:"%s",HiddenGene:"%s"' % g for g in _PANDA]},
    "polar_bear": {
        "look": "huge, thick-furred and white, heavy-pawed, at home in ice and cold water, gentle unless its young are threatened",
        "group": "beast", "biomes": ["snowy_plains", "ice_spikes", "frozen_ocean"], "count": 5, "where": "land",
        "nbt": "", "by_biome": {}},
    "sniffer": {
        "look": "an ancient huge mossy creature, green-backed and slow, with a long wide nose that it presses into the soil to dig up seeds",
        "group": "beast", "biomes": ["plains", "meadow", "flower_forest", "dappled_forest"], "count": 4, "where": "land",
        "nbt": "", "by_biome": {}},
    # ---------------------------------------------------------------- sea: creatures of the waters (day five)
    "cod": {
        "look": "a plain brown fish that swims in shoals",
        "group": "sea", "biomes": ["ocean", "cold_ocean", "lukewarm_ocean"], "count": 30, "where": "water",
        "nbt": "", "by_biome": {}},
    "salmon": {
        "look": "a long red-sided fish, strong, leaps",
        "group": "sea", "biomes": ["river", "frozen_river", "cold_ocean", "frozen_ocean"], "count": 24, "where": "water",
        "nbt": 'type:"medium"', "by_biome": {},
        "variants": ['type:"small"', 'type:"medium"', 'type:"medium"', 'type:"medium"', 'type:"medium"', 'type:"large"']},
    "tropical_fish": {
        "look": "a small fish in bright colours and patterns",
        "group": "sea", "biomes": ["warm_ocean", "lukewarm_ocean", "mangrove_swamp"], "count": 36, "where": "water",
        "nbt": "Variant:%d" % _TF[0], "by_biome": {}, "variants": ["Variant:%d" % v for v in _TF]},
    "pufferfish": {
        "look": "a small round fish that swells into a prickly ball when something comes near",
        "group": "sea", "biomes": _PUFF_FISH, "count": 20, "where": "water", "nbt": "", "by_biome": {}},
    "squid": {
        "look": "soft, dark, many arms, squirts black ink",
        "group": "sea", "biomes": ["ocean", "cold_ocean", "lukewarm_ocean", "warm_ocean", "frozen_ocean", "river"],
        "count": 10, "where": "water", "nbt": "", "by_biome": {}},
    "glow_squid": {
        "look": "like the soft many-armed ink-squirter, but it glows blue-green in the dark water",
        "group": "sea", "biomes": ["ocean", "lukewarm_ocean", "warm_ocean"], "count": 6, "where": "water",
        "nbt": "", "by_biome": {}},
    "dolphin": {
        "look": "sleek and grey, leaps out of the water, clicks and whistles, playful",
        "group": "sea", "biomes": ["ocean", "lukewarm_ocean", "warm_ocean"], "count": 8, "where": "water",
        "nbt": "", "by_biome": {}},
    "nautilus": {
        "look": "a swimmer in a great coiled shell, with trailing arms",
        "group": "sea", "biomes": ["ocean", "cold_ocean", "lukewarm_ocean", "warm_ocean", "frozen_ocean"], "count": 6,
        "where": "water", "nbt": "", "by_biome": {}},
    "axolotl": {
        "look": "a small smiling water creature with a flat face, four stubby legs, a flat tail and feathery gills like branches at the sides of its head",
        "group": "sea", "biomes": ["swamp", "mangrove_swamp", "river"], "count": 8, "where": "water",
        "nbt": "Variant:0", "by_biome": {}, "variants": ["Variant:0", "Variant:1", "Variant:2", "Variant:3", "Variant:4"]},
    "tadpole": {
        "look": "a tiny dark swimming speck with a wriggling tail, that will one day grow legs",
        "group": "sea", "biomes": ["swamp", "mangrove_swamp", "river"], "count": 10, "where": "water",
        "nbt": "", "by_biome": {}},
}

# ------------------------------------------------------------------ everything else in the entity registry, and why not
_EXCLUDE_GROUPS = {
    "hostile monster (attacks unprovoked or is undead)": (
        "blaze bogged breeze cave_spider creaking creeper drowned elder_guardian ender_dragon enderman endermite evoker "
        "ghast giant guardian husk illusioner magma_cube parched phantom pillager ravager shulker silverfish skeleton "
        "slime spider stray sulfur_cube vex vindicator warden witch wither wither_skeleton zombie zombie_villager"),
    "nether creature (not overworld; piglins and hoglins are hostile)": (
        "hoglin piglin piglin_brute strider zoglin zombified_piglin"),
    "undead or variant mount, not a natural animal": (
        "camel_husk skeleton_horse trader_llama zombie_horse zombie_nautilus"),
    "golem (made, not born)": "copper_golem iron_golem snow_golem",
    "person (not an animal)": "villager wandering_trader player mannequin",
    "furniture or decoration entity": "cushion armor_stand painting item_frame glow_item_frame leash_knot",
    "projectile, effect or technical entity": (
        "area_effect_cloud arrow block_display breeze_wind_charge dragon_fireball egg end_crystal ender_pearl "
        "evoker_fangs experience_bottle experience_orb eye_of_ender falling_block fireball firework_rocket "
        "fishing_bobber interaction item item_display lightning_bolt lingering_potion llama_spit marker "
        "ominous_item_spawner shulker_bullet small_fireball snowball spectral_arrow splash_potion text_display tnt "
        "trident wind_charge wither_skull"),
    "vehicle": (
        "acacia_boat acacia_chest_boat bamboo_chest_raft bamboo_raft birch_boat birch_chest_boat cherry_boat "
        "cherry_chest_boat chest_minecart command_block_minecart dark_oak_boat dark_oak_chest_boat furnace_minecart "
        "hopper_minecart jungle_boat jungle_chest_boat mangrove_boat mangrove_chest_boat minecart oak_boat "
        "oak_chest_boat pale_oak_boat pale_oak_chest_boat poplar_boat poplar_chest_boat spawner_minecart spruce_boat "
        "spruce_chest_boat tnt_minecart"),
}
EXCLUDED = {}
for _why, _names in _EXCLUDE_GROUPS.items():
    for _n in _names.split():
        EXCLUDED[_n] = _why

FISH = {"cod", "salmon", "tropical_fish", "pufferfish"}
WATER_BIOMES = {"warm_ocean", "lukewarm_ocean", "ocean", "cold_ocean", "frozen_ocean", "river", "frozen_river", "swamp",
                "mangrove_swamp"}
REQUIRED_BIOMES = ("plains sunflower_plains meadow forest flower_forest birch_forest old_growth_birch_forest dark_forest "
                   "dappled_forest pale_garden cherry_grove taiga old_growth_pine_taiga old_growth_spruce_taiga "
                   "snowy_taiga snowy_plains ice_spikes grove snowy_slopes frozen_peaks jagged_peaks stony_peaks "
                   "windswept_hills windswept_forest windswept_gravelly_hills savanna savanna_plateau windswept_savanna "
                   "desert badlands wooded_badlands eroded_badlands jungle sparse_jungle bamboo_jungle swamp "
                   "mangrove_swamp mushroom_fields beach snowy_beach stony_shore river frozen_river warm_ocean "
                   "lukewarm_ocean ocean cold_ocean frozen_ocean").split()
GROUPS = {"sea", "fowl", "cattle", "creeping", "beast"}
WHERES = {"land", "water", "air", "shore"}
BIOME_KEYS = {"bare", "green", "under", "deep_snow", "trees", "tree_spacing", "tree_chance", "ground", "extras", "look"}
ANIMAL_KEYS = {"look", "group", "biomes", "count", "where", "nbt", "by_biome"}
ANIMAL_OPTIONAL = {"variants"}
BADLANDS = {"badlands", "wooded_badlands", "eroded_badlands"}


# ------------------------------------------------------------------ the checker
def _split_top(s):
    """Split an SNBT field list on commas that are not inside quotes or brackets."""
    parts, depth, cur, q = [], 0, "", None
    for ch in s:
        if q:
            cur += ch
            if ch == q:
                q = None
        elif ch in "\"'":
            q = ch
            cur += ch
        elif ch in "[{(":
            depth += 1
            cur += ch
        elif ch in "]})":
            depth -= 1
            cur += ch
        elif ch == "," and depth == 0:
            parts.append(cur)
            cur = ""
        else:
            cur += ch
    if cur.strip():
        parts.append(cur)
    return parts


def _int(lo, hi, suffix=""):
    return lambda v: re.fullmatch(r"-?\d+" + suffix, v) is not None and lo <= int(v[:len(v) - len(suffix)]) <= hi


def _in(options):
    return lambda v: v in options


def check():
    problems = []

    def bad(msg):
        problems.append(msg)

    for p in (REG_PATH, BLOCKS_PATH, JAR_PATH):
        if not os.path.exists(p):
            print("missing source of truth: " + p)
            return 1
    entities = {k.split(":", 1)[1] for k in json.load(open(REG_PATH, encoding="utf-8"))["minecraft:entity_type"]["entries"]}
    blocks = json.load(open(BLOCKS_PATH, encoding="utf-8"))
    block_props = {k.split(":", 1)[1]: (v.get("properties") or {}) for k, v in blocks.items()}
    z = zipfile.ZipFile(JAR_PATH)
    fp = "data/minecraft/worldgen/feature/"
    features = {n[len(fp):-5] for n in z.namelist() if n.startswith(fp) and n.endswith(".json")}
    variants = {}
    for n in z.namelist():
        m = re.fullmatch(r"data/minecraft/(\w+_variant)/(\w+)\.json", n)
        if m:
            variants.setdefault(m.group(1), set()).add(m.group(2))

    used_blocks, used_features = set(), set()

    def check_block(ref, where):
        m = re.fullmatch(r"([a-z0-9_]+)(?:\[([^\]]*)\])?", ref)
        if not m:
            bad("%s: malformed block id %r" % (where, ref))
            return
        name, st = m.groups()
        if name not in block_props:
            bad("%s: unknown block %r" % (where, name))
            return
        used_blocks.add(name)
        if st:
            for kv in st.split(","):
                k, _, v = kv.partition("=")
                if k not in block_props[name]:
                    bad("%s: block %s has no property %r" % (where, name, k))
                elif v not in block_props[name][k]:
                    bad("%s: block %s property %s has no value %r" % (where, name, k, v))

    def check_feature(fid, where):
        if fid not in features:
            bad("%s: unknown feature %r" % (where, fid))
        else:
            used_features.add(fid)

    # ---- biomes
    if set(BIOMES) != set(REQUIRED_BIOMES):
        bad("BIOMES keys differ: missing %s extra %s" % (sorted(set(REQUIRED_BIOMES) - set(BIOMES)),
                                                        sorted(set(BIOMES) - set(REQUIRED_BIOMES))))
    for key, b in BIOMES.items():
        w = "biome %s" % key
        missing = BIOME_KEYS - set(b)
        if missing:
            bad("%s: missing keys %s" % (w, sorted(missing)))
            continue
        extra = set(b) - BIOME_KEYS - {"terraces"}
        if extra:
            bad("%s: unexpected keys %s" % (w, sorted(extra)))
        check_block(b["bare"], w + " bare")
        check_block(b["under"], w + " under")
        if b["green"] is not None:
            check_block(b["green"], w + " green")
            if b["bare"] != "dirt":
                bad("%s: green is set so bare must be 'dirt', not %r" % (w, b["bare"]))
        if not isinstance(b["deep_snow"], bool):
            bad("%s: deep_snow must be a bool" % w)
        if not isinstance(b["tree_spacing"], int) or b["tree_spacing"] < 0:
            bad("%s: tree_spacing must be a non-negative int" % w)
        if not (0 <= b["tree_chance"] <= 1):
            bad("%s: tree_chance out of range" % w)
        if b["trees"]:
            if b["tree_spacing"] < 1 or b["tree_chance"] <= 0:
                bad("%s: has trees but no spacing/chance" % w)
            for t in b["trees"]:
                if not (isinstance(t, tuple) and len(t) == 2 and t[1] > 0):
                    bad("%s: tree entry %r must be (feature, positive weight)" % (w, t))
                else:
                    check_feature(t[0], w + " tree")
        elif b["tree_chance"] > 0:
            bad("%s: tree_chance with no trees" % w)
        total = 0.0
        for g in b["ground"]:
            if not (isinstance(g, tuple) and len(g) == 2):
                bad("%s: ground entry %r must be (chance, thing)" % (w, g))
                continue
            ch, thing = g
            if not (0 < ch <= 0.6):
                bad("%s: ground chance %r out of range" % (w, ch))
            total += ch
            for item in (thing if isinstance(thing, list) else [thing]):
                if not isinstance(item, str):
                    bad("%s: ground thing %r not a string" % (w, item))
                elif item.startswith("feature:"):
                    if isinstance(thing, list):
                        bad("%s: feature inside a flower list: %r" % (w, item))
                    check_feature(item[8:], w + " ground")
                else:
                    check_block(item, w + " ground")
        if total > 0.6 + 1e-9:
            bad("%s: ground chances add up to %.3f (> 0.6)" % (w, total))
        for e in b["extras"]:
            if not (isinstance(e, tuple) and len(e) == 2 and isinstance(e[1], str) and e[1].startswith("feature:")):
                bad("%s: extras entry %r must be (chance, 'feature:<id>')" % (w, e))
                continue
            if not (0 < e[0] <= 0.1):
                bad("%s: extras chance %r out of range (0, 0.1]" % (w, e[0]))
            check_feature(e[1][8:], w + " extras")
        if key in BADLANDS:
            t = b.get("terraces")
            if not t or len(t) < 3:
                bad("%s: badlands need a terraces list" % w)
            else:
                for blk in t:
                    check_block(blk, w + " terraces")
        elif "terraces" in b:
            bad("%s: terraces only belong to badlands" % w)
        if not (isinstance(b["look"], str) and 20 <= len(b["look"]) <= 260 and b["look"].endswith(".")):
            bad("%s: look must be one sentence ending in a full stop" % w)
        elif re.search(r"\b(biome|block|blocks|minecraft|mob|spawn|game|texture|pixel)\b", b["look"], re.I):
            bad("%s: look uses a game/modern word" % w)

    # ---- animals
    rules = {
        "cow": {"variant": lambda v: v.strip('"') in {"minecraft:" + x for x in variants["cow_variant"]}},
        "pig": {"variant": lambda v: v.strip('"') in {"minecraft:" + x for x in variants["pig_variant"]}},
        "chicken": {"variant": lambda v: v.strip('"') in {"minecraft:" + x for x in variants["chicken_variant"]}},
        "frog": {"variant": lambda v: v.strip('"') in {"minecraft:" + x for x in variants["frog_variant"]}},
        "cat": {"variant": lambda v: v.strip('"') in {"minecraft:" + x for x in variants["cat_variant"]}},
        "wolf": {"variant": lambda v: v.strip('"') in {"minecraft:" + x for x in variants["wolf_variant"]}},
        "fox": {"Type": _in({'"red"', '"snow"'})},
        "mooshroom": {"Type": _in({'"red"', '"brown"'})},
        "salmon": {"type": _in({'"small"', '"medium"', '"large"'})},
        "rabbit": {"RabbitType": _int(0, 5)},          # 99 is the hostile killer rabbit: never allowed
        "parrot": {"Variant": _int(0, 4)},
        "axolotl": {"Variant": _int(0, 4)},
        "llama": {"Variant": _int(0, 3)},
        "horse": {"Variant": _int(0, 6 + 256 * 4)},
        "sheep": {"Color": _int(0, 15, "b")},
        "goat": {"IsScreamingGoat": _in({"0b", "1b"})},
        "tropical_fish": {"Variant": _int(0, 2 ** 31 - 1)},
        "panda": {"MainGene": _in({'"%s"' % g for g in "normal lazy worried playful brown weak".split()}),
                  "HiddenGene": _in({'"%s"' % g for g in "normal lazy worried playful brown weak".split()})},
    }

    def check_nbt(kind, s, where):
        if not isinstance(s, str):
            bad("%s: nbt must be a string" % where)
            return
        if s == "":
            return
        if "{" in s or "}" in s:
            bad("%s: nbt must not contain braces: %r" % (where, s))
            return
        if s.startswith(",") or s.endswith(","):
            bad("%s: stray comma in nbt %r" % (where, s))
        seen = set()
        for part in _split_top(s):
            k, sep, v = part.partition(":")
            k, v = k.strip(), v.strip()
            if not sep or not v:
                bad("%s: malformed nbt field %r" % (where, part))
                continue
            seen.add(k)
            r = rules.get(kind, {})
            if k not in r:
                bad("%s: field %r is not a known field for %s" % (where, k, kind))
            elif not r[k](v):
                bad("%s: bad value %s for %s.%s" % (where, v, kind, k))
        if kind == "panda" and seen and seen != {"MainGene", "HiddenGene"}:
            bad("%s: panda needs both MainGene and HiddenGene" % where)

    for k in sorted(ANIMALS):
        if k not in entities:
            bad("animal %s: not in registries.json" % k)
        if k in EXCLUDED:
            bad("animal %s: is also listed as excluded" % k)
    for k, a in ANIMALS.items():
        w = "animal %s" % k
        missing = ANIMAL_KEYS - set(a)
        if missing:
            bad("%s: missing keys %s" % (w, sorted(missing)))
            continue
        extra = set(a) - ANIMAL_KEYS - ANIMAL_OPTIONAL
        if extra:
            bad("%s: unexpected keys %s" % (w, sorted(extra)))
        if a["group"] not in GROUPS:
            bad("%s: bad group %r" % (w, a["group"]))
        if a["where"] not in WHERES:
            bad("%s: bad where %r" % (w, a["where"]))
        if not (isinstance(a["count"], int) and 4 <= a["count"] <= 40):
            bad("%s: count %r outside 4..40" % (w, a["count"]))
        if k in FISH and not (20 <= a["count"] <= 40):
            bad("%s: fish count must be 20..40" % w)
        if not a["biomes"]:
            bad("%s: needs at least one biome" % w)
        if len(set(a["biomes"])) != len(a["biomes"]):
            bad("%s: duplicate biomes" % w)
        for bm in a["biomes"]:
            if bm not in BIOMES:
                bad("%s: unknown biome %r" % (w, bm))
            elif a["where"] == "water" and bm not in WATER_BIOMES:
                bad("%s: lives in water but %s has none" % (w, bm))
        for bm, n in a["by_biome"].items():
            if bm not in BIOMES:
                bad("%s: by_biome has unknown biome %r" % (w, bm))
            elif bm not in a["biomes"]:
                bad("%s: by_biome biome %r is not in its biomes" % (w, bm))
            check_nbt(k, n, "%s by_biome[%s]" % (w, bm))
        check_nbt(k, a["nbt"], w + " nbt")
        for n in a.get("variants", []):
            check_nbt(k, n, w + " variants")
        if a.get("variants") and not a["nbt"]:
            bad("%s: variants given but nbt is empty" % w)
        if not (isinstance(a["look"], str) and len(a["look"]) > 15):
            bad("%s: look missing" % w)
        elif re.search(r"\b(minecraft|mob|spawn|game|biome|block)\b", a["look"], re.I):
            bad("%s: look uses a game word" % w)
    # no animal's look may name another animal
    for k, a in ANIMALS.items():
        for other in ANIMALS:
            word = other.replace("_", " ")
            if other != k and re.search(r"\b%ss?\b" % re.escape(word), a["look"], re.I):
                bad("animal %s: look names another animal (%s)" % (k, word))
    for k, b in BIOMES.items():
        for other in ANIMALS:
            if re.search(r"\b%ss?\b" % re.escape(other.replace("_", " ")), b["look"], re.I):
                bad("biome %s: look names an animal (%s)" % (k, other))
    # every entity in the registry is either an animal or excluded with a reason
    for e in sorted(entities):
        if e not in ANIMALS and e not in EXCLUDED:
            bad("entity %s is neither in ANIMALS nor EXCLUDED: decide" % e)
    for e in EXCLUDED:
        if e not in entities:
            bad("EXCLUDED lists %s which is not in registries.json" % e)

    print("biomes: %d   animals: %d   excluded entity types: %d   registry entity types: %d"
          % (len(BIOMES), len(ANIMALS), len(EXCLUDED), len(entities)))
    print("distinct features used: %d   distinct blocks used: %d" % (len(used_features), len(used_blocks)))
    print("features: " + " ".join(sorted(used_features)))
    by_group = {}
    for k, a in ANIMALS.items():
        by_group.setdefault(a["group"], []).append(k)
    for g in ("sea", "fowl", "cattle", "creeping", "beast"):
        print("%-9s %s" % (g, " ".join(sorted(by_group.get(g, [])))))
    print("total creatures to summon: %d" % sum(a["count"] for a in ANIMALS.values()))
    if problems:
        print("\n%d PROBLEM(S):" % len(problems))
        for p in problems:
            print("  - " + p)
        return 1
    print("\nOK: no problems found.")
    return 0


if __name__ == "__main__":
    if "--check" in sys.argv[1:]:
        sys.exit(check())
    print(__doc__)
