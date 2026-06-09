#!/usr/bin/env python3
"""Generate a high-resolution PNG ERD for the MediGuard database schema."""

import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mp

# ─── Dimensions (figure units = inches) ─────────────────────────────────────
BOX_W  = 3.0
HDR_H  = 0.36
ROW_H  = 0.22
FIG_W  = 14.5
FIG_H  = 11.5
GAP_Y  = 0.55
MARGIN = 0.50

# ─── Colors ──────────────────────────────────────────────────────────────────
C = dict(
    hdr_bg    = "#0891b2",
    hdr_txt   = "#ffffff",
    box_bg    = "#f8fafc",
    alt_row   = "#e0f2fe",
    border    = "#0e7490",
    pk_bg     = "#dbeafe",  pk_txt = "#1d4ed8",
    fk_bg     = "#ede9fe",  fk_txt = "#6d28d9",
    uq_bg     = "#dcfce7",  uq_txt = "#15803d",
    name      = "#0f172a",
    dtype     = "#64748b",
    shadow    = "#cbd5e1",
    arrow     = "#0891b2",
    arrow_opt = "#7c3aed",
    fig_bg    = "#f0f9ff",
    sep       = "#bae6fd",
)

# ─── Schema ──────────────────────────────────────────────────────────────────
# Each attr tuple: (column_name, SQL_type, badge)   badge ∈ {"PK","FK","UQ",""}
ENTITIES = {
    "users": dict(display="users", attrs=[
        ("id",            "INTEGER",  "PK"),
        ("email",         "VARCHAR",  "UQ"),
        ("full_name",     "VARCHAR",  ""),
        ("hashed_pw",     "VARCHAR",  ""),
        ("is_active",     "BOOLEAN",  ""),
        ("is_admin",      "BOOLEAN",  ""),
        ("notify_emails", "BOOLEAN",  ""),
        ("created_at",    "DATETIME", ""),
    ]),
    "password_reset_tokens": dict(display="password_reset_tokens", attrs=[
        ("id",         "INTEGER",  "PK"),
        ("user_id",    "INTEGER",  "FK"),
        ("token",      "VARCHAR",  "UQ"),
        ("otp_code",   "VARCHAR",  ""),
        ("expires_at", "DATETIME", ""),
        ("used_at",    "DATETIME", ""),
        ("created_at", "DATETIME", ""),
    ]),
    "diseases": dict(display="diseases", attrs=[
        ("id",                   "INTEGER",  "PK"),
        ("slug",                 "VARCHAR",  "UQ"),
        ("name",                 "VARCHAR",  "UQ"),
        ("category",             "VARCHAR",  ""),
        ("featured",             "BOOLEAN",  ""),
        ("severity",             "VARCHAR",  ""),
        ("symptoms",             "JSON",     ""),
        ("description",          "TEXT",     ""),
        ("causes",               "TEXT",     ""),
        ("treatment",            "TEXT",     ""),
        ("prevention",           "JSON",     ""),
        ("sections",             "JSON",     ""),
        ("symptom_descriptions", "JSON",     ""),
        ("updated_at",           "DATETIME", ""),
    ]),
    "prediction_logs": dict(display="prediction_logs", attrs=[
        ("id",          "INTEGER",  "PK"),
        ("user_id",     "INTEGER",  "FK"),
        ("symptoms",    "JSON",     ""),
        ("predictions", "JSON",     ""),
        ("top_disease", "VARCHAR",  ""),
        ("timestamp",   "DATETIME", ""),
        ("region",      "VARCHAR",  ""),
        ("age_group",   "VARCHAR",  ""),
    ]),
    "chat_logs": dict(display="chat_logs", attrs=[
        ("id",                  "INTEGER",  "PK"),
        ("user_id",             "INTEGER",  "FK"),
        ("title",               "VARCHAR",  ""),
        ("message",             "TEXT",     ""),
        ("response",            "TEXT",     ""),
        ("sources",             "JSON",     ""),
        ("follow_up_questions", "JSON",     ""),
        ("mode",                "VARCHAR",  ""),
        ("pregnancy_context",   "BOOLEAN",  ""),
        ("created_at",          "DATETIME", ""),
    ]),
    "contact_messages": dict(display="contact_messages", attrs=[
        ("id",      "INTEGER",  "PK"),
        ("name",    "VARCHAR",  ""),
        ("email",   "VARCHAR",  ""),
        ("subject", "VARCHAR",  ""),
        ("message", "TEXT",     ""),
        ("sent_at", "DATETIME", ""),
        ("read_at", "DATETIME", ""),
    ]),
    "chat_feedback": dict(display="chat_feedback", attrs=[
        ("id",               "INTEGER",  "PK"),
        ("session_id",       "VARCHAR",  ""),
        ("user_id",          "INTEGER",  "FK"),
        ("query",            "TEXT",     ""),
        ("response_preview", "TEXT",     ""),
        ("rating",           "BOOLEAN",  ""),
        ("query_keywords",   "JSON",     ""),
        ("mode",             "VARCHAR",  ""),
        ("created_at",       "DATETIME", ""),
    ]),
    "prediction_feedback": dict(display="prediction_feedback", attrs=[
        ("id",                "INTEGER",  "PK"),
        ("prediction_log_id", "INTEGER",  "FK"),
        ("user_id",           "INTEGER",  "FK"),
        ("top_predicted",     "VARCHAR",  ""),
        ("was_helpful",       "BOOLEAN",  ""),
        ("confirmed_disease", "VARCHAR",  ""),
        ("comment",           "TEXT",     ""),
        ("created_at",        "DATETIME", ""),
    ]),
    "newsletter_subscribers": dict(display="newsletter_subscribers", attrs=[
        ("id",                "INTEGER",  "PK"),
        ("email",             "VARCHAR",  "UQ"),
        ("name",              "VARCHAR",  ""),
        ("unsubscribe_token", "VARCHAR",  "UQ"),
        ("is_active",         "BOOLEAN",  ""),
        ("subscribed_at",     "DATETIME", ""),
    ]),
}

# (col, row) — users sits at the center (col 1, row 1)
LAYOUT = {
    "password_reset_tokens": (0, 0),
    "diseases":               (2, 0),
    "newsletter_subscribers": (3, 0),
    "chat_logs":              (0, 1),
    "users":                  (1, 1),
    "prediction_logs":        (2, 1),
    "contact_messages":       (3, 1),
    "chat_feedback":          (0, 2),
    "prediction_feedback":    (1, 2),
}

# (from_table, from_col, to_table, to_col, optional, curve_rad)
RELS = [
    ("password_reset_tokens", "user_id",          "users",           "id", False,  0.18),
    ("chat_logs",             "user_id",           "users",           "id", False,  0.0),
    ("chat_feedback",         "user_id",           "users",           "id", True,  -0.18),
    ("prediction_logs",       "user_id",           "users",           "id", True,   0.0),
    ("prediction_feedback",   "user_id",           "users",           "id", True,   0.0),
    ("prediction_feedback",   "prediction_log_id", "prediction_logs", "id", True,   0.15),
]

# ─── Layout math ─────────────────────────────────────────────────────────────
def box_h(key):
    return HDR_H + len(ENTITIES[key]["attrs"]) * ROW_H

col_left = {c: MARGIN + c * (BOX_W + 0.45) for c in range(4)}

row_keys  = {r: [k for k, (c, row) in LAYOUT.items() if row == r] for r in range(3)}
row_max_h = {r: max(box_h(k) for k in ks) for r, ks in row_keys.items()}

row_top = {}
y = FIG_H - MARGIN
for r in range(3):
    row_top[r] = y
    y -= row_max_h[r] + GAP_Y

def box_pos(key):
    col, row = LAYOUT[key]
    return col_left[col], row_top[row]

def attr_y(key, attr_name):
    _, yt = box_pos(key)
    i = [a[0] for a in ENTITIES[key]["attrs"]].index(attr_name)
    return yt - HDR_H - i * ROW_H - ROW_H / 2

# ─── Draw helpers ────────────────────────────────────────────────────────────
def draw_entity(ax, key):
    x, yt = box_pos(key)
    e = ENTITIES[key]
    h = box_h(key)
    yb = yt - h
    body_h = h - HDR_H

    # shadow
    ax.add_patch(mp.FancyBboxPatch(
        (x + 0.05, yb - 0.05), BOX_W, h,
        boxstyle="round,pad=0.02", lw=0, fc=C["shadow"], zorder=1))

    # full box in header colour (provides header background + rounded corners)
    ax.add_patch(mp.FancyBboxPatch(
        (x, yb), BOX_W, h,
        boxstyle="round,pad=0.02", lw=0, fc=C["hdr_bg"], zorder=2))

    # body background (rounded bottom corners)
    ax.add_patch(mp.FancyBboxPatch(
        (x, yb), BOX_W, body_h,
        boxstyle="round,pad=0.02", lw=0, fc=C["box_bg"], zorder=3))

    # header label
    ax.text(x + BOX_W / 2, yt - HDR_H / 2, e["display"],
            ha="center", va="center", fontsize=7.0, fontweight="bold",
            color=C["hdr_txt"], zorder=5, fontfamily="monospace")

    # header / body separator
    ax.plot([x, x + BOX_W], [yt - HDR_H] * 2, color=C["border"], lw=0.9, zorder=5)

    # attribute rows
    for i, (name, dtype, badge) in enumerate(e["attrs"]):
        ry  = yt - HDR_H - i * ROW_H
        rym = ry - ROW_H / 2

        if i % 2 == 1:
            ax.add_patch(mp.Rectangle(
                (x, ry - ROW_H), BOX_W, ROW_H,
                fc=C["alt_row"], lw=0, zorder=3))

        if i > 0:
            ax.plot([x, x + BOX_W], [ry] * 2, color=C["sep"], lw=0.3, zorder=4)

        tx = x + 0.08
        if badge:
            if   badge == "PK": bg, tc = C["pk_bg"], C["pk_txt"]
            elif badge == "FK": bg, tc = C["fk_bg"], C["fk_txt"]
            else:               bg, tc = C["uq_bg"], C["uq_txt"]
            bw, bh = 0.30, 0.13
            ax.add_patch(mp.FancyBboxPatch(
                (tx, rym - bh / 2), bw, bh,
                boxstyle="round,pad=0.01", lw=0.5,
                ec=tc, fc=bg, zorder=5))
            ax.text(tx + bw / 2, rym, badge,
                    ha="center", va="center", fontsize=5.0, fontweight="bold",
                    color=tc, zorder=6)
            tx += bw + 0.07

        ax.text(tx, rym, name,
                ha="left", va="center", fontsize=6.0,
                color=C["name"], zorder=5, fontfamily="monospace")
        ax.text(x + BOX_W - 0.06, rym, dtype,
                ha="right", va="center", fontsize=5.2,
                color=C["dtype"], style="italic", zorder=5)

    # border on top
    ax.add_patch(mp.FancyBboxPatch(
        (x, yb), BOX_W, h,
        boxstyle="round,pad=0.02", lw=1.3,
        ec=C["border"], fc="none", zorder=6))


def draw_rel(ax, fk, fa, tk, ta, optional, rad):
    fx, _ = box_pos(fk)
    tx, _ = box_pos(tk)
    fy = attr_y(fk, fa)
    ty = attr_y(tk, ta)
    fc, tc = LAYOUT[fk][0], LAYOUT[tk][0]

    if fc < tc:
        fp, tp = fx + BOX_W, tx
    elif fc > tc:
        fp, tp = fx, tx + BOX_W
    else:
        fp = tp = fx + BOX_W + 0.06   # same column → route right of both

    clr = C["arrow_opt"] if optional else C["arrow"]
    ax.annotate("", xy=(tp, ty), xytext=(fp, fy),
        arrowprops=dict(
            arrowstyle="-|>", color=clr, lw=1.0, mutation_scale=10,
            linestyle="--" if optional else "-",
            connectionstyle=f"arc3,rad={rad}",
        ), zorder=7)

    lbl = "0..N : 1" if optional else "N : 1"
    ax.text((fp + tp) / 2, (fy + ty) / 2 + 0.10, lbl,
            ha="center", va="bottom", fontsize=4.8, color=clr, zorder=8,
            bbox=dict(boxstyle="round,pad=0.07", fc="white", ec="none", alpha=0.88))


def draw_legend(ax):
    lx, ly = FIG_W - 2.25, 1.35
    ax.add_patch(mp.FancyBboxPatch(
        (lx - 0.12, ly - 1.05), 2.18, 1.22,
        boxstyle="round,pad=0.05", lw=0.8,
        ec=C["border"], fc="white", zorder=9))
    ax.text(lx + 0.84, ly + 0.10, "Legend",
            ha="center", fontsize=6.5, fontweight="bold", color=C["hdr_bg"], zorder=10)

    # arrows
    for i, (lbl, clr, ls) in enumerate([
        ("Required FK", C["arrow"],     "-"),
        ("Optional FK", C["arrow_opt"], "--"),
    ]):
        yy = ly - 0.18 - i * 0.28
        ax.annotate("", xy=(lx + 0.50, yy), xytext=(lx + 0.05, yy),
            arrowprops=dict(arrowstyle="-|>", color=clr, lw=1.0,
                            mutation_scale=8, linestyle=ls), zorder=10)
        ax.text(lx + 0.60, yy, lbl, va="center", fontsize=5.5, color=C["name"], zorder=10)

    # badges
    for i, (badge, bg, tc) in enumerate([
        ("PK", C["pk_bg"], C["pk_txt"]),
        ("FK", C["fk_bg"], C["fk_txt"]),
        ("UQ", C["uq_bg"], C["uq_txt"]),
    ]):
        yy = ly - 0.74 - i * 0.22
        ax.add_patch(mp.FancyBboxPatch(
            (lx + 0.05, yy - 0.065), 0.30, 0.13,
            boxstyle="round,pad=0.01", lw=0.5, ec=tc, fc=bg, zorder=10))
        ax.text(lx + 0.20, yy, badge,
                ha="center", va="center", fontsize=5.0, fontweight="bold",
                color=tc, zorder=11)
        full = {"PK": "Primary Key", "FK": "Foreign Key", "UQ": "Unique"}[badge]
        ax.text(lx + 0.60, yy, full, va="center", fontsize=5.5, color=C["name"], zorder=10)


# ─── Build figure ─────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
ax.set_xlim(0, FIG_W)
ax.set_ylim(0, FIG_H)
ax.axis("off")
fig.patch.set_facecolor(C["fig_bg"])
ax.set_facecolor(C["fig_bg"])

ax.text(FIG_W / 2, FIG_H - 0.22,
        "MediGuard — Entity Relationship Diagram",
        ha="center", va="center", fontsize=12, fontweight="bold",
        color=C["hdr_bg"], zorder=10)
ax.text(FIG_W / 2, FIG_H - 0.40,
        "9 tables  ·  SQLAlchemy / PostgreSQL",
        ha="center", va="center", fontsize=6.5, color=C["dtype"], zorder=10)

for rel in RELS:
    draw_rel(ax, *rel)

for key in LAYOUT:
    draw_entity(ax, key)

draw_legend(ax)

out = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "MediGuard_ERD.png"))
plt.savefig(out, dpi=180, bbox_inches="tight", facecolor=fig.get_facecolor())
print(f"Saved: {out}")
