import requests
from zipfile import ZipFile
import json
import io
import os
import UnityPy
from .asset import export_obj
from .paths import STRUCTS_PATH


def update_gamesettings(path: str, qooapp_id: int):
    with open(STRUCTS_PATH, "rt", encoding="utf8") as f:
        STRUCTS = json.load(f)

    MONOS = os.path.join(path, "apk_monobehaviours")
    os.makedirs(MONOS, exist_ok=True)

    apk = download_latest_apk(qooapp_id)

    # fetch unity data from apk
    apk_stream = io.BytesIO(apk)
    env = UnityPy.Environment()
    zipf = ZipFile(apk_stream)
    for file in ["data.unity3d", "datapack.unity3d"]:
        file = f"assets/bin/Data/{file}"
        if file not in zipf.namelist():
            continue
        print("Found:", file)
        unity_f = zipf.open(file)
        env.files[file] = env.load_file(unity_f)
        unity_f.close()

    # extract monobehaviours from apk
    for obj in env.objects:
        if obj.type.name == "MonoBehaviour":
            mb = obj.read()
            if mb.name == "GameSettings":
                tree = obj.read_typetree(STRUCTS["Assembly-CSharp.dll"]["GameSettings"])
                with open(
                    os.path.join(MONOS, "GameSettings-GameSettings.json"),
                    "wt",
                    encoding="utf8",
                ) as f:
                    json.dump(tree, f, indent=4, ensure_ascii=False)
                break
    zipf.close()
    apk_stream.close()


def update_apk_monobehaviours(path: str, qooapp_id: int):
    MONOS = os.path.join(path, "apk_monobehaviours")
    os.makedirs(MONOS, exist_ok=True)

    apk = download_latest_apk(qooapp_id)
    # store apk
    with open(os.path.join(path, "current.apk"), "wb") as f:
        f.write(apk)

    # fetch unity data from apk
    apk_stream = io.BytesIO(apk)
    env = UnityPy.Environment()
    zipf = ZipFile(apk_stream)
    for file in ["data.unity3d", "datapack.unity3d"]:
        file = f"assets/bin/Data/{file}"
        if file not in zipf.namelist():
            print("Missing file: ", file, "(so far unrelevant for JP)")
            continue
        unity_f = zipf.open(file)
        env.files[file] = env.load_file(unity_f)
        unity_f.close()

    # extract monobehaviours from apk
    for obj in env.objects:
        if obj.type.name == "MonoBehaviour":
            try:
                export_obj(obj, MONOS, True)
            except Exception as e:
                pass
                # print(f"Failed to extract obj {obj.path_id} - {e}")

    zipf.close()
    apk_stream.close()


def download_latest_apk(qooapp_id: int):
    # download the latest apk from qooapp
    # in this case the first split apk, which should usually work fine for Unity games
    headers = {
        "x-user-token": "38d46579e39a7dc70edf05c1ed75beab26fea8a7",
        "accept": "application/json",
        "content-type": "application/json; charset=utf-8",
        "accept-encoding": "gzip",
        "user-agent": "okhttp/3.12.0",
    }
    url = f"https://api.qoo-app.com/v10/apps/{qooapp_id}"
    res = requests.get(url, headers=headers)

    if res.status_code != 200:
        return None

    data = res.json()
    if data["code"] != 200:
        return None
    data = data["data"]
    if data.get("split_apks", []):
        base = None
        datapack = None
        for item in data["split_apks"]:
            if item["signature"].startswith("base"):
                base = item
                print(json.dumps(item, indent=4))
            elif item["signature"].startswith("UnityDataAssetPack"):
                datapack = item
                print(json.dumps(item, indent=4))
                break
        if datapack:
            return requests.get(datapack["url"]).content
        else:
            return requests.get(base["url"]).content

    else:
        return download_apk_via_pid(data["package_id"])


def download_apk_via_pid(package_id: str) -> bytes:
    # try all kinda of combinations of android versions and processors
    query_args = {
        # "supported_abis": "x86;x86_64;armeabi-v7a;arm64-v8a",
        # "base_apk_version"	:	"0",
        "sdk_version": "30",
        # "base_apk_md5"	:	"null",
        # "version_code"	:	"80200",
        # "version_name"	:	"8.2.0",
        # "os"	:	"android 3.9",
        # "type"	:	"app",
        # "token"	:	"38d46579e39a7dc70edf05c1ed75beab26fea8a7",
        "android_id": "5892c8fbaa0c9611",
    }
    url = f"https://api.qoo-app.com/v6/apps/{package_id}/download"
    res = requests.get(
        url,
        allow_redirects=False,
        params=query_args,
        headers={"user-agent": "QooApp 8.2.0", "device-id": "5892c8fbaa0c9611"},
    )

    location = res.headers.get("Location", None)
    if not location:
        print("Location error: ", package_id)
        return None
    if "com.qooapp.qoohelper" in location:
        # TODO, retry with different specks, maybe split apk?
        print("RIP")
    else:
        return requests.get(location).content
