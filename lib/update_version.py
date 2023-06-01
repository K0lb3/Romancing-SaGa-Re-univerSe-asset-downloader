import requests
from zipfile import ZipFile
import json
import io
import os
import UnityPy
from .asset import export_obj
from .paths import STRUCTS_PATH


def update_gamesettings(path: str, appid: int):
    with open(STRUCTS_PATH, "rt", encoding="utf8") as f:
        STRUCTS = json.load(f)

    MONOS = os.path.join(path, "apk_monobehaviours")
    os.makedirs(MONOS, exist_ok=True)

    apk = download_apksupport(appid)

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


def update_apk_monobehaviours(path: str, appid: int):
    MONOS = os.path.join(path, "apk_monobehaviours")
    os.makedirs(MONOS, exist_ok=True)

    apk = download_apksupport(appid)
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


def download_apksupport(appid: str) -> bytes:
    import re

    html = requests.post(
        url=f"https://apk.support/download-app/{appid}",
        data=f"cmd=apk&pkg={appid}&arch=default&tbi=default&device_id=&model=default&language=en&dpi=480&av=default".encode(
            "utf8"
        ),
        headers={
            "sec-ch-ua": '"Chromium";v="106", "Google Chrome";v="106", "Not;A=Brand";v="99"',
            "sec-ch-ua-platform": "Windows",
            "sec-ch-ua-mobile": "?0",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36",
            "accept": "*/*",
            "origin": "https://apk.support",
            "sec-fetch-site": "same-origin",
            "sec-fetch-mode": "cors",
            "sec-fetch-dest": "empty",
            f"referer": "https://apk.support/download-app/{appid}",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
            "pragma": "no-cache",
            "cache-control": "no-cache",
            "content-length": "112",
            "content-type": "application/x-www-form-urlencoded",
        },
    ).text
    apks = re.findall(
        r"""<a rel="nofollow" href="(.+?.apk)">\s+?<span class.+?</span>(.+?.apk)</span>""",
        html,
    )
    for apk_url, apk_name in apks:
        if "config" not in apk_name:
            return requests.get(apk_url).content
    else:
        raise Exception("couldn't find base apk found")
