"""Explicit Qt actions over the unchanged save engine and its entity schema."""
from collections import Counter
import modifiers


def set_material_quantity(save, item_id, quantity):
    """Set locker stock, leaving bag entities and unrelated slot metadata intact."""
    quantity = int(quantity)
    if quantity < 0:
        raise ValueError("Quantity cannot be negative")
    section, key, id_key = (
        ("mushroom", "msrs", "msrid") if item_id.startswith("MSR_") else
        ("beast", "bsts", "bstid") if item_id.startswith("BST_") else
        ("item", "items", "itemid")
    )
    entities = save.get(section, {}).get(key, [])
    matches = [e for e in entities if isinstance(e, dict)
               and e.get(id_key) == item_id and e.get("owner") == "COIN_LOCKER"]
    if quantity > len(matches):
        delta = quantity - len(matches)
        slots = save.get("soul", {}).get("cl", [])
        free = sum(1 for s in slots if s.get("type") == -1 or not s.get("eid"))
        if delta > free + max(0, 10000 - len(slots)):
            raise ValueError("Insufficient Coin Locker capacity")
        modifiers.add_material_to_storage(save, item_id, count=delta)
    elif quantity < len(matches):
        removed = matches[quantity:]
        removed_objects = {id(e) for e in removed}
        removed_eids = {e.get("eid") for e in removed if e.get("eid")}
        entities[:] = [e for e in entities if id(e) not in removed_objects]
        for slot in save.get("soul", {}).get("cl", []):
            if slot.get("eid") in removed_eids:
                slot.update(type=-1, eid="")
    return quantity


def inventory_counts(save):
    """Group real entities by ID, location, category, level and cooked state."""
    counts = Counter()
    sources = [
        (save.get("item", {}).get("items", []), "itemid", "MATS"),
        (save.get("mushroom", {}).get("msrs", []), "msrid", "SHROOMS"),
        (save.get("beast", {}).get("bsts", []), "bstid", "SHROOMS"),
    ]
    parts = save.get("part", {}).get("pts", [])
    if isinstance(parts, dict):
        parts = [e for group in parts.values() for e in (group if isinstance(group, list) else [group])]
    sources.append((parts, "ptid", "GEAR"))
    for entities, id_key, category in sources:
        for entity in entities:
            if not isinstance(entity, dict) or not entity.get(id_key):
                continue
            owner = entity.get("owner", "COIN_LOCKER")
            count = 1 if entity.get("eid") else max(0, int(entity.get("count", 1)))
            counts[(entity[id_key], owner, category, entity.get("lvl", 1), entity.get("state", 0))] += count
    return counts
