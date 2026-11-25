"""Human-readable labels and menu groups for HappyNest tour scenes."""
from __future__ import annotations
import re

# Explicit overrides where camel-case splitting isn't enough.
OVERRIDES = {
    "FrontSideOfVilla": "Front of the Villa",
    "GuestEntryRoad": "Driveway",
    "FrontLawnBadminton": "Badminton Court",
    "FrontLawnOne": "Front Lawn",
    "FrontLawnTwo": "Front Lawn 2",
    "BackLawnFour": "Back Lawn",
    "BackLawnOne": "Back Lawn 2",
    "BackLawnHut": "Back Lawn Hut",
    "CricketNetArea": "Cricket Net",
    "PoolAreaOne": "Pool",
    "PoolAreaTwo": "Pool 2",
    "RoofOne": "Roof",
    "RoofTwo": "Roof 2",
    "RoofFour": "Roof 3",
    "DrawingRoomTwo": "Drawing Room 2",
    "DrawingRoomThree": "Drawing Room 3",
    "DrawingRoomFour": "Drawing Room 4",
    "DarkBlueRoom": "Dark Blue Room",
    "DarkBlueRoomBathroom": "Dark Blue Room Bathroom",
    "DarkGreyRoom": "Dark Grey Room",
    "DarkGreyRoomWashroom": "Dark Grey Room Bathroom",
    "GreenRoom": "Green Room",
    "GreenRoomWashroom": "Green Room Bathroom",
    "PeachRoom": "Peach Room",
    "PeachRoomWashroom": "Peach Room Bathroom",
    "FirstFloorAquaBlueRoom": "Aqua Blue Room (1st floor)",
    "FirstFloorAquaBlueRoomWashroom": "Aqua Blue Room Bathroom (1st floor)",
    "FirstFloorDarkGreyRoom": "Dark Grey Room (1st floor)",
    "FirstFloorDarkGreyRoomWashroom": "Dark Grey Room Bathroom (1st floor)",
    "FirstFloorDrawingRoomOne": "Drawing Room 1 (1st floor)",
    "FirstFloorDrawingRoomTwo": "Drawing Room 2 (1st floor)",
    "FirstFloorBalconyOne": "Balcony 1 (1st floor)",
    "FirstFloorBalconyTwo": "Balcony 2 (1st floor)",
    "FirstFloorStairs": "Stairs (1st floor)",
    "FirstFloorWalkingPath": "Hallway (1st floor)",
}

# Hotspot text that should be kept rather than derived from the destination.
KEEP_TEXT = {
    "Go Down",
}

# Destination-specific hotspot wording
HOTSPOT_BY_EDGE = {
    ("RoofTwo", "PoolAreaTwo"): "Go Down",
    ("RoofFour", "FrontSideOfVilla"): "Go Down",
}

OUTDOORS = {
    "FrontSideOfVilla", "GuestEntryRoad", "FrontLawnOne", "FrontLawnTwo",
    "FrontLawnBadminton", "BackLawnFour", "BackLawnOne", "BackLawnHut",
    "CricketNetArea", "PoolAreaOne", "PoolAreaTwo",
}
ROOF = {"RoofOne", "RoofTwo", "RoofFour"}
FIRST_FLOOR = {
    "FirstFloorStairs", "FirstFloorWalkingPath",
    "FirstFloorDrawingRoomOne", "FirstFloorDrawingRoomTwo",
    "FirstFloorAquaBlueRoom", "FirstFloorAquaBlueRoomWashroom",
    "FirstFloorDarkGreyRoom", "FirstFloorDarkGreyRoomWashroom",
    "FirstFloorBalconyOne", "FirstFloorBalconyTwo",
    "PeachRoom", "PeachRoomWashroom",
    "DarkBlueRoom", "DarkBlueRoomBathroom",
}
# Remaining ground-floor interiors
GROUND = {
    "DrawingRoomTwo", "DrawingRoomThree", "DrawingRoomFour",
    "GreenRoom", "GreenRoomWashroom",
    "DarkGreyRoom", "DarkGreyRoomWashroom",
}

MENU_GROUPS = [
    ("Grounds", [
        "FrontSideOfVilla", "GuestEntryRoad", "FrontLawnOne", "FrontLawnTwo",
        "FrontLawnBadminton", "BackLawnFour", "BackLawnOne", "BackLawnHut",
        "CricketNetArea", "PoolAreaOne", "PoolAreaTwo",
    ]),
    ("Ground floor", [
        "DrawingRoomFour", "DrawingRoomThree", "DrawingRoomTwo",
        "GreenRoom", "GreenRoomWashroom",
        "DarkGreyRoom", "DarkGreyRoomWashroom",
    ]),
    ("First floor", [
        "FirstFloorStairs", "FirstFloorWalkingPath",
        "FirstFloorDrawingRoomOne", "FirstFloorDrawingRoomTwo",
        "FirstFloorAquaBlueRoom", "FirstFloorAquaBlueRoomWashroom",
        "DarkBlueRoom", "DarkBlueRoomBathroom",
        "FirstFloorDarkGreyRoom", "FirstFloorDarkGreyRoomWashroom",
        "PeachRoom", "PeachRoomWashroom",
        "FirstFloorBalconyOne", "FirstFloorBalconyTwo",
    ]),
    ("Roof", ["RoofOne", "RoofTwo", "RoofFour"]),
]


def humanize(scene_id: str) -> str:
    if scene_id in OVERRIDES:
        return OVERRIDES[scene_id]
    floor = ""
    s = scene_id
    if s.startswith("FirstFloor"):
        floor = " (1st floor)"
        s = s[len("FirstFloor"):]
    bath = ""
    if s.endswith("Washroom") or s.endswith("Bathroom"):
        bath = " Bathroom"
        s = re.sub(r"(Washroom|Bathroom)$", "", s)
    s = re.sub(r"([a-z])([A-Z])", r"\1 \2", s)
    s = re.sub(r"([A-Za-z])(\d)", r"\1 \2", s)
    return (s + bath + floor).strip()


def hotspot_text(from_scene: str, to_scene: str, original: str | None = None) -> str:
    if (from_scene, to_scene) in HOTSPOT_BY_EDGE:
        return HOTSPOT_BY_EDGE[(from_scene, to_scene)]
    if original in KEEP_TEXT:
        return original
    return humanize(to_scene)


def menu_groups() -> list[dict]:
    return [
        {"name": name, "scenes": [{"id": s, "title": humanize(s)} for s in ids]}
        for name, ids in MENU_GROUPS
    ]
