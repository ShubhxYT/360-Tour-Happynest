#!/usr/bin/env python3
"""Transform the live tour.json into the optimized multires config."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from labels import humanize, hotspot_text, menu_groups

LIVE = Path("/workspace/360-tour-work/live/tour.json")
OUT = Path("/workspace/360-tour-work/site/tour.json")
TILES = Path("/workspace/360-tour-work/site/assets/tiles")


def scene_multires(scene_id: str) -> dict:
    cfg_path = TILES / scene_id / "config.json"
    if cfg_path.exists():
        multi = json.loads(cfg_path.read_text())["multiRes"]
    else:
        multi = {
            "path": "/%l/%s%y_%x",
            "fallbackPath": "/fallback/%s",
            "extension": "webp",
            "tileResolution": 512,
            "maxLevel": 3,
            "cubeResolution": 2048,
        }
    multi = dict(multi)
    multi["basePath"] = f"assets/tiles/{scene_id}"
    return multi


def main() -> None:
    src = json.loads(LIVE.read_text())
    out = {
        "default": {
            **src["default"],
            "title": "HappyNest Blanc Belle",
        },
        "scenes": {},
        "menu": menu_groups(),
    }
    for sid, sc in src["scenes"].items():
        spots = []
        for hs in sc.get("hotSpots") or []:
            item = dict(hs)
            if item.get("type") == "scene" and item.get("sceneId"):
                item["text"] = hotspot_text(sid, item["sceneId"], item.get("text"))
            spots.append(item)
        out["scenes"][sid] = {
            "title": humanize(sid),
            "type": "multires",
            "preview": sc.get("preview") or f"assets/preview/{sid}.jpg",
            "hfov": sc.get("hfov", 100),
            "maxHfov": sc.get("maxHfov", 120),
            "minHfov": sc.get("minHfov", 50),
            "multiRes": scene_multires(sid),
            "hotSpots": spots,
        }
    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n")
    print(f"wrote {OUT} scenes={len(out['scenes'])} menu_groups={len(out['menu'])}")
    # sanity: leftover bad labels
    bad = []
    for sid, sc in out["scenes"].items():
        for hs in sc["hotSpots"]:
            t = hs.get("text") or ""
            if t in {"tKCc5PMy", "Drawning room 4"} or (t and t[0].islower() and " " not in t and t != "tKCc5PMy"):
                bad.append((sid, hs.get("sceneId"), t))
            if "Drawning" in t:
                bad.append((sid, hs.get("sceneId"), t))
    print("bad labels", bad)
    # sample
    print("FrontSide labels:", [h["text"] for h in out["scenes"]["FrontSideOfVilla"]["hotSpots"]])
    print("DrawingRoomTwo ->", [h["text"] for h in out["scenes"]["DrawingRoomTwo"]["hotSpots"]])
    print("FirstFloorDrawingRoomTwo ->", [h["text"] for h in out["scenes"]["FirstFloorDrawingRoomTwo"]["hotSpots"]])


if __name__ == "__main__":
    main()
