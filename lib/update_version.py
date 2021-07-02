import requests
from zipfile import ZipFile
import json
import io
import os
import UnityPy
from .paths import STRUCTS_PATH
from .asset import export_obj


def update_apk_monobehaviours(path: str, qooapp_id: int):
    with open(STRUCTS_PATH, "rt", encoding="utf8") as f:
        structs = json.load(f)

    MONOS = os.path.join(path, "apk_monobehaviours")
    os.makedirs(MONOS, exist_ok=True)

    apk = download_latest_apk(qooapp_id)
    # store apk
    with open(os.path.join(path, "current.apk"), "wb") as f:
        f.write(apk)

    # fetch unity data from apk
    apk_stream = io.BytesIO(apk)
    zipf = ZipFile(apk_stream)
    unity_f = zipf.open("assets/bin/Data/data.unity3d")
    env = UnityPy.load(unity_f)

    # extract monobehaviours from apk
    for obj in env.objects:
        if obj.type.name == "MonoBehaviour":
            try:
                export_obj(obj, MONOS, True)
            except Exception as e:
                print(f"Failed to extract obj {obj.path_id} - {e}")
    unity_f.close()
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

    return requests.get(data["split_apks"][0]["url"]).content
