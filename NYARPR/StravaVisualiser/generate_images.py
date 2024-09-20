"""
Script to test PIL and matplotlib.
"""
import io

import matplotlib.pyplot as plt
from PIL import Image

plt.rcParams["figure.figsize"] = [7.50, 3.50]
plt.rcParams["figure.autolayout"] = True

plt.figure()
plt.plot([1, 2])

img_buf = io.BytesIO()
plt.savefig(img_buf, format="png")

im = Image.open(img_buf)
im.show(title="My Image")

img_buf.close()
