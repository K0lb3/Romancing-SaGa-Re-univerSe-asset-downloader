import requests
from zipfile import ZipFile
import json
import io
import os
import UnityPy
from .paths import STRUCTS_PATH

with open(STRUCTS_PATH, "rt", encoding="utf8") as f:
    STRUCTS = json.load(f)


def update_gamesettings(path: str, appid: int):
    apks = download_apksupport(appid)
    assert len(apks) > 0, "No apks found on apk.support"

    for apk_url, apk_name in apks:
        print("Downloading", apk_name)
        apk = requests.get(apk_url).content
        print("Trying to extract game settings")
        if try_extract_game_settings(apk, path):
            print("Success")
            return
        print("Failed")
        raise Exception("Failed to update game settings")


def try_extract_game_settings(apk: bytes, path: str):
    MONOS = os.path.join(path, "apk_monobehaviours")

    found = True
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
                    found = True
                break
    zipf.close()
    apk_stream.close()
    return found


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
    if len(apks) == 0:
        # might be single apk
        apk = re.search(r"""<li><a href="(.+?)">\s*<img src.*?>(.+?)\s*<""", html)
        if apk:
            return [apk.groups()]
    return apks
