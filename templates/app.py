"""
╔═══════════════════════════════════════════════════════════════════════╗
║   Minecraft Modpack Builder — Flask Backend v2.0                      ║
║   Дипломна робота: автоматизоване формування Minecraft-збірок         ║
╠═══════════════════════════════════════════════════════════════════════╣
║  v2: Авторизація (roles), 6 робочих станцій, адмін-панель             ║
╠═══════════════════════════════════════════════════════════════════════╣
║  POST /auth/login          — вхід                                     ║
║  GET  /auth/logout         — вихід                                    ║
║  GET  /api/auth/me         — поточний користувач                      ║
║  GET    /api/items         — список предметів [auth]                  ║
║  POST   /api/items         — додати предмет [admin]                   ║
║  DELETE /api/items/<id>    — видалити [admin]                         ║
║  GET    /api/recipes       — рецепти (user: свої; admin: всі) [auth]  ║
║  POST   /api/recipes       — зберегти [auth]                          ║
║  DELETE /api/recipes/<id>  — видалити (user: свій; admin: будь-який)  ║
║  POST   /api/export        — генерувати ZIP [auth]                    ║
║  GET    /api/admin/stats   — статистика [admin]                       ║
║  GET    /api/admin/recipes — всі рецепти [admin]                      ║
║  GET    /health            — стан MongoDB                             ║
╚═══════════════════════════════════════════════════════════════════════╝
"""
from __future__ import annotations

import json
import os
import re
import shutil
import tempfile
import threading
import time
import zipfile
from datetime import datetime, timezone
from functools import wraps
from typing import Optional

from bson import ObjectId
from bson.errors import InvalidId
from dotenv import load_dotenv
from flask import (Flask, after_this_request, jsonify, render_template,
                   request, send_file, session)
from flask_cors import CORS
from pymongo import MongoClient, ASCENDING, DESCENDING
from werkzeug.security import generate_password_hash, check_password_hash

# ══════════════════════════════════════════════════════════════════════
#  КОНФІГУРАЦІЯ
# ══════════════════════════════════════════════════════════════════════

load_dotenv()

MONGO_URI: str  = os.getenv("MONGO_URI",   "mongodb://localhost:27017/")
DB_NAME: str    = os.getenv("DB_NAME",     "minecraft_modpack")
SECRET_KEY: str = os.getenv("SECRET_KEY",  "mc-diploma-secret-2024")
PORT: int       = int(os.getenv("PORT",    "5000"))
DEBUG: bool     = os.getenv("FLASK_DEBUG", "0") == "1"

# ══════════════════════════════════════════════════════════════════════
#  ЗАХАРДКОДЖЕНІ КОРИСТУВАЧІ (демо для дипломної роботи)
# ══════════════════════════════════════════════════════════════════════

USERS: dict[str, dict] = {
    "admin": {"password": "admin123", "role": "admin",  "display": "Адміністратор"},
    "user":  {"password": "user123",  "role": "user",   "display": "Користувач"},
}

# ══════════════════════════════════════════════════════════════════════
#  MONGODB (singleton)
# ══════════════════════════════════════════════════════════════════════

_mongo_client: Optional[MongoClient] = None


def _get_db():
    global _mongo_client
    if _mongo_client is None:
        _mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5_000)
    return _mongo_client[DB_NAME]


def _col_items():
    return _get_db()["items"]


def _col_recipes():
    return _get_db()["recipes"]


def _col_users():
    return _get_db()["users"]


def _ensure_indexes() -> None:
    try:
        col_i = _col_items()
        col_i.create_index([("item_id", ASCENDING), ("version", ASCENDING)], unique=True)
        col_i.create_index([("mod",     ASCENDING)])
        col_i.create_index([("version", ASCENDING)])
        col_i.create_index([("name",    ASCENDING)])

        col_r = _col_recipes()
        col_r.create_index([("user_id",      ASCENDING)])
        col_r.create_index([("game_version", ASCENDING)])
        col_r.create_index([("station",      ASCENDING)])
        col_r.create_index([("created_at",   DESCENDING)])
        col_r.create_index([("user_id", ASCENDING), ("game_version", ASCENDING)])

        col_u = _col_users()
        col_u.create_index([("username", ASCENDING)], unique=True)

        print("[MongoDB] Indexes ensured ✓")
    except Exception as exc:
        print(f"[MongoDB] Index warning: {exc}")


# ══════════════════════════════════════════════════════════════════════
#  FLASK APP
# ══════════════════════════════════════════════════════════════════════

app = Flask(__name__)
app.config["SECRET_KEY"]              = SECRET_KEY
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_HTTPONLY"] = True

CORS(app,
     resources={r"/api/*": {"origins": "*"}, r"/auth/*": {"origins": "*"}},
     supports_credentials=True)

# ══════════════════════════════════════════════════════════════════════
#  AUTH DECORATORS
# ══════════════════════════════════════════════════════════════════════

def login_required(f):
    """Вимагає активної сесії; повертає 401 якщо не авторизовано."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if "username" not in session:
            return jsonify({"error": "Authentication required", "code": "UNAUTHORIZED"}), 401
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    """Вимагає ролі 'admin'; повертає 403 якщо прав недостатньо."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if "username" not in session:
            return jsonify({"error": "Authentication required", "code": "UNAUTHORIZED"}), 401
        if session.get("role") != "admin":
            return jsonify({"error": "Admin privileges required", "code": "FORBIDDEN"}), 403
        return f(*args, **kwargs)
    return decorated


# ══════════════════════════════════════════════════════════════════════
#  СХЕМА ДАНИХ — валідація
# ══════════════════════════════════════════════════════════════════════

VALID_STATIONS = frozenset({
    "crafting", "smelting", "blasting", "smoking",
    "campfire", "stonecutting", "smithing", "anvil", "brewing",
})


def _validate_item(d: dict) -> list[str]:
    errors: list[str] = []
    for field in ("item_id", "name", "version", "mod"):
        if not d.get(field):
            errors.append(f"'{field}' is required")
    if d.get("item_id") and ":" not in d["item_id"]:
        errors.append("'item_id' must be namespaced, e.g. 'minecraft:dirt'")
    return errors


def _validate_recipe(d: dict) -> list[str]:
    errors: list[str] = []

    if not d.get("user_id"):
        errors.append("'user_id' is required")
    if not d.get("game_version"):
        errors.append("'game_version' is required")

    station = d.get("station", "crafting")
    if station not in VALID_STATIONS:
        errors.append(f"'station' must be one of: {', '.join(sorted(VALID_STATIONS))}")

    matrix = d.get("craft_matrix")
    if matrix is None:
        errors.append("'craft_matrix' is required")
    elif not isinstance(matrix, list) or len(matrix) != 3:
        errors.append("'craft_matrix' must be a list of 3 rows")
    else:
        for i, row in enumerate(matrix):
            if not isinstance(row, list) or len(row) != 3:
                errors.append(f"'craft_matrix[{i}]' must have 3 cells")
            else:
                for j, cell in enumerate(row):
                    if cell is not None and not isinstance(cell, str):
                        errors.append(f"'craft_matrix[{i}][{j}]' must be string or null")

    result = d.get("result")
    if not isinstance(result, dict) or not result.get("item_id"):
        errors.append("'result.item_id' is required")

    return errors


def _serialize(doc: dict) -> dict:
    doc["_id"] = str(doc["_id"])
    if "created_at" in doc:
        doc["created_at"] = doc["created_at"].isoformat()
    return doc


# ══════════════════════════════════════════════════════════════════════
#  VERSION HELPERS
# ══════════════════════════════════════════════════════════════════════

def _parse_ver(ver: str) -> tuple:
    try:
        return tuple(int(x) for x in ver.strip().split(".") if x.isdigit())
    except Exception:
        return (1, 12, 2)


def _is_legacy(ver: str) -> bool:
    """True для 1.7.x – 1.12.x → CraftTweaker. False для 1.13+ → Data Pack."""
    v = _parse_ver(ver)
    major = v[0] if len(v) > 0 else 1
    minor = v[1] if len(v) > 1 else 12
    return major == 1 and minor <= 12


# ══════════════════════════════════════════════════════════════════════
#  CRAFTTWEAKER GENERATORS (.zs) — 1.7.10 – 1.12.2
# ══════════════════════════════════════════════════════════════════════

def _to_ct(item_id: Optional[str]) -> str:
    return "null" if not item_id else f"<{item_id}>"


def _gen_ct_crafting(recipe: dict) -> str:
    matrix  = recipe.get("craft_matrix", [[None]*3]*3)
    result  = recipe.get("result", {})
    out_id  = result.get("item_id", "minecraft:air")
    count   = int(result.get("count", 1))
    out_ct  = _to_ct(out_id)
    if count > 1:
        out_ct = f"{out_ct} * {count}"
    rows = ",\n".join(
        "  [" + ", ".join(_to_ct(cell) for cell in row) + "]"
        for row in matrix
    )
    return f"// Верстак → {out_id}\nrecipes.addShaped({out_ct}, [\n{rows}\n]);\n"


def _gen_ct_furnace(recipe: dict, station: str) -> str:
    matrix = recipe.get("craft_matrix", [[None]*3]*3)
    inp    = matrix[0][0] if matrix and matrix[0] else None
    out_id = recipe.get("result", {}).get("item_id", "minecraft:air")
    label  = {"smelting":"Піч","blasting":"Доменна піч","smoking":"Коптильня","campfire":"Багаття"}.get(station, "Піч")
    return f"// {label} ({station}) → {out_id}\nfurnace.addRecipe({_to_ct(out_id)}, {_to_ct(inp)});\n"


def _gen_ct_stonecutter(recipe: dict) -> str:
    matrix = recipe.get("craft_matrix", [[None]*3]*3)
    inp    = matrix[0][0] if matrix and matrix[0] else None
    result = recipe.get("result", {})
    out_id = result.get("item_id", "minecraft:air")
    count  = int(result.get("count", 1))
    out_ct = _to_ct(out_id)
    if count > 1:
        out_ct = f"{out_ct} * {count}"
    return f"// Кам'яноріз (емульовано через shapeless) → {out_id}\nrecipes.addShapeless({out_ct}, [{_to_ct(inp)}]);\n"


def _gen_ct_smithing(recipe: dict) -> str:
    matrix   = recipe.get("craft_matrix", [[None]*3]*3)
    row0     = matrix[0] if matrix else [None, None, None]
    base     = row0[1] if len(row0) > 1 else None
    addition = row0[2] if len(row0) > 2 else None
    out_id   = recipe.get("result", {}).get("item_id", "minecraft:air")
    return (
        f"// Стіл коваля → {out_id}\n"
        f"// Base: {base}, Addition: {addition}\n"
        f"// (Smithing support via SmithingCraft or Forge CraftTweaker compat)\n"
    )


def _gen_ct_anvil(recipe: dict) -> str:
    matrix   = recipe.get("craft_matrix", [[None]*3]*3)
    row0     = matrix[0] if matrix else [None, None, None]
    base     = row0[0] if row0 else None
    material = row0[1] if len(row0) > 1 else None
    out_id   = recipe.get("result", {}).get("item_id", "minecraft:air")
    return (
        f"// Ковадло → {out_id}\n"
        f"// Base: {base}, Material: {material}\n"
        f"// (Anvil recipes via AnvilCraft or RepairableItems mod)\n"
    )


# ══════════════════════════════════════════════════════════════════════
#  DATA PACK GENERATORS (.json) — 1.13+
# ══════════════════════════════════════════════════════════════════════

_SYMBOLS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

_PACK_FORMAT_MAP: list[tuple[int, int]] = [
    (21, 48), (20, 15), (19, 10), (18, 9),
    (17, 7),  (16, 6),  (15, 5),  (14, 4), (13, 4),
]


def _get_pack_format(ver: str) -> int:
    v = _parse_ver(ver)
    minor = v[1] if len(v) > 1 else 13
    for min_minor, fmt in _PACK_FORMAT_MAP:
        if minor >= min_minor:
            return fmt
    return 4


def _matrix_to_pattern(matrix: list) -> tuple[list[str], dict]:
    sym_map: dict[str, str] = {}
    keys:    dict[str, dict] = {}
    idx = 0
    pattern: list[str] = []
    for row in matrix:
        row_str = ""
        for cell in row:
            if not cell:
                row_str += " "
            else:
                if cell not in sym_map:
                    sym = _SYMBOLS[idx % len(_SYMBOLS)]
                    idx += 1
                    sym_map[cell] = sym
                    keys[sym] = {"item": cell}
                row_str += sym_map[cell]
        pattern.append(row_str)
    while pattern and pattern[-1].strip() == "":
        pattern.pop()
    return pattern, keys


def _gen_dp_crafting(recipe: dict) -> Optional[dict]:
    matrix = recipe.get("craft_matrix", [[None]*3]*3)
    result = recipe.get("result", {})
    out_id = result.get("item_id", "")
    count  = int(result.get("count", 1))
    pattern, keys = _matrix_to_pattern(matrix)
    if not keys or not out_id:
        return None
    return {
        "type":    "minecraft:crafting_shaped",
        "pattern": pattern,
        "key":     keys,
        "result":  {"id": out_id, "count": count},
    }


def _gen_dp_furnace(recipe: dict, station: str) -> Optional[dict]:
    TYPE_MAP = {
        "smelting": "minecraft:smelting",
        "blasting": "minecraft:blasting",
        "smoking":  "minecraft:smoking",
        "campfire": "minecraft:campfire_cooking",
    }
    matrix      = recipe.get("craft_matrix", [[None]*3]*3)
    inp         = matrix[0][0] if matrix and matrix[0] else None
    result      = recipe.get("result", {})
    out_id      = result.get("item_id", "")
    experience  = recipe.get("experience", 0.7)
    cookingtime = recipe.get("cookingtime", 200)
    if not inp or not out_id:
        return None
    return {
        "type":        TYPE_MAP.get(station, "minecraft:smelting"),
        "ingredient":  {"item": inp},
        "result":      {"id": out_id, "count": 1},
        "experience":  float(experience),
        "cookingtime": int(cookingtime),
    }


def _gen_dp_stonecutting(recipe: dict) -> Optional[dict]:
    matrix = recipe.get("craft_matrix", [[None]*3]*3)
    inp    = matrix[0][0] if matrix and matrix[0] else None
    result = recipe.get("result", {})
    out_id = result.get("item_id", "")
    count  = int(result.get("count", 1))
    if not inp or not out_id:
        return None
    return {
        "type":       "minecraft:stonecutting",
        "ingredient": {"item": inp},
        "result":     {"id": out_id, "count": count},
    }


def _gen_dp_smithing(recipe: dict) -> Optional[dict]:
    matrix   = recipe.get("craft_matrix", [[None]*3]*3)
    row0     = matrix[0] if matrix else [None, None, None]
    template = row0[0] if len(row0) > 0 else None
    base     = row0[1] if len(row0) > 1 else None
    addition = row0[2] if len(row0) > 2 else None
    out_id   = recipe.get("result", {}).get("item_id", "")
    if not base or not out_id:
        return None
    obj: dict = {"type": "minecraft:smithing_transform", "result": {"id": out_id}}
    if template: obj["template"] = {"item": template}
    if base:     obj["base"]     = {"item": base}
    if addition: obj["addition"] = {"item": addition}
    return obj


def _gen_dp_brewing(recipe: dict) -> Optional[dict]:
    matrix  = recipe.get("craft_matrix", [[None]*3]*3)
    row0    = matrix[0] if matrix else [None, None, None]
    reagent = row0[0] if row0 else None
    base    = row0[1] if len(row0) > 1 else None
    out_id  = recipe.get("result", {}).get("item_id", "")
    if not reagent or not out_id:
        return None
    return {
        "type":    "custom:brewing",
        "_note":   "Vanilla brewing lacks Data Pack support. Use PotionCore or similar mod.",
        "reagent": {"item": reagent},
        "base":    {"item": base} if base else {"tag": "minecraft:brewed_potions"},
        "result":  {"id": out_id},
    }


# ══════════════════════════════════════════════════════════════════════
#  STATION DISPATCH — вибирає генератор за типом станції
# ══════════════════════════════════════════════════════════════════════

def _dispatch(recipe: dict, station: str) -> tuple[Optional[str], Optional[dict]]:
    """Повертає (legacy_str, modern_dict) для рецепту з урахуванням станції."""
    s = station or "crafting"
    if s == "crafting":
        return _gen_ct_crafting(recipe), _gen_dp_crafting(recipe)
    if s in ("smelting", "blasting", "smoking", "campfire"):
        return _gen_ct_furnace(recipe, s), _gen_dp_furnace(recipe, s)
    if s == "stonecutting":
        return _gen_ct_stonecutter(recipe), _gen_dp_stonecutting(recipe)
    if s == "smithing":
        return _gen_ct_smithing(recipe), _gen_dp_smithing(recipe)
    if s == "anvil":
        return _gen_ct_anvil(recipe), None
    if s == "brewing":
        return None, _gen_dp_brewing(recipe)
    return _gen_ct_crafting(recipe), _gen_dp_crafting(recipe)


# ══════════════════════════════════════════════════════════════════════
#  ZIP BUILDER
# ══════════════════════════════════════════════════════════════════════

def _collect_mod_deps(recipes: list) -> list[str]:
    mods: set[str] = set()
    for r in recipes:
        for row in r.get("craft_matrix", []):
            for cell in (row or []):
                if cell and ":" in cell and cell.split(":")[0] != "minecraft":
                    mods.add(cell.split(":")[0])
        rid = r.get("result", {}).get("item_id", "")
        if rid and ":" in rid and rid.split(":")[0] != "minecraft":
            mods.add(rid.split(":")[0])
    return sorted(mods)


def _write_manifest(base_dir: str, ver: str, recipes: list, extra: dict) -> None:
    manifest = {
        "generated_at":     datetime.now(timezone.utc).isoformat(),
        "game_version":     ver,
        "recipe_count":     len(recipes),
        "mod_dependencies": _collect_mod_deps(recipes),
        **extra,
    }
    with open(os.path.join(base_dir, "manifest.json"), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2, ensure_ascii=False)


def _pack_to_zip(src_dir: str, zip_path: str) -> None:
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _dirs, files in os.walk(src_dir):
            for fname in files:
                full = os.path.join(root, fname)
                zf.write(full, os.path.relpath(full, src_dir))


def _build_legacy_pack(recipes: list, ver: str, base_dir: str) -> None:
    scripts_dir = os.path.join(base_dir, "scripts")
    os.makedirs(scripts_dir, exist_ok=True)
    header = (
        f"// Modpack Recipes — Minecraft {ver}\n"
        f"// Згенеровано: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC\n"
        f"// Вимагає: CraftTweaker мод\n\n"
        "import crafttweaker.item.IItemStack;\n\n"
    )
    lines = []
    for r in recipes:
        legacy, _ = _dispatch(r, r.get("station", "crafting"))
        if legacy:
            lines.append(legacy)
    with open(os.path.join(scripts_dir, "modpack_recipes.zs"), "w", encoding="utf-8") as fh:
        fh.write(header + "\n".join(lines))
    _write_manifest(base_dir, ver, recipes, {
        "format":       "CraftTweaker (.zs scripts)",
        "required_mod": "CraftTweaker",
        "install_path": ".minecraft/scripts/",
    })


def _build_datapack(recipes: list, ver: str, base_dir: str) -> None:
    namespace  = "modpack"
    pack_fmt   = _get_pack_format(ver)
    recipe_dir = os.path.join(base_dir, "data", namespace, "recipe")
    os.makedirs(recipe_dir, exist_ok=True)

    mcmeta = {"pack": {"pack_format": pack_fmt,
                       "description": f"Custom recipes for MC {ver}"}}
    with open(os.path.join(base_dir, "pack.mcmeta"), "w", encoding="utf-8") as fh:
        json.dump(mcmeta, fh, indent=2, ensure_ascii=False)

    counter: dict[str, int] = {}
    for recipe in recipes:
        station = recipe.get("station", "crafting")
        _, modern = _dispatch(recipe, station)
        if not modern:
            continue
        base_name = recipe["result"]["item_id"].replace(":", "_").replace("/", "_")
        if station != "crafting":
            base_name = f"{station}_{base_name}"
        n = counter.get(base_name, 0)
        counter[base_name] = n + 1
        fname = f"{base_name}{'_' + str(n) if n else ''}.json"
        with open(os.path.join(recipe_dir, fname), "w", encoding="utf-8") as fh:
            json.dump(modern, fh, indent=2, ensure_ascii=False)

    _write_manifest(base_dir, ver, recipes, {
        "format":       "Vanilla Data Pack (JSON recipes)",
        "pack_format":  pack_fmt,
        "install_path": ".minecraft/saves/<world>/datapacks/",
    })


def build_modpack_zip(recipes: list, game_version: str) -> str:
    tmp  = tempfile.mkdtemp(prefix="mcbuild_")
    fd, zpath = tempfile.mkstemp(suffix=".zip")
    os.close(fd)
    try:
        if _is_legacy(game_version):
            _build_legacy_pack(recipes, game_version, tmp)
        else:
            _build_datapack(recipes, game_version, tmp)
        _pack_to_zip(tmp, zpath)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return zpath


# ══════════════════════════════════════════════════════════════════════
#  AUTH ROUTES
# ══════════════════════════════════════════════════════════════════════

@app.post("/auth/login")
def auth_login():
    """POST /auth/login  Body: {username, password}"""
    data     = request.get_json(silent=True) or {}
    username = str(data.get("username", "")).strip().lower()
    password = str(data.get("password", ""))

    # 1) Перевірка у захардкоджених демо-акаунтах
    user = USERS.get(username)
    if user:
        if user["password"] != password:
            return jsonify({"error": "Невірний логін або пароль"}), 401
        role    = user["role"]
        display = user["display"]
    else:
        # 2) Перевірка у MongoDB (зареєстровані користувачі)
        db_user = _col_users().find_one({"username": username})
        if not db_user or not check_password_hash(db_user.get("password_hash", ""), password):
            return jsonify({"error": "Невірний логін або пароль"}), 401
        role    = db_user.get("role", "user")
        display = db_user.get("display", username)

    session.permanent   = True
    session["username"] = username
    session["role"]     = role

    return jsonify({
        "message":  "Login successful",
        "username": username,
        "role":     role,
        "display":  display,
    })


@app.post("/auth/register")
def auth_register():
    """POST /auth/register  Body: {username, password, confirm}"""
    data     = request.get_json(silent=True) or {}
    username = str(data.get("username", "")).strip().lower()
    password = str(data.get("password", ""))
    confirm  = str(data.get("confirm",  ""))

    # Валідація
    if len(username) < 4:
        return jsonify({"error": "Логін повинен містити щонайменше 4 символи"}), 400
    if not re.match(r"^[a-z0-9_\-]+$", username):
        return jsonify({"error": "Логін може містити лише латинські літери, цифри, _ та -"}), 400
    if len(password) < 4:
        return jsonify({"error": "Пароль повинен містити щонайменше 4 символи"}), 400
    if password != confirm:
        return jsonify({"error": "Паролі не збігаються"}), 400
    if username in USERS:
        return jsonify({"error": "Цей логін зарезервований. Оберіть інший"}), 409

    # Перевірка унікальності у MongoDB
    if _col_users().find_one({"username": username}):
        return jsonify({"error": "Користувач з таким логіном вже існує"}), 409

    _col_users().insert_one({
        "username":      username,
        "password_hash": generate_password_hash(password),
        "role":          "user",
        "display":       username,
        "created_at":    datetime.now(timezone.utc),
    })

    return jsonify({"message": "Реєстрація успішна! Тепер увійдіть у систему.", "username": username}), 201


@app.get("/auth/logout")
def auth_logout():
    session.clear()
    return jsonify({"message": "Logged out"})


@app.get("/api/auth/me")
def auth_me():
    if "username" not in session:
        return jsonify({"error": "Not authenticated"}), 401
    username = session["username"]
    u = USERS.get(username)
    if u:
        display = u.get("display", username)
    else:
        db_user = _col_users().find_one({"username": username})
        display = db_user.get("display", username) if db_user else username
    return jsonify({
        "username": username,
        "role":     session.get("role", "user"),
        "display":  display,
    })


# ══════════════════════════════════════════════════════════════════════
#  ITEMS ROUTES
# ══════════════════════════════════════════════════════════════════════

@app.get("/api/items")
@login_required
def api_list_items():
    version = request.args.get("version")
    mod     = request.args.get("mod")
    search  = request.args.get("search", "").strip()
    page    = max(int(request.args.get("page",  1)), 1)
    limit   = min(max(int(request.args.get("limit", 200)), 1), 500)
    skip    = (page - 1) * limit

    query: dict = {}
    if version:
        query["$or"] = [{"version": version}, {"version": "universal"}]
    if mod:     query["mod"]     = mod.lower()
    if search:  query["name"]    = {"$regex": re.escape(search), "$options": "i"}

    col   = _col_items()
    total = col.count_documents(query)
    docs  = list(
        col.find(query, {"created_at": 0})
           .sort("name", ASCENDING)
           .skip(skip).limit(limit)
    )
    for d in docs:
        d["_id"] = str(d["_id"])

    return jsonify({
        "data": docs,
        "meta": {"total": total, "page": page, "limit": limit,
                  "pages": (total + limit - 1) // limit},
    })


@app.post("/api/items")
@admin_required
def api_create_item():
    data = request.get_json(silent=True) or {}
    errs = _validate_item(data)
    if errs:
        return jsonify({"errors": errs}), 400
    col = _col_items()
    if col.find_one({"item_id": data["item_id"].lower(), "version": data["version"]}):
        return jsonify({"error": "Item already exists for this version"}), 409
    doc = {
        "item_id":    data["item_id"].strip().lower(),
        "name":       data["name"].strip(),
        "version":    data["version"].strip(),
        "icon":       data.get("icon",  ""),
        "emoji":      data.get("emoji", ""),
        "mod":        data["mod"].strip().lower(),
        "created_at": datetime.now(timezone.utc),
    }
    res = col.insert_one(doc)
    doc["_id"] = str(res.inserted_id)
    doc.pop("created_at")
    return jsonify({"data": doc, "message": "Item created"}), 201


@app.get("/api/items/<item_id>")
@login_required
def api_get_item(item_id: str):
    try:
        doc = _col_items().find_one({"_id": ObjectId(item_id)}, {"created_at": 0})
    except InvalidId:
        return jsonify({"error": "Invalid ObjectId"}), 400
    if not doc:
        return jsonify({"error": "Item not found"}), 404
    doc["_id"] = str(doc["_id"])
    return jsonify({"data": doc})


@app.delete("/api/items/<item_id>")
@admin_required
def api_delete_item(item_id: str):
    try:
        res = _col_items().delete_one({"_id": ObjectId(item_id)})
    except InvalidId:
        return jsonify({"error": "Invalid ObjectId"}), 400
    if res.deleted_count == 0:
        return jsonify({"error": "Item not found"}), 404
    return jsonify({"message": "Item deleted"})


# ══════════════════════════════════════════════════════════════════════
#  RECIPES ROUTES
# ══════════════════════════════════════════════════════════════════════

@app.get("/api/recipes")
@login_required
def api_list_recipes():
    """user бачить тільки свої рецепти; admin — всі."""
    user_id = request.args.get("user_id")
    version = request.args.get("game_version")
    page    = max(int(request.args.get("page",  1)), 1)
    limit   = min(max(int(request.args.get("limit", 50)), 1), 200)
    skip    = (page - 1) * limit

    query: dict = {}
    if session.get("role") == "admin":
        if user_id:
            query["user_id"] = str(user_id)
    else:
        query["user_id"] = session["username"]

    if version:
        query["game_version"] = version

    col   = _col_recipes()
    total = col.count_documents(query)
    docs  = list(col.find(query).sort("created_at", DESCENDING).skip(skip).limit(limit))
    for d in docs:
        _serialize(d)

    return jsonify({"data": docs, "meta": {"total": total, "page": page, "limit": limit}})


@app.post("/api/recipes")
@login_required
def api_create_recipe():
    data = request.get_json(silent=True) or {}
    data["user_id"] = session["username"]   # завжди із сесії

    errs = _validate_recipe(data)
    if errs:
        return jsonify({"errors": errs}), 400

    doc = {
        "user_id":      session["username"],
        "game_version": data["game_version"].strip(),
        "station":      data.get("station", "crafting"),
        "craft_matrix": data["craft_matrix"],
        "experience":   data.get("experience"),
        "cookingtime":  data.get("cookingtime"),
        "result": {
            "item_id": data["result"]["item_id"].strip(),
            "count":   int(data["result"].get("count", 1)),
        },
        "created_at": datetime.now(timezone.utc),
    }
    res = _col_recipes().insert_one(doc)
    doc["_id"] = str(res.inserted_id)
    doc.pop("created_at")
    return jsonify({"data": doc, "message": "Recipe saved"}), 201


@app.get("/api/recipes/<recipe_id>")
@login_required
def api_get_recipe(recipe_id: str):
    try:
        doc = _col_recipes().find_one({"_id": ObjectId(recipe_id)})
    except InvalidId:
        return jsonify({"error": "Invalid ObjectId"}), 400
    if not doc:
        return jsonify({"error": "Recipe not found"}), 404
    if session.get("role") != "admin" and doc.get("user_id") != session["username"]:
        return jsonify({"error": "Access denied"}), 403
    return jsonify({"data": _serialize(doc)})


@app.delete("/api/recipes/<recipe_id>")
@login_required
def api_delete_recipe(recipe_id: str):
    try:
        doc = _col_recipes().find_one({"_id": ObjectId(recipe_id)})
    except InvalidId:
        return jsonify({"error": "Invalid ObjectId"}), 400
    if not doc:
        return jsonify({"error": "Recipe not found"}), 404
    if session.get("role") != "admin" and doc.get("user_id") != session["username"]:
        return jsonify({"error": "You can only delete your own recipes"}), 403
    _col_recipes().delete_one({"_id": ObjectId(recipe_id)})
    return jsonify({"message": "Recipe deleted"})


# ══════════════════════════════════════════════════════════════════════
#  EXPORT ROUTE
# ══════════════════════════════════════════════════════════════════════

@app.post("/api/export")
@login_required
def api_export():
    data         = request.get_json(silent=True) or {}
    game_version = data.get("game_version", "").strip()
    if not game_version:
        return jsonify({"error": "'game_version' is required"}), 400

    recipes: list = data.get("recipes") or []
    if not recipes:
        uid    = data.get("user_id") or session["username"]
        cursor = _col_recipes().find({"user_id": str(uid), "game_version": game_version})
        recipes = [_serialize(r) for r in cursor]
    if not recipes:
        return jsonify({"error": f"No recipes found for version '{game_version}'."}), 404

    for i, r in enumerate(recipes):
        if not isinstance(r.get("craft_matrix"), list):
            return jsonify({"error": f"recipes[{i}].craft_matrix must be a list"}), 400
        if not r.get("result", {}).get("item_id"):
            return jsonify({"error": f"recipes[{i}].result.item_id is required"}), 400

    fmt = "CraftTweaker (.zs)" if _is_legacy(game_version) else "Data Pack (JSON)"
    app.logger.info(f"Generating {fmt}: {len(recipes)} recipes for MC {game_version}")

    try:
        zip_path = build_modpack_zip(recipes, game_version)
    except Exception as exc:
        app.logger.error(f"Pack generation failed: {exc}")
        return jsonify({"error": f"Pack generation failed: {exc}"}), 500

    @after_this_request
    def _cleanup(response):
        def _defer():
            time.sleep(10)
            try:
                os.remove(zip_path)
            except OSError:
                pass
        threading.Thread(target=_defer, daemon=True).start()
        return response

    safe = game_version.replace(".", "_")
    return send_file(zip_path, as_attachment=True,
                     download_name=f"modpack_{safe}.zip",
                     mimetype="application/zip")


# ══════════════════════════════════════════════════════════════════════
#  ADMIN ROUTES
# ══════════════════════════════════════════════════════════════════════

@app.get("/api/admin/stats")
@admin_required
def api_admin_stats():
    col_r = _col_recipes()
    col_i = _col_items()

    total_recipes = col_r.count_documents({})
    total_items   = col_i.count_documents({})
    unique_users  = col_r.distinct("user_id")

    by_version = list(col_r.aggregate([
        {"$group": {"_id": "$game_version", "count": {"$sum": 1}}},
        {"$sort":  {"count": -1}},
    ]))
    by_station = list(col_r.aggregate([
        {"$group": {"_id": {"$ifNull": ["$station", "crafting"]}, "count": {"$sum": 1}}},
        {"$sort":  {"count": -1}},
    ]))

    return jsonify({
        "total_recipes": total_recipes,
        "total_items":   total_items,
        "unique_users":  len(unique_users),
        "users_list":    unique_users,
        "by_version":    [{"version": b["_id"], "count": b["count"]} for b in by_version],
        "by_station":    [{"station": b["_id"], "count": b["count"]} for b in by_station],
    })


@app.get("/api/admin/recipes")
@admin_required
def api_admin_recipes():
    """Всі рецепти з фільтрацією (admin only)."""
    user_id = request.args.get("user_id")
    version = request.args.get("game_version")
    page    = max(int(request.args.get("page",  1)), 1)
    limit   = min(max(int(request.args.get("limit", 50)), 1), 200)
    skip    = (page - 1) * limit

    query: dict = {}
    if user_id: query["user_id"]      = user_id
    if version: query["game_version"] = version

    col   = _col_recipes()
    total = col.count_documents(query)
    docs  = list(col.find(query).sort("created_at", DESCENDING).skip(skip).limit(limit))
    for d in docs:
        _serialize(d)

    return jsonify({"data": docs, "meta": {"total": total, "page": page, "limit": limit}})


# ══════════════════════════════════════════════════════════════════════
#  HEALTH & ROOT
# ══════════════════════════════════════════════════════════════════════

@app.get("/health")
def health():
    try:
        _get_db().command("ping")
        db_status = "connected"
    except Exception as exc:
        db_status = f"error: {exc}"
    return jsonify({"status": "ok", "database": db_status})


@app.get("/")
def root():
    return render_template("index.html")


# ══════════════════════════════════════════════════════════════════════
#  ERROR HANDLERS
# ══════════════════════════════════════════════════════════════════════

@app.errorhandler(400)
def err_400(e): return jsonify({"error": "Bad request", "detail": str(e)}), 400
@app.errorhandler(404)
def err_404(e): return jsonify({"error": "Not found"}), 404
@app.errorhandler(405)
def err_405(e): return jsonify({"error": "Method not allowed"}), 405
@app.errorhandler(500)
def err_500(e): return jsonify({"error": "Internal server error"}), 500


# ══════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    _ensure_indexes()
    app.run(host="0.0.0.0", port=PORT, debug=DEBUG)
