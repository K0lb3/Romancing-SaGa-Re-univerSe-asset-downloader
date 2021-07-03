from PIL import Image
import re
import os
from lib import ASSETS

def main():
    for root, dirs, files in os.walk(ASSETS):
        if "base_clut.png" in files:
            print("Coloring", root)
            color_item_images(root)

def color_item_images(path: str):
    bc_img = Image.open(os.path.join(path, "base_clut.png"))
    palette = bc_img.getdata()

    for f in os.listdir(path):
        if not re.match(r"\d+\.png", f):
            continue
        img = Image.open(os.path.join(path, f))
        apply_color_palette(img, palette)
        img.save(os.path.join(path, f"c{f}"))

def apply_color_palette(img: Image, palette):
    pixdata = img.load()
    img.putdata([
        palette[x]
        for x in img.getchannel(3).getdata() #3 == alpha
    ])

if __name__ == "__main__":
    main()