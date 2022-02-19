from PIL import Image
import os
import glob
from typing import Tuple, Dict, Union, Any
from itertools import cycle


def defragment_gif(path: str, output: str) -> None:
    """ Defragments a gif into frames.
    :param path:
    :param output: """

    imageObject = Image.open(path)  # .convert('RGBA')

    # Display individual frames from the loaded animated GIF file
    for frame in range(0, imageObject.n_frames):
        imageObject.seek(frame)
        imageObject.convert('RGBA')
        imageObject.save(f"{output}_{frame+1}.png", transparency=0)


def remove_background(path: str, output: str) -> None:
    """ Removes the background of image frames.
    :param path:
    :param output: """

    # Display individual frames from the loaded animated GIF file
    for i in range(len(glob.glob('./media/effects/fidget_spinner/*.png'))):
        im = Image.open(f'./media/effects/fidget_spinner/fidget_spinner_{i+1}.png').convert('RGBA')
        datas = im.getdata()

        newData = []
        # print(datas)
        # break
        # print(f'====={i+1}=====')
        for item in datas:
            if item[0] == 255 and item[1] == 255 and item[2] == 255:
                newData.append((255, 255, 255, 0))
            else:
                if item[0] > 150:
                    newData.append((0, 0, 0, 255))
                else:
                    newData.append(item)

        im.putdata(newData)
        im.save(f"{output}_{i+1}.png")


class GIF:
    """ A handler for GIF creations."""

    def __init__(self, image: Image.Image, frame_duration: int) -> None:
        """ Class initializing method.
        :param image: The base image of the GIF.
        :param frame_duration: The duration of each frame. """

        self._base_image = image
        self._frames = []
        self._frame_duration = frame_duration

    def add_frame(self, image: Image.Image) -> None:
        if not isinstance(image, Image.Image):
            raise TypeError("PIL.Image.Image expected")

        self._frames.append(image)

    def new_frame(self) -> Image:
        """ Retrieves a copy of the base image. """

        return self._base_image.copy()

    def export(self, path: str, **kwargs) -> None:
        """ Saves the gif.
        :param path: The path that the GIF is gonna be saved in. """
        image = self._base_image.copy()
        image.paste(self._frames[0], (0, 0), self._frames[0].convert('RGBA'))
        image.save(path, "GIF", save_all=True, append_images=self._frames,
                   duration=self._frame_duration, quality=90, loop=0, **kwargs)

