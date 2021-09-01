# Romancing SaGa Re;univerSe asset downloader

A small project that downloads all assets as well as the masterdata of Romancing SaGa Re;univerSe and extracts them while it's at it.

The script updates the assets and even its own parameters on its own,
so all you have to do is execute the download_assets.py script after every update to get the latest files.

## Script Requirements

- Python 3.6+

- UnityPy 1.7.8
- requests
- acb-py (for the album creation/extraction)

```cmd
pip install UnityPy==1.7.9
pip install requests
```

## Asset Download

Run ``download_assets.py`` to download the latest updates.
This script also directly extracts the downloaded assets.
The results are stored by default in ``/assets``

## Texture Coloring

Some textures, like those of the characters, use color palettes.
The script color_textures.py applies the given palette to each base image of the character.
