import glob
import sys

import cv2

prefix = sys.argv[1]
files = sorted(glob.glob(prefix + "_*.png"))
if not files:
    sys.exit(f"Tidak ada file {prefix}_*.png")
for path in files:
    img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    cv2.imwrite(path, cv2.flip(img, 1))
    print("dibalik:", path)