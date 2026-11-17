# AeroBridge Studio — Product 1

A laptop stand that lifts your screen to eye level and gives you the desk back.
Two solid walnut blades carry one pale ash deck. The blades rise behind the deck
into a pair of fins, and each fin is pierced clean through with a tall slot.

---

## What it is

Your laptop sits on a tilted board, so the screen comes up to your eyes instead
of making you stoop. Underneath, the stand is a pair of open arches: you can see
straight through it, and your keyboard and notebook live in the space it frees
up. Behind the deck the two blades sweep up into fins — structure that also
holds your notebook upright.

**Size:** 440 mm wide × 260 mm deep × 356 mm tall at the fin tips.
The deck is 380 × 204 mm and falls from 204 mm at the back to 144 mm at the
front, a 17° slope.

---

## Why it looks like this

| The idea | What it does for you |
|---|---|
| **The pierce** | A tall slot cut clean through each fin, 22 × 116 mm with 11 mm of wood round it. Light passes through, the fin reads as a drawing rather than a slab, and it is what you remember about the object. |
| **Fins that rise behind the deck** | The blades do not stop at the deck. They keep going, so the stand has a silhouette instead of a profile. The fins cradle the back of the laptop. |
| **Tilted deck** | Raises the screen to a comfortable angle. 204 mm at the back where the screen sits, 144 mm at the front so your wrists are not up in the air. |
| **Open arches** | You can see through it, so it does not wall off your desk. It also means you can push a keyboard or a notebook right underneath. |
| **Two solid blades, not four legs** | Four thin legs wobble. Two 30 mm boards do not. Each blade is one piece of wood, so there are no joints to work loose. |
| **Deck sits between the blades** | The wood of the deck is captured by the blades on both sides. It cannot slide, and you do not need a single screw to hold it. |
| **Drawn front corners** | The deck is not a rectangle: its front corners are rounded, so it reads as a shaped part rather than a shelf with cut ends. |
| **Front stop** | A brass bar set into the deck. Your laptop rests against it, so it cannot slide down the slope. |
| **Tie rod** | One alloy rod through both back legs. It stops the two blades from splaying apart when you lean on the stand, and it is why the whole thing feels solid. |
| **Felt pads** | Four small pads under the feet. They stop it scratching your desk, and they stop it creeping. |

### Two materials, and that is deliberate

- **Walnut** for the blades and the front stop: dark, so the frame reads as a
  shadow and the deck looks like it is floating.
- **Ash** for the deck: pale, so your eyes go to the laptop, not the furniture.
- **Brass** for the front stop, **alloy** for the tie rod: the two warm metal
  notes, and they tell you where the structure is.

---

## The parts

Eleven parts. Every one of them is a real file in `parts/stl/`, and every one
of those files is a closed, watertight solid.

| Tag | Part | Material | Size (mm) | Qty |
|---|---|---|---|---|
| A1 | Blade Left | Walnut, 30 mm | 260 × 356 × 30 | 1 |
| A2 | Blade Right | Walnut, 30 mm | 260 × 356 × 30 | 1 |
| D1 | Deck | Ash, 13 mm | 380 × 204 | 1 |
| S1 | Front Stop | Brass | 328 × 11 × 9 | 1 |
| R1 | Tie Rod | Alloy, Ø10 | 440 long | 1 |
| CL | Rod Collar L | Alloy, Ø10 | 26 long | 1 |
| CR | Rod Collar R | Alloy, Ø10 | 26 long | 1 |
| FLB / FLF | Felt Pad, left | Felt, 2 mm | 30 × 30 | 2 |
| FRB / FRF | Felt Pad, right | Felt, 2 mm | 30 × 30 | 2 |

A1 and A2 are the **same part**, turned around. You only cut one shape, twice.
That is on purpose: fewer drawings, fewer ways to get it wrong.

### The pierce

Both `A1_Blade_Left_cut.dxf` and `A2_Blade_Right_cut.dxf` contain **two** closed
polylines: the outline of the blade, and the slot. The slot is 22 mm wide,
116 mm tall, with an arched head, and it clears the blade's edge by at least
11 mm everywhere — enough that the fin will not split when the piece is routed
or when the laptop leans back on it. `A1_A2_Both_Blades_cut.dxf` puts both
blades in one file for nesting.

---

## Files

```
parts/
  stl/   one closed STL per part, in millimetres
  dxf/   the blade outline AND its pierce, as closed polylines
  renders/  hero.png, hero_side.png, exploded.png, one shot per part
  BOM.csv, CUTTING_LIST.csv
AeroBridge_Studio.py   the Fusion 360 script that rebuilds the whole assembly
```

The STLs are exported from the same geometry the renders come from, so what is
pictured is what comes off the machine. Every file is checked for manifoldness:
zero loose edges, zero non-manifold edges.

---

## Cutting notes

- Cut both blades from one 30 mm walnut board, 300 × 380 mm minimum. Nest them
  with the fins pointing in opposite directions and you will fit both.
- Cut the pierce **before** the outside profile, and cut it from both faces to
  avoid tear-out on the far side.
- The deck is 13 mm ash. Round the front corners at R34 to match the drawing.
- Sand the inside of the pierce. It is the first thing anyone puts a finger into.
- The blades are handed only by assembly — the cut file is identical.

---

## Building it

Run `AeroBridge_Studio.py` inside Fusion 360 (Scripts and Add-ins → Create).
It rebuilds the blades from the same silhouette the drawings use, extrudes the
pierce as a real hole, places the deck and the hardware, and names every body
so it matches the tags above.
