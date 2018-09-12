from .img_widget import *

import os
widget_images = {}

widget_img_dir = os.path.join(os.path.dirname(__file__), 'img')
for img in os.listdir(widget_img_dir):
    if img.endswith('png'):
        widget_images.update({os.path.basename(img)[:-4]:os.path.join(widget_img_dir, img)})

del widget_img_dir, os