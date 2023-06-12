import pygame as pg

pg.init()

class Block:
    def __init__(self, file_name, image_size):
        self.file_name = file_name
        self.name = file_name.replace("_iso.png", "")
        self.surface = pg.image.load(file_name).convert_alpha()
        self.surface = pg.transform.scale(self.surface, image_size)
        self.image_size = image_size
