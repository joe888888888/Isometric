# Isometric level editor to manipulate the landscape and other solid objects

# KEY INPUTS:
# Select Blocks;
# Grass - 1
# Sand - 2
# Water - 3
# Stone - 4
# CobbleStone - 5
# Erase - Backspace
# Open/Close Edit Mode - 0
# Export Ordered Grid Locations - Shift + E
# Open Save File - Shift + S
# June 3, 2023 - 3D Finished
# June 11, 2023 - Finished Menus and Refactored Code

import pygame as pg
import sys, math
import numpy as np
from block import Block
# import time

pg.init()

screen = pg.display.set_mode((0, 0), pg.FULLSCREEN)
res = pg.display.get_window_size()

# res = (600, 600)
# screen = pg.display.set_mode((600, 600))

pg.display.set_caption("Level Editor")

# # # # #
image_size = (48, 48)
all_block_dict = {
    "air": Block("air_iso.png", image_size),
    "grass": Block("grass_iso.png", image_size),
    "sand": Block("sand_iso.png", image_size),
    "stone": Block("stone_iso.png", image_size),
    "cobblestone": Block("cobblestone_iso.png", image_size),
    "water": Block("water_iso.png", image_size)
}

# colors
white = (255, 255, 255)
off_white = (206, 219, 245)
grey = (40, 40, 50)
black = (0, 0, 0)

isometric_matrix = np.matrix([
    [1, 1],
    [-.5, .5]
])

edit_mode_flag = True
menu_flag = False
clicked = False
debug = False
export_flag = False

current_block = start_block = empty_block = all_block_dict["air"]
ground_block = all_block_dict["water"]
current_slice = start_slice = 0
num_slices = 7  # or "rows" or "bases"

menu_image_size = 72
hotbar_size = 5

slices = []


def export_values():
    global edit_mode_flag, export_flag
    edit_mode_flag = False
    f = open("level_edit_save_file.txt", "w")
    for k in range(num_slices):
        for i in range(slices[current_slice].num_nodes):
            f.write(f"{i} - ")
            f.write(f"{str(slices[k].sorted_iso_grid[i]['coords'])}"
                    f" - {slices[k].sorted_iso_grid[i]['occupancy'].name} \n")
        f.write("\n")
    export_flag = True
    f.close()

def event_handler():
    global edit_mode_flag, menu_flag, clicked, current_slice, num_slices
    for event in pg.event.get():
        if event.type == pg.QUIT: _exit()

        if event.type == pg.KEYDOWN:
            if event.key == pg.K_ESCAPE: _exit()
            if event.key == pg.K_0:  # toggle edit mode
                if not edit_mode_flag: edit_mode_flag = True
                else: edit_mode_flag = False

            if event.key == pg.K_m:
                if not menu_flag: menu_flag = True
                else: menu_flag = False

            if event.key == pg.K_DOWN:
                if current_slice > 0: current_slice -= 1
            elif event.key == pg.K_UP:
                if current_slice < num_slices - 1: current_slice += 1

        if event.type == pg.MOUSEBUTTONDOWN:
            if menu_flag: menu.select_menu_option()
            else:
                slices[current_slice].place_blocks()
                clicked = True
            if edit_mode_flag:
                if pg.Rect.collidepoint(hotbar.hotbar_rect, pg.mouse.get_pos()): hotbar.add_selected_blocks()


        elif event.type == pg.MOUSEMOTION:
            if clicked: slices[current_slice].place_blocks()

        if event.type == pg.MOUSEBUTTONUP: clicked = False

def keyboard_inputs():
    global current_block, img_size, debug
    keys = pg.key.get_pressed()
    if keys[pg.K_e] and pg.key.get_mods() & pg.KMOD_SHIFT:
        export_values()

    elif keys[pg.K_d] and keys[pg.K_g] and pg.key.get_mods() & pg.KMOD_SHIFT:
        debug = True

    elif keys[pg.K_s] and pg.key.get_mods() & pg.KMOD_SHIFT:
        open_save_file()

    elif keys[pg.K_BACKSPACE]: current_block = all_block_dict["air"]  # or "air" or "empty"

    elif keys[pg.K_1]:
        hotbar.select_from_hotbar(0)
    elif keys[pg.K_2]:
        hotbar.select_from_hotbar(1)
    elif keys[pg.K_3]:
        hotbar.select_from_hotbar(2)
    elif keys[pg.K_4]:
        hotbar.select_from_hotbar(3)
    elif keys[pg.K_5]:
        hotbar.select_from_hotbar(4)

def draw_screen():
    global screen, edit_mode_flag, menu_flag
    if edit_mode_flag:
        screen.fill(off_white)
    else: screen.fill(white)

    for k in range(num_slices):
        y_shift = slices[k].scale_factor / -2
        for i in range(slices[k].num_nodes):
            screen.blit(slices[k].sorted_iso_grid[i]["occupancy"].surface,
                        (slices[k].sorted_iso_grid[i]["coords"][0],
                         slices[k].sorted_iso_grid[i]["coords"][1] + y_shift - k * slices[k].scale_factor))
    slices[current_slice].draw_locations()

    if menu_flag: menu.draw_menu_screen()
    else: draw_selection()

    if edit_mode_flag: hotbar.draw_hotbar_screen()

    pg.display.update()

def draw_selection():
    global current_block, edit_mode_flag
    global menu_image_size
    # display selected block
    if edit_mode_flag and not menu_flag:
        image = pg.transform.scale(current_block.surface, (menu_image_size, menu_image_size))
        screen.blit(image, (50, 50))

def _exit():
    pg.quit()
    sys.exit()

def open_save_file():
    f = open("level_edit_save_file.txt","r")
    # lines = f.readlines()
    # temp = []
    # for k in range(num_slices):
    #     for i in range(len(lines)):
    f.close()


class Grid:
    def __init__(self, slice_number):
        self.grid_size = 15  # number of cells in one x/z-axis of grid
        self.num_nodes = self.grid_size ** 2
        self.slice_number = slice_number
        self.cartesian_grid = []  # list of points from (0,0) to (grid_size_x - 1, grid_size_z - 1)
        self.iso_grid = []  # list of dictionaires
        self.sorted_iso_grid = []  # sorted grid for blitting blocks in the correct order
        self.scale_factor = image_size[0] / 2   # 16 pixel bit across all things isometric
        self.create_locations()
        self.transform_locations(slice_number)

    def create_locations(self):
        for i in range(self.grid_size):
            for j in range(self.grid_size):
                # append 2d cartesian coordiantes
                self.cartesian_grid.append((i, j))

    def transform_locations(self, num_slice):
        global num_slices
        shift_x = pg.display.get_window_size()[0] / 2 - (self.grid_size * self.scale_factor)
        shift_y = pg.display.get_window_size()[1] / 1.75
        for i in range(self.num_nodes):
            cartesian_matrix = (np.matrix(self.cartesian_grid[i])).reshape((2, 1)) # calculate dot products
            converted_matrix = np.dot(isometric_matrix, cartesian_matrix)
            self.iso_grid.append({"coords": (float(converted_matrix[0]), float(converted_matrix[1]))}) #extract data
            # scale and translate
            self.iso_grid[i].update({"coords": (self.iso_grid[i]["coords"][0] * self.scale_factor,
                                                    self.iso_grid[i]["coords"][1] * self.scale_factor)})
            self.iso_grid[i].update({"coords": (round(self.iso_grid[i]["coords"][0] + shift_x),
                                                    round(self.iso_grid[i]["coords"][1] + shift_y))})
            self.iso_grid[i].update({"selection": False})
            if num_slice == start_slice: self.iso_grid[i].update({"occupancy": ground_block})
            else:  self.iso_grid[i].update({"occupancy": start_block})
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
                dist = math.dist(mouse_pos, (self.iso_grid[i]["coords"][0] + self.scale_factor,
                                          self.iso_grid[i]["coords"][1] - current_slice * self.scale_factor))
                if dist <= self.scale_factor / 2:
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

class SelectionMenu:
    def __init__(self):
        global res, menu_image_size
        self.width = res[0] / 1.5
        self.height =  res[1] / 1.5
        self.images_per_row = self.width / (menu_image_size + 7)  # small 7 px buffer
        self.menu_rect = pg.rect.Rect(0, 0, self.width, self.height)
        self.menu_rect.center = res[0] // 2, res[1] // 2
        self.cell_coords = []
        self.create_menu()

    def create_menu(self):
        count = 0
        for i in range(len(all_block_dict)):
            if count >= self.images_per_row:
                count = 0
            x = self.menu_rect.x + 64 + menu_image_size * count
            y = self.menu_rect.y + 64 + menu_image_size * ((i + 1) // self.images_per_row)
            count += 1
            self.cell_coords.append((x, y))

    def draw_menu_screen(self):
        pg.draw.rect(screen, off_white, self.menu_rect)
        count = 0
        for key in all_block_dict:
            if key == "air":
                pass
                # do not display any blocks in all block dict that I don't want in the menum
            else:
                screen.blit(all_block_dict[key].surface, self.cell_coords[count])
                count += 1

    def select_menu_option(self):
        global current_block, menu_flag
        mouse_pos = pg.mouse.get_pos()
        for i, key in enumerate(all_block_dict):
            dist = math.dist(mouse_pos, self.cell_coords[i])
            if dist <= menu_image_size:
                current_block = all_block_dict[key]
                menu_flag = False

class Hotbar:
    def __init__(self):
        global menu_image_size, hotbar_size
        self.num_squares = hotbar_size
        self.height = (menu_image_size + 7)  # small 7 px buffer again
        self.width = self.height * self.num_squares   # a line of sqaures make up hotbar
        self.hotbar_rect = pg.rect.Rect(0, 0, self.width, self.height)
        self.hotbar_rect.center = res[0] // 2, res[1] // 2
        self.hotbar_rect.bottom = res[1] - 7
        self.occupancy_list = []

    def add_selected_blocks(self):
        global current_block
        if len(self.occupancy_list) >= self.num_squares:
            self.occupancy_list.append(current_block)
            self.occupancy_list.pop(0)
        else: self.occupancy_list.append(current_block)

    def draw_hotbar_screen(self):
        pg.draw.rect(screen, black, self.hotbar_rect, 3)
        count = 0
        for i, b in enumerate(self.occupancy_list):
            if b == "air":
                pass
                # do not display any blocks in all block dict that I don't want in the menum
            else:
                screen.blit(b.surface, (self.hotbar_rect.x + self.height // 5 + self.height * i,
                                        self.hotbar_rect.center[1] - self.height // 3.5))
                count += 1

    def select_from_hotbar(self, num_key):
        global current_block
        current_block = self.occupancy_list[num_key]

class Camera_Group(pg.sprite.Group):
    def __init__(self):
        super().__init__()


# allot locations
for slc in range(num_slices):
    slices.append(Grid(slc))

menu = SelectionMenu()
hotbar = Hotbar()

clock = pg.time.Clock()
start_time = pg.time.get_ticks()

while True:
    clock.tick(50)  # 50 fps cap
    pg.mouse.set_cursor(*pg.cursors.diamond)
    event_handler()
    keyboard_inputs()

    slices[current_slice].prep_nodes()

    draw_screen()

    # print(clock.get_fps())

    if debug:
        pass

    if export_flag:
        pg.image.save(screen, 'img.png') # rip peggy
        _exit()
