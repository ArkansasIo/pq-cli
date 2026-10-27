from enum import StrEnum


class RaceId(StrEnum):
    HUMAN = "human"
    ELF = "elf"
    DWARF = "dwarf"
    ORC = "orc"
    HALFLING = "halfling"
    UNDEAD = "undead"
    DRACONIC = "draconic"


class ClassId(StrEnum):
    WARRIOR = "warrior"
    PALADIN = "paladin"
    ROGUE = "rogue"
    RANGER = "ranger"
    MAGE = "mage"
    CLERIC = "cleric"
    WARLOCK = "warlock"
    BARD = "bard"


class DamageType(StrEnum):
    PHYSICAL = "physical"
    FIRE = "fire"
    FROST = "frost"
    ARCANE = "arcane"
    HOLY = "holy"
    SHADOW = "shadow"
    POISON = "poison"
    NATURE = "nature"


class Rarity(StrEnum):
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"
    MYTHIC = "mythic"


class EquipmentSlot(StrEnum):
    HEAD = "head"
    CHEST = "chest"
    LEGS = "legs"
    FEET = "feet"
    HANDS = "hands"
    MAIN_HAND = "main_hand"
    OFF_HAND = "off_hand"
    NECK = "neck"
    RING_1 = "ring_1"
    RING_2 = "ring_2"
    TRINKET_1 = "trinket_1"
    TRINKET_2 = "trinket_2"


class QuestStatus(StrEnum):
    AVAILABLE = "available"
    ACTIVE = "active"
    COMPLETE = "complete"
    FAILED = "failed"


class FactionStanding(StrEnum):
    HOSTILE = "hostile"
    UNFRIENDLY = "unfriendly"
    NEUTRAL = "neutral"
    FRIENDLY = "friendly"
    HONORED = "honored"
    REVERED = "revered"
    EXALTED = "exalted"
