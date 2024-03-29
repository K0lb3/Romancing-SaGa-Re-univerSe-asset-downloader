import os
import UnityPy
from collections import Counter
import zipfile
import json
from .paths import STRUCTS_PATH
from UnityPy.enums import ClassIDType
from UnityPy.classes.Object import NodeHelper

TYPES = [
    # Images
    "Sprite",
    "Texture2D",
    # Text (filish)
    "TextAsset",
    "Shader",
    "MonoBehaviour",
    "Mesh"
    # Font
    "Font",
    # Audio
    "AudioClip",
]

STRUCTS = {}


def extract_asset(inp, path):
    env = UnityPy.load(inp)
    # make sure that Texture2Ds are at the end
    objs = sorted(
        (obj for obj in env.objects if obj.type.name in TYPES),
        key=lambda x: 1 if x.type == ClassIDType.Texture2D else 0,
    )
    # check how the path should be handled
    if len(objs) == 1 or (
        len(objs) == 2
        and objs[0].type == ClassIDType.Sprite
        and objs[1].type == ClassIDType.Texture2D
    ):
        try:
            export_obj(objs[0], os.path.dirname(path), True)
        except Exception as e:
            print("Failed to export", objs[0].type.name, objs[0].path_id, e)
    else:
        used = []
        for obj in objs:
            if obj.path_id not in used:
                try:
                    used.extend(export_obj(obj, path, True))
                except Exception as e:
                    print("Failed to export", obj.type.name, obj.path_id, e)


def export_obj(obj, fp: str, append_name: bool = False) -> list:
    if obj.type.name not in TYPES:
        return []

    if not STRUCTS:
        with open(STRUCTS_PATH, "rt", encoding="utf8") as f:
            STRUCTS.update(json.load(f))

    data = obj.read()

    if isinstance(data, NodeHelper) and data.type != ClassIDType.MonoBehaviour:
        return []

    if append_name:
        name = getattr(data, "name", getattr(data, "m_Name", None))
        fp = os.path.join(
            fp, name if name is not None else f"{data.type.name}-{obj.path_id}"
        )
    name, extension = os.path.splitext(fp)
    os.makedirs(os.path.dirname(fp), exist_ok=True)

    # streamlineable types
    export = None
    if obj.type == ClassIDType.TextAsset:
        if not extension:
            extension = ".txt"
        export = data.script

    elif obj.type == ClassIDType.Font:
        if data.m_FontData:
            extension = ".ttf"
            if data.m_FontData[0:4] == b"OTTO":
                extension = ".otf"
            export = data.m_FontData
        else:
            return [obj.path_id]

    elif obj.type == ClassIDType.Mesh:
        extension = ".obf"
        export = data.export().encode("utf8")

    # elif obj.type == ClassIDType.Shader:
    #    extension = ".txt"
    #    export = data.export().encode("utf8")

    elif obj.type == ClassIDType.MonoBehaviour:
        # The data structure of MonoBehaviours is custom
        # and is stored as nodes
        # If this structure doesn't exist,
        # it might still help to at least save the binary data,
        # which can then be inspected in detail.
        if obj.serialized_type.nodes:
            extension = ".json"
            export = json.dumps(
                obj.read_typetree(), indent=4, ensure_ascii=False
            ).encode("utf8", errors="surrogateescape")
        else:
            script = data.m_Script
            if not script:
                return [obj.path_id]
            script = script.read()
            try:
                nodes = STRUCTS[script.m_AssemblyName][script.m_ClassName]
            except KeyError:
                return [obj.path_id]
            # adjust the name
            name = (
                f"{script.m_ClassName}-{data.name}" if data.name else script.m_ClassName
            )
            if append_name:
                new_fp = os.path.join(os.path.dirname(fp), name)
                if len(new_fp) + len(extension) < 256:
                    fp = new_fp
            extension = ".json"
            export = json.dumps(
                obj.read_typetree(nodes), indent=4, ensure_ascii=False
            ).encode("utf8", errors="surrogateescape")

    if export:
        fp = f"{fp}{extension}"
        if len(fp) < (256):
            with open(fp, "wb") as f:
                f.write(export)

    # non-streamlineable types
    if obj.type == ClassIDType.Sprite:
        data.image.save(f"{fp}.png")

        return [
            obj.path_id,
            data.m_RD.texture.path_id,
            getattr(data.m_RD.alphaTexture, "path_id", None),
        ]

    elif obj.type == ClassIDType.Texture2D:
        if not os.path.exists(fp) and data.m_Width:
            # textures can have size 0.....
            data.image.save(f"{fp}.png")

    elif obj.type == ClassIDType.AudioClip:
        samples = data.samples
        if len(samples) == 0:
            pass
        elif len(samples) == 1:
            with open(f"{fp}.wav", "wb") as f:
                f.write(list(data.samples.values())[0])
        else:
            os.makedirs(fp, exist_ok=True)
            for name, clip_data in samples.items():
                with open(os.path.join(fp, f"{name}.wav"), "wb") as f:
                    f.write(clip_data)
    return [obj.path_id]


class Fake:
    def __init__(self, **kwargs) -> None:
        self.__dict__.update(**kwargs)
