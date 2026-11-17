"""DraftShelf — product 6.  A modular dowel desk shelf, machined rather than printed.

**How the reference is actually built.** I had this wrong twice before reading
its parts list properly. The Workspace Hero's DeskShelf is not three legs with
a shelf sitting on top. It is:

    six 7/8 in dowels, 36 in long, laid side by side as a raft;
    three legs, left / middle / right, that cradle all six at once;
    a cover that caps the raft;
    a shelf that drops onto the cover.

So the dowels run ACROSS the desk, they are the deck, and the thing you see
from the front is six parallel rails with the shelf above them. That is the
whole look, and it is why the parts list says "9.5 in W Cover, 6 Dowel".

This is the machined version of the same system. The printed leg family
becomes **one billet comb**, which is the only genuinely engineered part in the
product and the only thing you have to make:

    J01 Comb     6061-T6 billet, 3 off. Six scallops R11.1 on 38 mm pitch,
                 cut into its top edge, so it cradles all six dowels in one
                 part. The teeth between the scallops are the datum: the
                 dowels are held on 38 +/- 0.05, and because all six are cut in
                 one setup they cannot drift relative to each other.
    R01 Dowel    22 mm ash, 900 long, 6 off, bought by the metre.
    S01 Shelf    20 mm ash board, 900 x 241, 1 off.
    C01 Cap      brass, turned, 12 off. They cover the dowel ends so no end
                 grain shows, and they are the only bright metal in the object.
    F01 Pad      95A TPU, 3 off, let into the comb's base.

    part          qty   material
    J01 Comb       3    6061-T6, clear anodised
    R01 Dowel      6    22 mm ash dowel
    S01 Shelf      1    20 mm ash board
    C01 Cap       12    CZ121 brass, brushed
    F01 Pad        3    95A TPU

All dimensions in millimetres. Y is up, X runs across the desk with -X on your
left, Z runs front to back with +Z pointing AWAY from you.
"""
import math

# ------------------------------------------------------------------ envelope
DESK = dict(x=1400.0, z=700.0)
ROD_D = 22.0                        # 7/8 in, the reference's dowel
ROD_R = ROD_D / 2.0
SHELF_T = 20.0                      # shelf thickness
SHELF_D = 241.0                     # 9.5 in front to back
SHELF_W = 900.0                     # 36 in, the reference's shelf width
N_RODS = 6
# 30, not 38. On a 38 pitch there is a 16 mm gap between an 22 mm dowel and
# its neighbour, and you look straight through it to the far comb: the front
# view showed the raft as a chewed fringe of ash and aluminium. At 30 the
# reveal is 8 mm -- still six separate dowels, still a shadow line between each
# -- but the raft is opaque. This is the one number in the product that is set
# by how it looks rather than by how it works.
PITCH = 30.0                        # dowel centres
FOOT_H = 4.0

# ----------------------------------------------------------------- J01 comb
COMB = dict(
    t=26.0,             # along X
    top=111.0,          # top of the teeth = top of the dowels = shelf underside
    # R11.6 against an R11.0 dowel: 0.6 mm of radial clearance, not 0.2.
    # At 0.2 the cradle arc and the dowel are two polygons with different
    # segment counts whose faces are nearly tangent, and the depth buffer
    # interleaves them: the render chews the dowel's top edge into a sawtooth.
    # 0.6 mm is also what you would actually machine so a sawn dowel drops in.
    scallop=ROD_D / 2.0 + 0.6,
    tooth=2.0,          # flat left at the very top of each tooth
    web=44.0,           # solid web below the scallops
    pad_dep=3.0,        # recess in the base for the TPU pad
)
COMB["w"] = N_RODS * PITCH                     # 228, the raft's depth
COMB["scallop_y"] = COMB["top"] - COMB["scallop"]
SHELF_Y = COMB["top"]
CAP = dict(r=ROD_R + 2.0, t=5.0, chamfer=1.0)

# The two end combs must NOT sit flush with the dowel ends. At -450/450 the
# comb's outer face was exactly coplanar with the sawn dowel ends, and the
# depth buffer chewed the top edge into a sawtooth. Inset 4 mm: the dowels now
# overhang the outer combs, which also hides the joint from the side.
LEG_XS = (-433.0, 0.0, 433.0)
ROD_X0, ROD_X1 = -450.0, 450.0

STOCK = dict(
    rod="22 mm ash dowel",
    shelf="20 mm ash board",
    alum="6061-T6, clear anodised",
    brass="CZ121 brass, brushed",
    tpu="95A TPU",
)


def rod_zs():
    """Centre of each dowel in Z, front to back."""
    z0 = -(N_RODS - 1) * PITCH / 2.0
    return [z0 + k * PITCH for k in range(N_RODS)]


def summary():
    return dict(
        overall_w=ROD_X1 - ROD_X0 + 2 * CAP["t"],
        overall_d=COMB["w"],
        height=SHELF_Y + SHELF_T,
        shelf_y=SHELF_Y,
        shelf_top=SHELF_Y + SHELF_T,
        raft_d=COMB["w"],
        pitch=PITCH,
        tooth_gap=PITCH - ROD_D,
        n_comb=3, n_dowel=6, n_shelf=1, n_cap=12, n_pad=3,
        rod_len=ROD_X1 - ROD_X0,
    )


if __name__ == "__main__":
    for k, v in summary().items():
        print("%-12s %s" % (k, v))
    print("rod z centres:", ["%.1f" % z for z in rod_zs()])
