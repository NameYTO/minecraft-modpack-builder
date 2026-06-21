"""
seed.py — наповнення MongoDB тестовими даними (v3).
Структура версій:
  version = "universal"  → базові ванільні предмети для БУДЬ-ЯКОЇ версії
  version = "1.12.2"     → лише мод-предмети (Thermal Expansion, AE2)
  version = "1.20.1"     → сучасні предмети (незерит, мідь, аметист тощо)
Запуск: python seed.py
"""
import os
from datetime import datetime, timezone
from dotenv import load_dotenv
from pymongo import MongoClient, ASCENDING, DESCENDING

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME   = os.getenv("DB_NAME",   "minecraft_modpack")

client = MongoClient(MONGO_URI)
db     = client[DB_NAME]

db["items"].drop()
db["recipes"].drop()
print("Collections cleared.")

now = datetime.now(timezone.utc)

# ══════════════════════════════════════════════════════════════════════
#  UNIVERSAL — базові ванільні предмети для ВСІХ версій Minecraft
#  Ендпоінт /api/items?version=<anything> поверне ці предмети ЗАВЖДИ
# ══════════════════════════════════════════════════════════════════════

items_universal = [
    # ── Блоки ────────────────────────────────────────────────────────
    {"item_id": "minecraft:oak_planks",     "name": "Дубові дошки",       "category": "Блоки"},
    {"item_id": "minecraft:cobblestone",    "name": "Булижник",            "category": "Блоки"},
    {"item_id": "minecraft:stone",          "name": "Камінь",              "category": "Блоки"},
    {"item_id": "minecraft:glass",          "name": "Скло",                "category": "Блоки"},
    {"item_id": "minecraft:obsidian",       "name": "Обсидіан",            "category": "Блоки"},
    {"item_id": "minecraft:sand",           "name": "Пісок",               "category": "Блоки"},
    {"item_id": "minecraft:dirt",           "name": "Земля",               "category": "Блоки"},
    {"item_id": "minecraft:gravel",         "name": "Гравій",              "category": "Блоки"},
    {"item_id": "minecraft:iron_ore",       "name": "Залізна руда",        "category": "Блоки"},
    {"item_id": "minecraft:gold_ore",       "name": "Золота руда",         "category": "Блоки"},
    {"item_id": "minecraft:coal_ore",       "name": "Вугільна руда",       "category": "Блоки"},
    {"item_id": "minecraft:chest",          "name": "Скриня",              "category": "Блоки"},
    {"item_id": "minecraft:furnace",        "name": "Піч",                 "category": "Блоки"},
    {"item_id": "minecraft:crafting_table", "name": "Верстак",             "category": "Блоки"},
    {"item_id": "minecraft:bookshelf",      "name": "Книжкова шафа",       "category": "Блоки"},
    {"item_id": "minecraft:torch",          "name": "Смолоскип",           "category": "Блоки"},
    {"item_id": "minecraft:stone_bricks",   "name": "Кам'яні цеглини",    "category": "Блоки"},
    {"item_id": "minecraft:oak_log",        "name": "Дубова колода",       "category": "Блоки"},

    # ── Ресурси та матеріали ─────────────────────────────────────────
    {"item_id": "minecraft:iron_ingot",     "name": "Залізний злиток",     "category": "Ресурси та матеріали"},
    {"item_id": "minecraft:gold_ingot",     "name": "Золотий злиток",      "category": "Ресурси та матеріали"},
    {"item_id": "minecraft:diamond",        "name": "Алмаз",               "category": "Ресурси та матеріали"},
    {"item_id": "minecraft:coal",           "name": "Вугілля",             "category": "Ресурси та матеріали"},
    {"item_id": "minecraft:emerald",        "name": "Смарагд",             "category": "Ресурси та матеріали"},
    {"item_id": "minecraft:lapis_lazuli",   "name": "Ляпіс-лазур",        "category": "Ресурси та матеріали"},
    {"item_id": "minecraft:redstone",       "name": "Редстоун",            "category": "Ресурси та матеріали"},
    {"item_id": "minecraft:quartz",         "name": "Нетеровий кварц",     "category": "Ресурси та матеріали"},
    {"item_id": "minecraft:stick",          "name": "Палиця",              "category": "Ресурси та матеріали"},
    {"item_id": "minecraft:string",         "name": "Нитка",               "category": "Ресурси та матеріали"},
    {"item_id": "minecraft:bone",           "name": "Кістка",              "category": "Ресурси та матеріали"},
    {"item_id": "minecraft:blaze_rod",      "name": "Скіпетр вогню",       "category": "Ресурси та матеріали"},
    {"item_id": "minecraft:feather",        "name": "Перо",                "category": "Ресурси та матеріали"},
    {"item_id": "minecraft:flint",          "name": "Кремінь",             "category": "Ресурси та матеріали"},
    {"item_id": "minecraft:leather",        "name": "Шкіра",               "category": "Ресурси та матеріали"},
    {"item_id": "minecraft:ender_pearl",    "name": "Перло Краю",          "category": "Ресурси та матеріали"},
    {"item_id": "minecraft:gunpowder",      "name": "Порох",               "category": "Ресурси та матеріали"},
    {"item_id": "minecraft:slime_ball",     "name": "Куля слизу",          "category": "Ресурси та матеріали"},
    {"item_id": "minecraft:apple",          "name": "Яблуко",              "category": "Ресурси та матеріали"},
    {"item_id": "minecraft:bread",          "name": "Хліб",                "category": "Ресурси та матеріали"},

    # ── Інструменти та зброя ─────────────────────────────────────────
    {"item_id": "minecraft:wooden_sword",   "name": "Дерев'яний меч",     "category": "Інструменти та зброя"},
    {"item_id": "minecraft:stone_sword",    "name": "Кам'яний меч",       "category": "Інструменти та зброя"},
    {"item_id": "minecraft:iron_sword",     "name": "Залізний меч",        "category": "Інструменти та зброя"},
    {"item_id": "minecraft:golden_sword",   "name": "Золотий меч",         "category": "Інструменти та зброя"},
    {"item_id": "minecraft:diamond_sword",  "name": "Алмазний меч",        "category": "Інструменти та зброя"},
    {"item_id": "minecraft:iron_pickaxe",   "name": "Залізна кирка",       "category": "Інструменти та зброя"},
    {"item_id": "minecraft:diamond_pickaxe","name": "Алмазна кирка",       "category": "Інструменти та зброя"},
    {"item_id": "minecraft:iron_axe",       "name": "Залізна сокира",      "category": "Інструменти та зброя"},
    {"item_id": "minecraft:iron_shovel",    "name": "Залізна лопата",      "category": "Інструменти та зброя"},
    {"item_id": "minecraft:iron_hoe",       "name": "Залізна мотика",      "category": "Інструменти та зброя"},
    {"item_id": "minecraft:bow",            "name": "Лук",                 "category": "Інструменти та зброя"},
    {"item_id": "minecraft:fishing_rod",    "name": "Вудка",               "category": "Інструменти та зброя"},
    {"item_id": "minecraft:flint_and_steel","name": "Кремінь та сталь",    "category": "Інструменти та зброя"},
    {"item_id": "minecraft:shears",         "name": "Ножиці",              "category": "Інструменти та зброя"},
    {"item_id": "minecraft:wooden_pickaxe", "name": "Дерев'яна кирка",     "category": "Інструменти та зброя"},
    {"item_id": "minecraft:stone_pickaxe",  "name": "Кам'яна кирка",       "category": "Інструменти та зброя"},
    {"item_id": "minecraft:golden_pickaxe", "name": "Золота кирка",        "category": "Інструменти та зброя"},
    {"item_id": "minecraft:golden_sword",   "name": "Золотий меч",         "category": "Інструменти та зброя"},
    {"item_id": "minecraft:diamond_axe",    "name": "Алмазна сокира",      "category": "Інструменти та зброя"},
    {"item_id": "minecraft:diamond_shovel", "name": "Алмазна лопата",      "category": "Інструменти та зброя"},
    {"item_id": "minecraft:diamond_hoe",    "name": "Алмазна мотика",      "category": "Інструменти та зброя"},
    {"item_id": "minecraft:iron_helmet",    "name": "Залізний шолом",      "category": "Інструменти та зброя"},
    {"item_id": "minecraft:iron_chestplate","name": "Залізний нагрудник",  "category": "Інструменти та зброя"},
    {"item_id": "minecraft:iron_leggings",  "name": "Залізні поножі",      "category": "Інструменти та зброя"},
    {"item_id": "minecraft:iron_boots",     "name": "Залізні чоботи",      "category": "Інструменти та зброя"},
    {"item_id": "minecraft:diamond_helmet", "name": "Алмазний шолом",      "category": "Інструменти та зброя"},
    {"item_id": "minecraft:diamond_chestplate","name": "Алмазний нагрудник","category": "Інструменти та зброя"},
    {"item_id": "minecraft:bucket",         "name": "Відро",               "category": "Інструменти та зброя"},
    {"item_id": "minecraft:water_bucket",   "name": "Відро води",          "category": "Інструменти та зброя"},
    {"item_id": "minecraft:lava_bucket",    "name": "Відро лави",          "category": "Інструменти та зброя"},
    {"item_id": "minecraft:milk_bucket",    "name": "Відро молока",        "category": "Інструменти та зброя"},
    {"item_id": "minecraft:compass",        "name": "Компас",              "category": "Інструменти та зброя"},
    {"item_id": "minecraft:clock",          "name": "Годинник",            "category": "Інструменти та зброя"},
]

# Додаткові ванільні предмети (universal) — розширений каталог
items_universal_extra = [
    # ── Блоки ──
    {"item_id": "minecraft:spruce_planks",  "name": "Ялинові дошки",       "category": "Блоки"},
    {"item_id": "minecraft:birch_planks",   "name": "Березові дошки",      "category": "Блоки"},
    {"item_id": "minecraft:spruce_log",     "name": "Ялинова колода",      "category": "Блоки"},
    {"item_id": "minecraft:smooth_stone",   "name": "Гладкий камінь",      "category": "Блоки"},
    {"item_id": "minecraft:diamond_ore",    "name": "Алмазна руда",        "category": "Блоки"},
    {"item_id": "minecraft:emerald_ore",    "name": "Смарагдова руда",     "category": "Блоки"},
    {"item_id": "minecraft:redstone_ore",   "name": "Редстоунова руда",    "category": "Блоки"},
    {"item_id": "minecraft:lapis_ore",      "name": "Ляпісова руда",       "category": "Блоки"},
    {"item_id": "minecraft:diamond_block",  "name": "Блок алмазу",         "category": "Блоки"},
    {"item_id": "minecraft:gold_block",     "name": "Блок золота",         "category": "Блоки"},
    {"item_id": "minecraft:iron_block",     "name": "Блок заліза",         "category": "Блоки"},
    {"item_id": "minecraft:emerald_block",  "name": "Блок смарагду",       "category": "Блоки"},
    {"item_id": "minecraft:redstone_block", "name": "Блок редстоуну",      "category": "Блоки"},
    {"item_id": "minecraft:coal_block",     "name": "Блок вугілля",        "category": "Блоки"},
    {"item_id": "minecraft:lapis_block",    "name": "Блок ляпісу",         "category": "Блоки"},
    {"item_id": "minecraft:quartz_block",   "name": "Кварцовий блок",      "category": "Блоки"},
    {"item_id": "minecraft:bricks",         "name": "Цегляний блок",       "category": "Блоки"},
    {"item_id": "minecraft:nether_bricks",  "name": "Пекельна цегла",      "category": "Блоки"},
    {"item_id": "minecraft:glowstone",      "name": "Сяйний камінь",       "category": "Блоки"},
    {"item_id": "minecraft:sea_lantern",    "name": "Морський ліхтар",     "category": "Блоки"},
    {"item_id": "minecraft:hay_block",      "name": "Сінний блок",         "category": "Блоки"},
    {"item_id": "minecraft:sponge",         "name": "Губка",               "category": "Блоки"},
    {"item_id": "minecraft:melon",          "name": "Кавун",               "category": "Блоки"},
    {"item_id": "minecraft:pumpkin",        "name": "Гарбуз",              "category": "Блоки"},
    {"item_id": "minecraft:clay",           "name": "Глиняний блок",       "category": "Блоки"},
    {"item_id": "minecraft:end_stone",      "name": "Камінь Краю",         "category": "Блоки"},
    {"item_id": "minecraft:purpur_block",   "name": "Пурпуровий блок",     "category": "Блоки"},
    {"item_id": "minecraft:prismarine",     "name": "Призмарин",           "category": "Блоки"},
    {"item_id": "minecraft:dark_prismarine","name": "Темний призмарин",    "category": "Блоки"},
    {"item_id": "minecraft:sandstone",      "name": "Пісковик",            "category": "Блоки"},
    {"item_id": "minecraft:red_sand",       "name": "Червоний пісок",      "category": "Блоки"},
    {"item_id": "minecraft:white_wool",     "name": "Біла вовна",          "category": "Блоки"},
    {"item_id": "minecraft:oak_leaves",     "name": "Дубове листя",        "category": "Блоки"},
    {"item_id": "minecraft:netherrack",     "name": "Пекельний камінь",    "category": "Блоки"},
    {"item_id": "minecraft:soul_sand",      "name": "Пісок душ",           "category": "Блоки"},
    {"item_id": "minecraft:magma_block",    "name": "Магмовий блок",       "category": "Блоки"},
    {"item_id": "minecraft:slime_block",    "name": "Блок слизу",          "category": "Блоки"},
    {"item_id": "minecraft:honey_block",    "name": "Медовий блок",        "category": "Блоки"},
    {"item_id": "minecraft:tnt",            "name": "Динаміт",             "category": "Блоки"},
    {"item_id": "minecraft:redstone_lamp",  "name": "Редстоунова лампа",   "category": "Блоки"},
    # ── Ресурси та матеріали ──
    {"item_id": "minecraft:charcoal",       "name": "Деревне вугілля",     "category": "Ресурси та матеріали"},
    {"item_id": "minecraft:blaze_powder",   "name": "Вогняний порошок",    "category": "Ресурси та матеріали"},
    {"item_id": "minecraft:ender_eye",      "name": "Око Краю",            "category": "Ресурси та матеріали"},
    {"item_id": "minecraft:clay_ball",      "name": "Грудка глини",        "category": "Ресурси та матеріали"},
    {"item_id": "minecraft:brick",          "name": "Цеглина",             "category": "Ресурси та матеріали"},
    {"item_id": "minecraft:nether_brick",   "name": "Пекельна цеглина",    "category": "Ресурси та матеріали"},
    {"item_id": "minecraft:paper",          "name": "Папір",               "category": "Ресурси та матеріали"},
    {"item_id": "minecraft:book",           "name": "Книга",               "category": "Ресурси та матеріали"},
    {"item_id": "minecraft:glowstone_dust", "name": "Сяйний пил",          "category": "Ресурси та матеріали"},
    {"item_id": "minecraft:magma_cream",    "name": "Магмовий крем",       "category": "Ресурси та матеріали"},
    {"item_id": "minecraft:nether_star",    "name": "Зоря Незеру",         "category": "Ресурси та матеріали"},
    {"item_id": "minecraft:ghast_tear",     "name": "Сльоза гаста",        "category": "Ресурси та матеріали"},
    {"item_id": "minecraft:honeycomb",      "name": "Стільники",           "category": "Ресурси та матеріали"},
    {"item_id": "minecraft:ink_sac",        "name": "Чорнильний мішок",    "category": "Ресурси та матеріали"},
    {"item_id": "minecraft:wheat",          "name": "Пшениця",             "category": "Ресурси та матеріали"},
    {"item_id": "minecraft:sugar",          "name": "Цукор",               "category": "Ресурси та матеріали"},
    {"item_id": "minecraft:egg",            "name": "Яйце",                "category": "Ресурси та матеріали"},
    {"item_id": "minecraft:golden_apple",   "name": "Золоте яблуко",       "category": "Ресурси та матеріали"},
    {"item_id": "minecraft:prismarine_shard","name": "Уламок призмарину",  "category": "Ресурси та матеріали"},
    {"item_id": "minecraft:prismarine_crystals","name": "Кристали призмарину","category": "Ресурси та матеріали"},
    {"item_id": "minecraft:rabbit_foot",    "name": "Кроляча лапка",       "category": "Ресурси та матеріали"},
    {"item_id": "minecraft:rabbit_hide",    "name": "Кроляча шкура",       "category": "Ресурси та матеріали"},
    {"item_id": "minecraft:nautilus_shell", "name": "Мушля наутілуса",     "category": "Ресурси та матеріали"},
    {"item_id": "minecraft:heart_of_the_sea","name": "Серце моря",         "category": "Ресурси та матеріали"},
    {"item_id": "minecraft:dried_kelp",     "name": "Сушені водорості",    "category": "Ресурси та матеріали"},
]

# ══════════════════════════════════════════════════════════════════════
#  1.12.2 — ТІЛЬКИ мод-предмети (Thermal Expansion, AE2)
#  Завантажуються лише при version=1.12.2 + universal
# ══════════════════════════════════════════════════════════════════════

items_112 = [
    # ── Thermal Expansion ─────────────────────────────────────────────
    {"item_id": "thermalexpansion:copper_ingot",       "name": "Мідний злиток (TE)",           "category": "Thermal Expansion"},
    {"item_id": "thermalexpansion:tin_ingot",          "name": "Олов'яний злиток (TE)",         "category": "Thermal Expansion"},
    {"item_id": "thermalexpansion:silver_ingot",       "name": "Срібний злиток (TE)",           "category": "Thermal Expansion"},
    {"item_id": "thermalexpansion:lead_ingot",         "name": "Свинцевий злиток (TE)",         "category": "Thermal Expansion"},
    {"item_id": "thermalexpansion:nickel_ingot",       "name": "Нікелевий злиток (TE)",         "category": "Thermal Expansion"},
    {"item_id": "thermalexpansion:pulverizer",         "name": "Подрібнювач (TE)",              "category": "Thermal Expansion"},
    {"item_id": "thermalexpansion:induction_smelter",  "name": "Індукційна плавильня (TE)",     "category": "Thermal Expansion"},
    {"item_id": "thermalexpansion:energy_cell",        "name": "Енергетична клітина (TE)",      "category": "Thermal Expansion"},
    {"item_id": "thermalexpansion:redstone_furnace",   "name": "Редстоун-піч (TE)",             "category": "Thermal Expansion"},
    {"item_id": "thermalexpansion:dynamo",             "name": "Паровий генератор (TE)",        "category": "Thermal Expansion"},

    # ── Applied Energistics 2 ─────────────────────────────────────────
    {"item_id": "appliedenergistics2:quartz_glass",          "name": "Кварцове скло (AE2)",    "category": "Applied Energistics 2"},
    {"item_id": "appliedenergistics2:certus_quartz_crystal", "name": "Кристал кварцу (AE2)",   "category": "Applied Energistics 2"},
    {"item_id": "appliedenergistics2:fluix_crystal",         "name": "Кристал флюксу (AE2)",   "category": "Applied Energistics 2"},
    {"item_id": "appliedenergistics2:sky_stone",             "name": "Камінь неба (AE2)",      "category": "Applied Energistics 2"},
    {"item_id": "appliedenergistics2:drive",                 "name": "ME-диск (AE2)",           "category": "Applied Energistics 2"},
    {"item_id": "appliedenergistics2:controller",            "name": "ME-контролер (AE2)",      "category": "Applied Energistics 2"},
    {"item_id": "appliedenergistics2:cable",                 "name": "ME-кабель (AE2)",         "category": "Applied Energistics 2"},
    {"item_id": "appliedenergistics2:terminal",              "name": "ME-термінал (AE2)",       "category": "Applied Energistics 2"},
    {"item_id": "appliedenergistics2:pattern",               "name": "ME-шаблон (AE2)",         "category": "Applied Energistics 2"},
    {"item_id": "appliedenergistics2:inscriber",             "name": "Гравер (AE2)",            "category": "Applied Energistics 2"},
]

# ══════════════════════════════════════════════════════════════════════
#  1.20.1 — Сучасні ванільні предмети (1.16–1.20 ексклюзиви)
#  Завантажуються лише при version=1.20.1 + universal
# ══════════════════════════════════════════════════════════════════════

items_modern = [
    # ── Блоки (сучасні) ───────────────────────────────────────────────
    {"item_id": "minecraft:deepslate",           "name": "Глибинний сланець",                  "category": "Блоки"},
    {"item_id": "minecraft:tuff",                "name": "Туф",                                "category": "Блоки"},
    {"item_id": "minecraft:calcite",             "name": "Кальцит",                            "category": "Блоки"},
    {"item_id": "minecraft:barrel",              "name": "Барель",                             "category": "Блоки"},
    {"item_id": "minecraft:smithing_table",      "name": "Стіл коваля",                        "category": "Блоки"},
    {"item_id": "minecraft:blast_furnace",       "name": "Доменна піч",                        "category": "Блоки"},
    {"item_id": "minecraft:smoker",              "name": "Коптильня",                          "category": "Блоки"},
    {"item_id": "minecraft:amethyst_block",      "name": "Блок аметисту",                      "category": "Блоки"},

    # ── Ресурси та матеріали (сучасні) ───────────────────────────────
    {"item_id": "minecraft:netherite_ingot",     "name": "Незеритовий злиток",                 "category": "Ресурси та матеріали"},
    {"item_id": "minecraft:copper_ingot",        "name": "Мідний злиток",                      "category": "Ресурси та матеріали"},
    {"item_id": "minecraft:amethyst_shard",      "name": "Аметистовий осколок",                "category": "Ресурси та матеріали"},
    {"item_id": "minecraft:echo_shard",          "name": "Осколок луни",                       "category": "Ресурси та матеріали"},
    {"item_id": "minecraft:disc_fragment_5",     "name": "Фрагмент диска",                     "category": "Ресурси та матеріали"},
    {"item_id": "minecraft:raw_iron",            "name": "Необроблене залізо",                 "category": "Ресурси та матеріали"},
    {"item_id": "minecraft:raw_gold",            "name": "Необроблене золото",                 "category": "Ресурси та матеріали"},
    {"item_id": "minecraft:raw_copper",          "name": "Необроблена мідь",                   "category": "Ресурси та матеріали"},

    # ── Інструменти та зброя (сучасні) ───────────────────────────────
    {"item_id": "minecraft:netherite_sword",     "name": "Незеритовий меч",                    "category": "Інструменти та зброя"},
    {"item_id": "minecraft:netherite_pickaxe",   "name": "Незеритова кирка",                   "category": "Інструменти та зброя"},
    {"item_id": "minecraft:crossbow",            "name": "Арбалет",                            "category": "Інструменти та зброя"},
    {"item_id": "minecraft:trident",             "name": "Тризуб",                             "category": "Інструменти та зброя"},
    {"item_id": "minecraft:spyglass",            "name": "Підзорна труба",                     "category": "Інструменти та зброя"},

    # ── Блоки (сучасні, додатково) ──
    {"item_id": "minecraft:cobbled_deepslate",   "name": "Бруківка глибосланцю",               "category": "Блоки"},
    {"item_id": "minecraft:deepslate_bricks",    "name": "Глибосланцева цегла",                "category": "Блоки"},
    {"item_id": "minecraft:tinted_glass",        "name": "Тоноване скло",                      "category": "Блоки"},
    {"item_id": "minecraft:amethyst_cluster",    "name": "Грозно аметисту",                    "category": "Блоки"},
    {"item_id": "minecraft:budding_amethyst",    "name": "Аметист, що росте",                  "category": "Блоки"},
    {"item_id": "minecraft:copper_block",        "name": "Мідний блок",                        "category": "Блоки"},
    {"item_id": "minecraft:copper_ore",          "name": "Мідна руда",                         "category": "Блоки"},
    {"item_id": "minecraft:raw_iron_block",      "name": "Блок необробл. заліза",              "category": "Блоки"},
    {"item_id": "minecraft:raw_gold_block",      "name": "Блок необробл. золота",              "category": "Блоки"},
    {"item_id": "minecraft:raw_copper_block",    "name": "Блок необробл. міді",                "category": "Блоки"},

    # ── Ресурси (сучасні, додатково) ──
    {"item_id": "minecraft:netherite_scrap",     "name": "Незеритовий брухт",                  "category": "Ресурси та матеріали"},
    {"item_id": "minecraft:glow_ink_sac",        "name": "Сяйний чорнильний мішок",            "category": "Ресурси та матеріали"},
    {"item_id": "minecraft:phantom_membrane",    "name": "Мембрана фантома",                   "category": "Ресурси та матеріали"},

    # ── Шаблони коваля ────────────────────────────────────────────────
    {"item_id": "minecraft:netherite_upgrade_smithing_template",
     "name": "Шаблон незерит. оновлення",                                                      "category": "Ресурси та матеріали"},
    {"item_id": "minecraft:coast_armor_trim_smithing_template",
     "name": "Шаблон прибережного обладунку",                                                  "category": "Ресурси та матеріали"},
]

# ══════════════════════════════════════════════════════════════════════
#  ВСТАВКА У MONGODB
# ══════════════════════════════════════════════════════════════════════

def insert_items(items_list: list, version: str) -> int:
    docs = []
    for item in items_list:
        docs.append({
            "item_id":    item["item_id"],
            "name":       item["name"],
            "version":    version,
            "icon":       "",       # обчислюється на фронтенді через getIconUrl()
            "emoji":      "",       # прибрано — іконки замінені на PNG
            "category":   item.get("category", "Інше"),
            "mod":        item["item_id"].split(":")[0],
            "created_at": now,
        })
    if docs:
        db["items"].insert_many(docs, ordered=False)
    return len(docs)


n_univ = insert_items(items_universal, "universal")
n_extra = insert_items(items_universal_extra, "universal")
n_112  = insert_items(items_112,  "1.12.2")
n_mod  = insert_items(items_modern, "1.20.1")
print(f"Items inserted: {n_univ}+{n_extra} (universal) + {n_112} (1.12.2 mods) + {n_mod} (1.20.1 modern) = {n_univ+n_extra+n_112+n_mod} total")

# ══════════════════════════════════════════════════════════════════════
#  РЕЦЕПТИ — по 4 для кожної версії
# ══════════════════════════════════════════════════════════════════════

recipes = [
    # ── 1.12.2 — CraftTweaker ────────────────────────────────────────
    {
        "user_id": "admin", "game_version": "1.12.2", "station": "crafting",
        "craft_matrix": [
            ["minecraft:iron_ingot", None,                  None],
            ["minecraft:iron_ingot", None,                  None],
            ["minecraft:stick",      None,                  None],
        ],
        "result": {"item_id": "minecraft:iron_sword", "count": 1},
    },
    {
        "user_id": "admin", "game_version": "1.12.2", "station": "crafting",
        "craft_matrix": [
            ["minecraft:diamond", "minecraft:diamond", "minecraft:diamond"],
            [None,                "minecraft:stick",   None              ],
            [None,                "minecraft:stick",   None              ],
        ],
        "result": {"item_id": "minecraft:diamond_pickaxe", "count": 1},
    },
    {
        "user_id": "user", "game_version": "1.12.2", "station": "smelting",
        "craft_matrix": [
            ["minecraft:iron_ore", None, None],
            [None,                 None, None],
            [None,                 None, None],
        ],
        "experience": 0.7, "cookingtime": 200,
        "result": {"item_id": "minecraft:iron_ingot", "count": 1},
    },
    {
        "user_id": "user", "game_version": "1.12.2", "station": "crafting",
        "craft_matrix": [
            ["thermalexpansion:copper_ingot", "thermalexpansion:copper_ingot", "thermalexpansion:copper_ingot"],
            ["thermalexpansion:copper_ingot", "minecraft:diamond",             "thermalexpansion:copper_ingot"],
            ["thermalexpansion:copper_ingot", "thermalexpansion:copper_ingot", "thermalexpansion:copper_ingot"],
        ],
        "result": {"item_id": "thermalexpansion:pulverizer", "count": 1},
    },

    # ── 1.20.1 — Data Pack ───────────────────────────────────────────
    {
        "user_id": "admin", "game_version": "1.20.1", "station": "crafting",
        "craft_matrix": [
            ["minecraft:netherite_ingot", "minecraft:netherite_ingot", "minecraft:netherite_ingot"],
            [None,                        "minecraft:stick",            None                      ],
            [None,                        "minecraft:stick",            None                      ],
        ],
        "result": {"item_id": "minecraft:netherite_pickaxe", "count": 1},
    },
    {
        "user_id": "admin", "game_version": "1.20.1", "station": "smithing",
        "craft_matrix": [
            ["minecraft:netherite_upgrade_smithing_template",
             "minecraft:diamond_pickaxe",
             "minecraft:netherite_ingot"],
            [None, None, None],
            [None, None, None],
        ],
        "result": {"item_id": "minecraft:netherite_pickaxe", "count": 1},
    },
    {
        "user_id": "user", "game_version": "1.20.1", "station": "stonecutting",
        "craft_matrix": [
            ["minecraft:cobblestone", None, None],
            [None,                    None, None],
            [None,                    None, None],
        ],
        "result": {"item_id": "minecraft:stone", "count": 1},
    },
    {
        "user_id": "user", "game_version": "1.20.1", "station": "smelting",
        "craft_matrix": [
            ["minecraft:raw_gold", None, None],
            [None,                 None, None],
            [None,                 None, None],
        ],
        "experience": 1.0, "cookingtime": 200,
        "result": {"item_id": "minecraft:gold_ingot", "count": 1},
    },
]

for r in recipes:
    r["created_at"] = now
    r.setdefault("experience",  None)
    r.setdefault("cookingtime", None)

res = db["recipes"].insert_many(recipes)
print(f"Recipes inserted: {len(res.inserted_ids)}")

# ══════════════════════════════════════════════════════════════════════
#  ІНДЕКСИ
# ══════════════════════════════════════════════════════════════════════

db["items"].create_index([("item_id", ASCENDING), ("version", ASCENDING)], unique=True)
db["items"].create_index([("mod",      ASCENDING)])
db["items"].create_index([("version",  ASCENDING)])
db["items"].create_index([("name",     ASCENDING)])
db["items"].create_index([("category", ASCENDING)])

db["recipes"].create_index([("user_id",      ASCENDING)])
db["recipes"].create_index([("game_version", ASCENDING)])
db["recipes"].create_index([("station",      ASCENDING)])
db["recipes"].create_index([("created_at",   DESCENDING)])
db["recipes"].create_index([("user_id", ASCENDING), ("game_version", ASCENDING)])

print("Indexes created.")
print("\nSeed complete!")
print("Demo credentials: admin/admin123  user/user123")
print("Run: python app.py  → open http://localhost:5000")
