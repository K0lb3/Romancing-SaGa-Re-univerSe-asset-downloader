from urllib import request
import requests
import UnityPy  # 1.7.7
import re
import os
import json
from lib import API, ASSETS, RES, extract_asset, update_apk_monobehaviours
import io


def toDict(tuples):
    return {key: val for key, val in tuples}


# init
os.makedirs(ASSETS, exist_ok=True)

VERSIONS = [
    [
        # game version, important for GameSettings.json
        "gl",
        # game host, hardcoded - il2cpp dumper -> stringliteral.json
        "production-api.rs-eu.aktsk.com",
        # apk name, check the url of the playstore
        "com.square_enix.android_googleplay.RSRSWW",
        # asset host, hardcoded - il2cpp dumper -> stringliteral.json
        "https://d22uketudusdsv.cloudfront.net",
        # qooapp id, check the url of qoapp
        12451,
    ],
    [
       "jp",
       "production-api.rs.aktsk.jp",
       "com.square_enix.android_googleplay.RSRS",
       "https://d1mur7djiqqbjs.cloudfront.net",
       6927
    ],
]


def main():
    for ver in VERSIONS:
        update_version(*ver)


def update_version(version: str, host: str, apk: str, asset_host: str, qooapp_id: int):
    path = os.path.join(ASSETS, version)
    os.makedirs(path, exist_ok=True)

    client_version_hash = "0.00.0-0"
    game_settings_path = os.path.join(
        path, "apk_monobehaviours", "GameSettings-GameSettings.json"
    )
    if os.path.exists(game_settings_path):
        with open(game_settings_path, "rt", encoding="utf8") as f:
            game_settings = json.load(f)
        client_version_hash = game_settings[f"{version}Setting"]["clientVersionHash"]

    res = query_api_version(host, client_version_hash)
    if res.status_code == 400:
        # fetch latest apk and extract the new client version hash
        update_apk_monobehaviours(path, qooapp_id)
        with open(game_settings_path, "rt", encoding="utf8") as f:
            game_settings = json.load(f)
        client_version_hash = game_settings[f"{version}Setting"]["clientVersionHash"]
        res = query_api_version(host, client_version_hash)

        if res.status_code == 400:
            print("Updated version hash seems to be invalid or outdated.")
            print("Try again in 2-3 hours.")
            return

    versions = res.json()

    update_assets(
       path,
       f"{asset_host}/AssetBundles/{'en/' if version == 'gl' else ''}Android/masterdata/{versions['master_version']}",
       "masterdata",
    )

    # normal assets
    update_assets(
        path,
        f"{asset_host}/AssetBundles/{'en/' if version == 'gl' else ''}Android/{versions['assets_version']}",
        "Android",
    )


def update_assets(path: str, api_namespace: str, assetlist_url: str):
    # api_namespace - space to nagivate within
    # assetlist_name - path to the assetlist within the namespace
    path_raw = os.path.join(path, "raw")
    path_ext = os.path.join(path, "extracted")

    asset_list = {}
    asset_list_fp = os.path.join(path, "assetlist.txt")
    if os.path.exists(asset_list_fp):
        with open(asset_list_fp, "rt", encoding="utf8") as f:
            asset_list = dict(line.strip().split("\t") for line in f if line.strip())

    asset_list_f = open(asset_list_fp, "at", encoding="utf8")

    asset_api = API(api_namespace)
    asset_list_o = asset_api.get(assetlist_url)
    try:
        TODO = []
        for obj in UnityPy.load(asset_list_o).objects:
            if obj.type == "AssetBundleManifest":
                d = obj.read_typetree()
                names = toDict(d["AssetBundleNames"])
                infos = toDict(d["AssetBundleInfos"])
                for aid, name in names.items():
                    ahash = bytes(infos[aid]["AssetBundleHash"].values()).hex()

                    if name not in asset_list or asset_list[name] != ahash:
                        TODO.append((name, ahash))
        if TODO:
            for i, (name, ahash) in enumerate(TODO):
                print(f"{i+1}/{len(TODO)} : {name}")
                data = download_asset(asset_api, name, path_raw)
                extract_asset(data, get_path(path_ext, name))
                asset_list_f.write(f"{name}\t{ahash}\n")

                if i % 10:
                    # save current progress
                    asset_list_f.close()
                    asset_list_f = open(asset_list_fp, "at", encoding="utf8")
            asset_list_f.close()
    except KeyboardInterrupt as e:
        pass
    asset_list_f.close()


def download_asset(asset_api, name, dir_path: str = ""):
    # dir : if set, save file into that dir
    data = asset_api.get(name)
    if dir_path:
        with open(get_path(dir_path, name), "wb") as f:
            f.write(data)
    return data


def get_path(path, name):
    fp = os.path.join(path, *name.split("/"))
    os.makedirs(os.path.dirname(fp), exist_ok=True)
    return fp


def query_api_version(host: str, version_hash: str):
    url = f"https://{host}/status"
    headers = {
        "User-Agent": "BestHTTP",
        "Connection": "TE",
        "Content-Type": "application/json",
        "X-Mikoto-Client-Version": version_hash,
        "X-Mikoto-Platform": "android",
        "TE": "identity"
    }
    return requests.post(url, headers=headers)


if __name__ == "__main__":
    main()
