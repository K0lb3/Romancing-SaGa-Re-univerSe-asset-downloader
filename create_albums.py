import os
from lib.paths import ASSETS
from lib.convert_sound import sound_to_wav
import json
import shutil

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

def load_master(region, name):
    with open(os.path.join(ASSETS, region, "extracted", "master", f"{name}.json"), "rt", encoding="utf8") as f:
        ret = json.load(f)
    return {item["id"]:item for item in ret["objectArray"]}

def load_merged(name):
    gl = load_master("gl", name)
    for item in gl.values():
        item["origin"] = "gl"
    jp = load_master("jp", name)
    jp.update(gl)
    return jp


# 1. collect all albums
albums  = load_merged("MusicAlbum")

# 2. add tracks to albums
tracks = load_merged("MusicTrack")
for tid, track in tracks.items():
    album = albums[track["music_album_id"]]
    if "tracks" not in album:
        album["tracks"] = []
    album["tracks"].append(track)

# 3. extract tracks to album folder
sounds = load_merged("Sound")

for album in albums.values():
    print(album["name"])
    album_folder = os.path.join(ASSETS, "albums", replace_forbidden_characters(album["name"]))
    os.makedirs(album_folder, exist_ok=True)

    # info
    with open(os.path.join(album_folder, "info.txt"), "wt", encoding="utf8") as f:
        f.write(album["name"])
        f.write("\n")
        f.write(album["flavor_text"])
        f.write("\n\ntracks:\n")
        for i, track in enumerate(sorted(album["tracks"], key = lambda item:item["sort_order"])):
            f.write(f"{i}. {track['name']} - {track['composer']}\n")
        f.write("\n")

    # album art
    shutil.copy(
        os.path.join(ASSETS, album.get("origin", "jp"), "extracted", "texture", "concerthall", "album", f"concert_hall_album_{album['icon']}.png"),
        os.path.join(album_folder, "cover.png")
    )

    # tracks
    for i, track in enumerate(sorted(album["tracks"], key = lambda item:item["sort_order"])):
        print(i, track["name"])
        sound = sounds[track["sound_id"]]
        sound_folder = os.path.join(ASSETS, track.get("origin", "jp"), "extracted", "sound", sound["cueSheetName"].lower())
        if not os.path.exists(sound_folder):
            sound_folder = os.path.join(ASSETS, "jp" if track.get("origin", "jp") == "gl" else "jp", "extracted", "sound", sound["cueSheetName"].lower())
        if not os.path.exists(sound_folder):
            print(sound_folder, "not found!!!!!")
            continue
        wav_path = os.path.join(album_folder, f"{i}. {replace_forbidden_characters(track['name'])}.wav")
        sound_to_wav(sound_folder, sound["cueName"], wav_path)
    