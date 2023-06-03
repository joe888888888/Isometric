# Isometric level editor to manipulate the landscape and other solid objects

# KEY INPUTS:
# Select Blocks;
# Grass - 1
# Sand - 2
# Water - 3
# Stone - 4
# Erase - 5
# Open/Close Edit Mode - 0
# Export Ordered Grid Locations - Shift + E + S + C
# "Finished" June 3, 2023. #

import pygame as pg
import sys, math
import numpy as np

pg.init()

res = (1440, 900)
# screen = pg.display.set_mode((0, 0), pg.FULLSCREEN)
screen = pg.display.set_mode((600, 600))
pg.display.set_caption("Level Editor")
image_size = (48, 48)  # 3 times the original pixel bit size of 16

# outline_top = pg.image.load("top_iso.png").convert_alpha()
# outline_top = pg.transform.scale(outline_top, image_size)
# highlight_top = pg.image.load("highlight_top_iso.png").convert_alpha()
# highlight_top = pg.transform.scale(highlight_top, image_size)

# # # # #
grass = pg.image.load("grass_iso.png").convert_alpha()
grass = pg.transform.scale(grass, image_size)
water = pg.image.load("water_iso.png").convert_alpha()
water = pg.transform.scale(water, image_size)
sand = pg.image.load("sand_iso.png").convert_alpha()
sand = pg.transform.scale(sand, image_size)
stone = pg.image.load("stone_iso.png").convert_alpha()
stone = pg.transform.scale(stone, image_size)

# colors
white = (255, 255, 255)
off_white = (206, 219, 245)
grey = (150, 150, 150)
black = (0, 0, 0)

isometric_matrix = np.matrix([
    [1, 1],
    [-.5, .5]
])

edit_mode_flag = True
clicked = False
current_block = start_block = pg.Surface(image_size, pg.SRCALPHA)
debug = False

slices = []
current_slice = 0
num_slices = 5

# # # # # v # # # # #
def export_values():
        f = open("save_grid.txt", "w")
        for k in range(num_slices):
            for i in range(slices[current_slice].num_nodes):
                f.write(f"{i} ")
                # I don't like this, but I have to make a lot of textures for it to get out of hand anyway
                if slices[k].sorted_iso_grid[i]["occupancy"] is\
                        grass: slices[k].sorted_iso_grid[i]["occupancy"] = "grass"
                elif slices[k].sorted_iso_grid[i]["occupancy"] is\
                        sand: slices[k].sorted_iso_grid[i]["occupancy"] = "sand"
                elif slices[k].sorted_iso_grid[i]["occupancy"] is\
                        water: slices[k].sorted_iso_grid[i]["occupancy"] = "water"
                elif slices[k].sorted_iso_grid[i]["occupancy"] is\
                        stone: slices[k].sorted_iso_grid[i]["occupancy"] = "stone"
                if type(slices[k].sorted_iso_grid[i]["occupancy"]) == str:
                    f.write(f"{str(slices[k].sorted_iso_grid[i]['coords'])} - ")
                    f.write(f"{str(slices[k].sorted_iso_grid[i]['occupancy'])}")
                f.write("\n")
            f.write("\n")
        f.close()

# # # # # v # # # # #
def event_handler():
    global edit_mode_flag, clicked, current_block, current_slice, num_slices
    for event in pg.event.get():
        if event.type == pg.QUIT: _exit()

        if event.type == pg.KEYDOWN:
            if event.key == pg.K_ESCAPE: _exit()
            if event.key == pg.K_0:  # toggle edit mode
                if not edit_mode_flag: edit_mode_flag = True
                else: edit_mode_flag = False
            if event.key == pg.K_1: current_block = grass
            if event.key == pg.K_2: current_block = sand
            if event.key == pg.K_3: current_block = water
            if event.key == pg.K_4: current_block = stone
            if event.key == pg.K_5: current_block = pg.Surface(image_size, pg.SRCALPHA)

            if event.key == pg.K_DOWN:
                if current_slice > 0: current_slice -= 1
            elif event.key == pg.K_UP:
                if current_slice < num_slices - 1: current_slice += 1

        if event.type == pg.MOUSEBUTTONDOWN:
            slices[current_slice].place_blocks()
            clicked = True

        elif event.type == pg.MOUSEMOTION:
            if clicked: slices[current_slice].place_blocks()

        if event.type == pg.MOUSEBUTTONUP:
            clicked = False

def _exit():
    pg.quit()
    sys.exit()

def keyboard_inputs():
    global current_block, img_size, debug
    keys = pg.key.get_pressed()
    if keys[pg.K_e] and keys[pg.K_s] and keys[pg.K_c] and pg.key.get_mods() & pg.KMOD_SHIFT:
        export_values()
        _exit()

    if keys[pg.K_d] and keys[pg.K_g] and pg.key.get_mods() & pg.KMOD_SHIFT:
        debug = True

def draw_screen():
    global screen
    if edit_mode_flag:
        screen.fill(off_white)
    else: screen.fill(white)

    for k in range(num_slices):
        y_shift = slices[k].scale_factor / -2
        for i in range(slices[k].num_nodes):
            screen.blit(slices[k].sorted_iso_grid[i]["occupancy"],
                        (slices[k].sorted_iso_grid[i]["coords"][0],
                         slices[k].sorted_iso_grid[i]["coords"][1] + y_shift - k * slices[k].scale_factor))
    slices[current_slice].draw_locations()

    draw_selection()

    pg.display.update()

def draw_selection():
    global current_block, edit_mode_flag
    # display selected block
    if edit_mode_flag and type(current_block) == pg.Surface:
        image = pg.transform.scale(current_block, (32, 32))
        screen.blit(image,(50, 50))


class Grid:
    def __init__(self):
        self.img_size = image_size
        self.grid_size = 8  # number of cells in one x/z-axis of grid
        self.num_nodes = self.grid_size ** 2
        self.cartesian_grid = []  # list of points from (0,0) to (grid_size_x - 1, grid_size_z - 1)
        self.iso_grid = []  # list of dictionaires
        self.sorted_iso_grid = []  # sorted grid for blitting blocks in the correct order
        self.scale_factor = self.img_size[0] / 2   # 16 pixel bit across all things isometric
        self.create_locations()
        self.transform_locations()

    def create_locations(self):
        for i in range(self.grid_size):
            for j in range(self.grid_size):
                # append 2d cartesian coordiantes
                self.cartesian_grid.append((i, j))

    def transform_locations(self):
        shift_x = pg.display.get_window_size()[0] / 2 - (self.grid_size * self.scale_factor)
        shift_y = pg.display.get_window_size()[1] / 1.6
        for i in range(self.num_nodes):
            cartesian_matrix = (np.matrix(self.cartesian_grid[i])).reshape((2, 1)) # calculate dot products
            converted_matrix = np.dot(isometric_matrix, cartesian_matrix)
            self.iso_grid.append({"coords": (float(converted_matrix[0]), float(converted_matrix[1]))}) #extract data
            # scale and translate
            self.iso_grid[i].update({"coords": (self.iso_grid[i]["coords"][0] * self.scale_factor,
                                                    self.iso_grid[i]["coords"][1] * self.scale_factor)})
            self.iso_grid[i].update({"coords": (self.iso_grid[i]["coords"][0] + shift_x,
                                                    self.iso_grid[i]["coords"][1] + shift_y)})
            self.iso_grid[i].update({"selection": False})
            self.iso_grid[i].update({"occupancy": start_block})
        self.order_locations()

    def order_locations(self):
            n = self.num_nodes
            shift_y = self.scale_factor / 2  # half of the pixel size of the top face
            self.sorted_iso_grid = self.iso_grid
            swapped = False
            for i in range(n - 1):
                for j in range(0, n - i - 1):
                    if self.sorted_iso_grid[j]["coords"][1] > self.sorted_iso_grid[j + 1]["coords"][1]:
                        swapped = True
                        self.sorted_iso_grid[j], self.sorted_iso_grid[j + 1] = \
                            self.sorted_iso_grid[j + 1], self.sorted_iso_grid[j]
                if not swapped:
                    return


    def prep_nodes(self):
        global edit_mode_flag, current_slice
        shift_y = self.scale_factor / 2  # half of the pixel size of the top face
        # equidistance!
        if edit_mode_flag:
            mouse_pos = pg.mouse.get_pos()
            for i in range(self.num_nodes):
                d = math.dist(mouse_pos, (self.iso_grid[i]["coords"][0] + self.scale_factor,
                                          self.iso_grid[i]["coords"][1] - current_slice * self.scale_factor))
                if d <= self.scale_factor / 2:
                    self.iso_grid[i]["selection"] = i
                else: self.iso_grid[i]["selection"] = -1

    def draw_locations(self):
        global edit_mode_flag, current_slice
        y_shift = self.scale_factor / -2
        # draw blocks
        if edit_mode_flag:
            for i in range(self.num_nodes):
                pg.draw.circle(screen, black, (self.iso_grid[i]["coords"][0] + self.scale_factor,
                    self.iso_grid[i]["coords"][1] - current_slice * self.scale_factor), 3)

    def place_blocks(self):
        global current_block
        for i in range(self.num_nodes):
            if self.iso_grid[i]["selection"] >= 0:
                if type(current_block) != str:
                    self.iso_grid[i].update({"occupancy": current_block})

class Camera_Group(pg.sprite.Group):
    def __init__(self):
        super().__init__()


for slc in range(num_slices):
    slices.append(Grid())


clock = pg.time.Clock()
start_time = pg.time.get_ticks()

while True:
    clock.tick(50)
    event_handler()
    keyboard_inputs()

    slices[current_slice].prep_nodes()

    if debug:
        pass

    draw_screen()

    # print(clock.get_fps())
