# AeroBridge Studio — Product 1

A laptop stand that lifts your screen to eye level and gets the desk back.
Two solid walnut blades carry one pale ash deck. That is the whole thing.

---

## What it is

Your laptop sits on a tilted board, so the screen comes up to your eyes instead
of making you stoop. Underneath, the stand is a pair of open arches: you can see
straight through it, and your keyboard and notebook live in the space it frees
up. It is a bridge for your laptop, not a box on your desk.

**Size:** 464 mm wide (at the feet) × 240 mm deep × 204 mm tall at the back.
The deck is 344 × 268 mm and drops to 144 mm at the front, giving a 12° slope.

---

## Why it looks like this

| The idea | What it does for you |
|---|---|
| **Tilted deck** | Raises the screen to a comfortable angle. 204 mm at the back where the screen sits, 144 mm at the front so your wrists are not up in the air. |
| **Open arches** | You can see through it, so it does not wall off your desk. It also means you can push a keyboard or a notebook right underneath. |
| **Two solid blades, not four legs** | Four thin legs wobble. Two 28 mm boards do not. Each blade is one piece of wood, so there are no joints to work loose. |
| **Deck sits between the blades** | The wood of the deck is captured by the blades on both sides. It cannot slide, and you do not need a single screw to hold it. |
| **Front stop** | A small walnut lip on the front edge. Your laptop rests against it, so it cannot slide down the slope. |
| **Tie rod** | One alloy rod through both back legs. It stops the two blades from splaying apart when you lean on the stand, and it is why the whole thing feels solid. |
| **Felt pads** | Four small pads under the feet. They stop it scratching your desk, and they stop it creeping. |

### Two materials, and that is deliberate

- **Walnut** for the blades, the front stop: dark, so the frame reads as a
  shadow and the deck looks like it is floating.
- **Ash** for the deck: pale, so your eyes go to the laptop, not the furniture.
- **Alloy** for the tie rod: the one bright line, and it tells you where the
  structure is.

---

## The parts

Eleven parts. Every one of them is a real file in `parts/stl/`.

| Tag | Part | Material | Size (mm) | Qty |
|---|---|---|---|---|
| A1 | Blade Left | Walnut, 28 mm | 240 × 189 × 28 | 1 |
| A2 | Blade Right | Walnut, 28 mm | 240 × 189 × 28 | 1 |
| D1 | Deck Board | Ash, 12 mm | 344 × 268 | 1 |
| S1 | Front Stop | Walnut | 344 × 9 × 16 | 1 |
| R1 | Tie Rod | Alloy, Ø9 | 400 long | 1 |
| CL | Rod Collar L | Alloy, Ø16 | 24 long | 1 |
| CR | Rod Collar R | Alloy, Ø16 | 24 long | 1 |
| FLB / FLF | Felt Pad, left | Felt, 2 mm | 34 × 34 | 2 |
| FRB / FRF | Felt Pad, right | Felt, 2 mm | 34 × 34 | 2 |

A1 and A2 are the **same part**, turned around. You only cut one shape, twice.
That is on purpose: fewer drawings, fewer ways to get it wrong.

Full details, including the cutting list, are in:
- `parts/BOM.csv` — every part, with sizes
- `parts/CUTTING_LIST.csv` — what to buy and how to cut it
- `parts/dxf/` — the blade outline, to scale, ready for a CNC or a saw

---

## How to build it

### 1. Cut the two blades

Open `parts/dxf/A1_A2_Both_Blades_cut.dxf`. It is drawn **full size in
millimetres**. Stick it to a piece of 28 mm walnut, or send the file to a
shop with a CNC router, and cut two.

If you are cutting by hand, print it at 100% — check the 240 mm width with a
tape measure before you trust it — and trace round it.

### 2. Cut the deck

One piece of 12 mm ash, **344 × 268 mm**. The front edge needs a 12° bevel…
actually, no: leave it square. The deck is a flat board that sits on the slope
of the blades, and it is the *blades* that are angled, not the board. Square
edges are stronger and easier to sand.

### 3. Cut the front stop

A piece of walnut, 344 long, 16 mm thick, 9 mm tall, with the front top edge
rounded over. Glue and pin it to the front edge of the deck.

### 4. Drill the two holes for the tie rod

In each blade's back leg, **46 mm up from the bottom** and **46 mm in from the
back edge**, drill a Ø9 hole straight through the 28 mm thickness. Use a drill
press or a guide — this hole is what keeps the stand square, so it needs to be
at right angles.

### 5. Assemble

1. Stand the two blades up, 344 mm apart, **with the arches facing the same
   way**. Both front faces should look identical.
2. Slide the deck down between them. It sits on the flat 52 mm crown of each
   blade. Tap it down until it is seated. No glue needed yet.
3. Push the tie rod through both holes, then slide a collar on each end,
   tight against the inside face of each blade. Do up the grub screws.
4. Check it for square: measure the two diagonals across the feet. They should
   match within 2 mm. If they do, glue the deck to the blades and leave it
   overnight.
5. Stick the four felt pads under the feet.

### 6. Finish

Sand to 240 grit, then 400. Two coats of a hardwax oil on the walnut, one on
the ash deck (you want the deck smooth, not glossy). Let it cure for a week
before you put a laptop on it.

---

## The numbers, if you want to change something

Every dimension lives in one place: `studio_common.py`, in the `P` dictionary.
Change a number there, then re-run the scripts below and everything — the
renders, the STLs, the DXF, the BOM — updates together. Nothing is typed twice.

| Setting | Value | What it controls |
|---|---|---|
| `desk_x` / `desk_z` | 630 × 280 | the desk you are designing for |
| `arch_t` | 28 | how thick each blade is |
| `span_left` / `span_right` | 112 / 512 | where the blades stand |
| `deck_back` / `deck_front` | 204 / 144 | the slope of the deck |
| `deck_z0` / `deck_z1` | 10 / 278 | how deep the deck is |
| `blade_w` | 52 | how wide the wood is at the legs |
| `blade_w_crown` | 34 | how thick the crown is under the deck |
| `rod_y` / `rod_z` | 46 / 46 | where the tie rod goes |

---

## The scripts

You need Python 3 and `numpy` and `Pillow`. Everything else is standard library.

```bash
cd desk_system_v3

# draw the product pictures  -> parts/renders/
../.venv/bin/python studio_render.py

# write the part files      -> Product1_AeroBridgeStudio/parts/
../.venv/bin/python studio_export.py

# check the design before you build it
../.venv/bin/python verify_studio.py
```

`verify_studio.py` is the one that matters before you cut anything. It runs
the Fusion script against a stand-in for Fusion, then checks the geometry for
the things that actually go wrong: feet that are not flat, a deck that does not
sit down on the blades, a rod that misses the wood, a deck too short for the
laptop. If it passes, the design is buildable.

---

## In Fusion 360

`AeroBridge_Studio.py` builds the whole stand, with every part named.

1. Fusion 360 → **Utilities → Add-Ins → Scripts and Add-Ins**
2. **Scripts** tab → the green **+** → pick `AeroBridge_Studio.py`
3. Select it, press **Run**.

You get a component called `AeroBridge_Studio` with bodies named `A1 Blade`,
`A2 Blade`, `D1 Deck`, `S1 Front Stop`, `R1 Tie Rod`, `CL`/`CR` collars and the
four felt pads — the same tags as the drawings, so you can always tell which
part is which.

---

## Files in here

```
AeroBridge_Studio.py        the Fusion script - builds the model
parts/
  stl/                      every part as a 3D file, one per part
  dxf/                      the blade outline, full size, for cutting
  renders/                  the product pictures
  BOM.csv                   every part and its size
  CUTTING_LIST.csv          what to buy
```

Pictures are in `parts/renders/`: `hero.png` and `hero_side.png` show the whole
thing, `exploded.png` shows how it goes together, and there is one picture per
part (`blade_left.png`, `deck.png`, `rod.png`, `stop.png`).
