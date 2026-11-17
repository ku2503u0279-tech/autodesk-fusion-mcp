"""The 43-piece catalogue, written out of the Fusion parameters.

Sizes are strings so they read exactly the way they do in the CAD and in the
exported STL/STEP manifest: a flat panel is L x H x T, a rod is Ød x L, a disc
is Ød x T.  The `used` column names the product the part belongs to, so every
row is traceable to one Fusion component.
"""

# (part, size, material, how to make it, used in)
WOOD = [
    ("W1A  Left arch",        "184 x 131.4 x 12", "12 mm walnut / birch ply",
     "Band-saw or jigsaw, spindle-sand the C-curve, drill 2 x \u00d88.1 rod bores", "P1"),
    ("W1B  Right arch",       "184 x 131.4 x 12", "12 mm walnut / birch ply",
     "Mirror of W1A \u2014 flip the template, same tool path", "P1"),
    ("W1C  Slat deck",        "360 x 182 x 6", "6 mm walnut",
     "Router 6 stadium slots, ease the front lip with an R3 round-over", "P1"),
    ("W2A  Vault floor",      "184 x 52 x 6", "6 mm birch ply",
     "Table-saw rectangle, 4 vent slots, glue-and-clamp to the shield", "P2"),
    ("W2B  Vault shield",     "184 x 84 x 6", "6 mm walnut",
     "Nine 9 mm vent slots, 2 mm round-over on the outer face", "P2"),
    ("W2C  ULT saddle",       "99 x 38 x 20", "20 mm walnut block",
     "Bandsaw crescent, cove the seat with a 38 mm core-box bit", "P2"),
    ("W3A  Bottle coaster",   "\u00d884 x 6", "6 mm walnut",
     "\u00d884 hole saw, chamfer the rim, 2 coats oil", "P3"),
    ("W3B  Notebook tray",    "172 x 162 x 6", "6 mm birch ply",
     "Jigsaw crescent scoop, 10 mm corner radius, sand to 320", "P3"),
    ("W4A  Caddy floor",      "124 x 72 x 6", "6 mm walnut",
     "22 mm-radius stadium blank, 4 x M3 pilot holes", "P4"),
    ("W4B  Pen collar",       "124 x 72 x 6", "6 mm walnut",
     "Same stadium blank, 6 x \u00d823 wells, 2 mm round-over", "P4"),
    ("W4C  Drawer face",      "51.5 x 23.5 x 6", "6 mm walnut",
     "Bandsaw, 7 mm radius, finger pull cove, glue to P4C", "P4"),
    ("W5A  Cheek, left",      "34 x 30 x 6", "6 mm walnut",
     "6 mm radius corners, 2 mm round-over \u2014 one of a mirrored pair", "P5"),
    ("W5A  Cheek, right",     "34 x 30 x 6", "6 mm walnut",
     "Mirror of the left cheek", "P5"),
    ("W5B  Pedestal base",    "\u00d870 x 6", "6 mm walnut",
     "\u00d870 hole saw, \u00d836 relief for the 608 hub, chamfer the rim", "P5"),
]

METAL = [
    ("M1A  Rear tie-rod",     "\u00d88.0 x 360", "6061 aluminium / 304 stainless",
     "Hacksaw or pipe-cutter, de-burr, 400-grit lengthwise for a brushed finish", "P1"),
    ("M1B  Front tie-rod",    "\u00d88.0 x 360", "6061 aluminium / 304 stainless",
     "Same cut, same finish", "P1"),
    ("G5  Beam-splitter",     "25.4 x 25.4 x 25.4", "K9 optical glass, 50:50 coat",
     "Buy \u2014 1-inch 50:50 non-polarising cube, 400-700 nm", "P5"),
]

PRINT_A = [
    ("P0  Fit coupon",        "90 x 150 x 14", "PETG",
     "Print first. Confirms your tolerances before anything else", "P0"),
    ("P1D  Stopper L",        "44 x 27.5 x 27.2", "TPU 95A",
     "0.2 mm layers, 3 walls, 20% infill \u2014 one of a pair", "P1"),
    ("P1D  Stopper R",        "44 x 27.5 x 27.2", "TPU 95A",
     "Mirror of the left stopper", "P1"),
    ("P1E  DT-30 collar L",   "11 x 44 x 44", "PETG",
     "0.16 mm layers, 4 walls; dovetail root 30 mm at 60\u00b0", "P1"),
    ("P1E  DT-30 collar R",   "11 x 44 x 44", "PETG",
     "Receives the HoloBuddy wing at X = 459 \u00b1 0.15 mm", "P1"),
    ("P1F  MagPivot arm",     "68.8 x 38 x 60", "PETG",
     "Print flat on its side, no supports; 608 bore reamed to 8.05", "P1"),
    ("P1G  MagSafe disc",     "\u00d870 x 9", "PETG",
     "8 x 6 x 3 N52 pockets press-fit at 54 mm PCD", "P1"),
    ("P2A  Rear clamp arch",  "58 x 133.5 x 28", "PETG",
     "Print upright, 4 walls; 2 mm EVA pad recessed in each jaw", "P2"),
    ("P2B  Front clamp arch", "58 x 133.5 x 28", "PETG",
     "Identical part \u2014 the pair sets the 184 mm vault width", "P2"),
    ("P2C  Cable spine",      "22 x 70 x 26", "PETG",
     "Screw-free snap into the shield, 22 mm cable channel", "P2"),
    ("P2D  608 bearing hub",  "50 x 47.5 x 48", "PETG",
     "608 bore 22.15 mm interference; print with 5 perimeters", "P2"),
    ("P2E  Axle collar",      "24 x 13.4 x 24", "PETG",
     "Cyber-Red accent, M4 grub screw clamps the swing arm", "P2"),
    ("P3A  Bottle chalice",   "99 x 186.5 x 121.5", "PETG",
     "Largest node \u2014 186.5 mm tall, fits a 200 mm bed. Print upright with a brim", "P3"),
]

PRINT_B = [
    ("P3B  Left runner",      "24 x 58 x 48", "PETG",
     "Clamp body + DT-30 slide rail in one part", "P3"),
    ("P3B  Right runner",     "24 x 58 x 48", "PETG",
     "Runs the 110 mm tray travel", "P3"),
    ("P3C  Slide cleat L",    "14 x 6 x 146", "PETG",
     "Glue or screw to the walnut tray underside", "P3"),
    ("P3C  Slide cleat R",    "14 x 6 x 146", "PETG",
     "Mirror of the left cleat", "P3"),
    ("P4A  Right C-clamp",    "86 x 52 x 36", "PETG",
     "Tucked to Z = 16...52 mm so the deck edge stays clear", "P4"),
    ("P4B  Fluted core",      "64 x 72 x 116", "PETG",
     "6 x \u00d823 pen wells, micro-drawer bay, 7 flutes", "P4"),
    ("P4C  Drawer box",       "47.5 x 21.5 x 66", "PETG",
     "Print walls upright, 0.16 mm layers for the slide fit", "P4"),
    ("P4D  Airfoil spire",    "51.1 x 94.1 x 14", "PETG",
     "Print flat, 14 mm thick; 608 light-pipe at the tip", "P4"),
    ("P5A  Optical core",     "38 x 40 x 42", "matte-black PETG",
     "Kill the gloss: 0.12 mm layers, matte filament, no supports", "P5"),
    ("P5B  Electronics base", "44 x 30 x 42", "PETG",
     "ESP32-C3 cradle, INMP441 port, 608 swivel boss", "P5"),
    ("P5C  Magnetic visor",   "38 x 10 x 14.7", "PETG",
     "Cyber-Red brow, 2 x N52 magnets, snaps on or flicks off", "P5"),
    ("P5D  DT-30 wing arm",   "70.7 x 51 x 76", "PETG",
     "30 mm dovetail tongue slides into P1E at X = 459 mm", "P5"),
    ("P5E  Pedestal hub",     "36 x 9 x 36", "PETG",
     "608 press seat for the freestanding desktop mount", "P5"),
]

PRODUCTS = {
    "P0": ("Fit Check Gauge", "Print this first", "09"),
    "P1": ("AeroBridge G16 + MagPivot S24+", "Laptop stand, keyboard garage, phone arm", "10"),
    "P2": ("StealthVault 280 + SideDock ULT", "Hide the brick, hang the headphones", "11"),
    "P3": ("HydroSling", "Bottle outside the desk, notebook underneath", "12"),
    "P4": ("HexWing + Chimera Spire", "Pens, drawer and a mouse bungee that clears the sweep", "13"),
    "P5": ("HoloBuddy", "A hologram in a 25.4 mm cube", "14"),
}

ALL = WOOD + METAL + PRINT_A + PRINT_B

CONTENTS = [
    ("01", "How to read this book", "The three drawings on every product page, and the colour key", "03"),
    ("02", "The system at a glance", "One desk, six products, and where each one clamps", "04"),
    ("03", "Dimensions", "Top plan, front elevation and right side, dimensioned", "05"),
    ("04", "Why wood, metal and print", "What each material is doing, and the 70% filament saving", "08"),
    ("05", "Product 0 \u2014 Fit Check Gauge", "Print this first: it proves your printer and your hardware fit", "09"),
    ("06", "Product 1 \u2014 AeroBridge G16 + MagPivot S24+", "The laptop stand, the keyboard garage and the phone arm", "10"),
    ("07", "Product 2 \u2014 StealthVault 280 + SideDock ULT", "Hide the 280 W brick, hang the headphones", "11"),
    ("08", "Product 3 \u2014 HydroSling", "Bottle cage and notebook tray, both off the desk surface", "12"),
    ("09", "Product 4 \u2014 HexWing + Chimera Spire", "Pen caddy, micro-drawer and mouse bungee", "13"),
    ("10", "Product 5 \u2014 HoloBuddy", "The desk-top hologram, three ways to mount it", "14"),
    ("11", "Every piece, in one table", "All 43 parts with size, material and fabrication method", "15"),
    ("12", "Cut guides", "12 mm sheet, 6 mm sheet and one length of \u00d88 mm rod", "18"),
    ("13", "Building it", "Order of operations, from the first print to the last magnet", "19"),
    ("14", "Daily use", "What each product does for you on a normal working day", "20"),
    ("15", "Appendix", "Files, names, and the checks this book depends on", "21"),
]
