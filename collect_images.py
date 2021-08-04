import os
import json
import shutil

from lib.paths import ASSETS

IMAGES = os.path.join(ASSETS, "images")
os.makedirs(IMAGES, exist_ok=True)

# 1. load the masterdata of both versions
data = {}
for ver in ["gl", "jp"]:
    data[ver] = {}
    p = os.path.join(ASSETS, ver, "extracted", "master")
    for elem in ["Character", "Style", "DramaCharacter", "Costume", "StyleIllust"]:
        with open(os.path.join(p, f"{elem}.json"), "rt", encoding="utf8") as f:
            data[ver][elem] = {x["id"] : x for x in json.load(f)["objectArray"]}

# 2. merge global and japan, prefer global (to keep the translation)
for key, vdict in data["jp"].items():
    gdict = data["gl"][key]
    for iid, item in vdict.items():
        if iid not in gdict:
            # annotate that the item is from the jp version, important to find the correct path
            item["origin"] = "jp"
            gdict[iid] = item
data = data["gl"]
# 3. assign styles and costumes to their characters and resolve the styleillus
for key in ["Costume", "Style"]:
    for item in data[key].values():
        char = data["Character"][item["character_id"]]
        if key not in char:
            char[key] = []
        char[key].append(item)

# 4. store in new folder
forbidden = {
    "<" : "＜",
    ">" : "＞",
    ":" : "：",
    "\"" : "",
    "/" : "／",
    "\\" : "＼",
    "|" : "⏐",
    "?" : "？",
    "*" : "＊",
}
def replace_forbidden_characters(string):
    for ori, rep in forbidden.items():
        string = string.replace(ori, rep)
    return string

for key in ["Costume", "Style"]:
    dir = os.path.join(IMAGES, key)
    os.makedirs(dir, exist_ok=True)
    for cid, char in data["Character"].items():
        for item in char.get(key, []):
            illust_item = data["StyleIllust"][item["style_illust_id"]]
            illust = str(illust_item['illust_id'])
            
            src = os.path.join(ASSETS, item.get("origin", "gl"), "extracted", "texture", "style", illust, f"style_{illust}.png")
            dst = os.path.join(dir, replace_forbidden_characters(f"{char['name']} - {item.get('another_name', item.get('name'))} - clean.png"))
            shutil.copy(src, dst)

            if illust_item["has_background"] or illust_item["has_front"]:
                print()
