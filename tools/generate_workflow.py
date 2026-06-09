#!/usr/bin/env python3
"""Generate MediGuard main user-workflow diagram as a PNG."""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mp
import os

FIG_W, FIG_H = 16.0, 20.0
CLR_BG     = "#f0f9ff"
CLR_START  = "#0891b2"   # cyan  — terminal nodes
CLR_PROC   = "#0e7490"   # teal  — process / action
CLR_DEC    = "#1e40af"   # blue  — decision diamond
CLR_DATA   = "#6d28d9"   # purple — data store / API call
CLR_END    = "#dc2626"   # red   — error / exit
CLR_TXT    = "#ffffff"
CLR_ARROW  = "#334155"
CLR_ANNOT  = "#64748b"
CLR_BORDER = "#0891b2"

# ─── Node definitions ────────────────────────────────────────────────────────
# shape: 'oval' | 'rect' | 'diamond' | 'data'
# (id, label, x_center, y_center, width, height, shape, color)
NODES = [
    # ── User entry ──
    ("start",        "User Opens\nMediGuard",          8.0, 19.2,  2.2, 0.55, "oval",    CLR_START),

    # ── Auth flow ──
    ("auth_q",       "Registered\nUser?",              8.0, 18.3,  1.9, 0.80, "diamond", CLR_DEC),
    ("register",     "Register\n(name · email · pw)",  4.8, 17.4,  2.4, 0.55, "rect",    CLR_PROC),
    ("login",        "Log In\n(email + password)",     11.2, 17.4,  2.4, 0.55, "rect",    CLR_PROC),
    ("jwt",          "JWT Issued\n& Stored",           8.0, 16.5,  2.2, 0.55, "data",    CLR_DATA),

    # ── Home / dashboard ──
    ("dashboard",    "Home Dashboard\n(symptom banner · alerts)",  8.0, 15.5,  3.0, 0.55, "rect", CLR_PROC),

    # ── Choose path ──
    ("choose",       "Choose\nFeature",                8.0, 14.5,  1.9, 0.80, "diamond", CLR_DEC),

    # ── Branch A — Symptom checker ──
    ("symptoms",     "Select\nSymptoms",               3.5, 13.4,  2.4, 0.55, "rect",    CLR_PROC),
    ("predict_api",  "POST /predict\n(RF + NB + DT)",  3.5, 12.4,  2.4, 0.55, "data",    CLR_DATA),
    ("results",      "View Top-5\nDiagnoses + %",      3.5, 11.4,  2.4, 0.55, "rect",    CLR_PROC),
    ("log_q",        "Save to\nHistory?",              3.5, 10.4,  1.9, 0.70, "diamond", CLR_DEC),
    ("history_save", "Saved to\nPrediction History",   3.5,  9.5,  2.4, 0.55, "data",    CLR_DATA),
    ("feedback",     "Submit\nFeedback (helpful?)",    3.5,  8.6,  2.4, 0.55, "rect",    CLR_PROC),

    # ── Branch B — AI Chat ──
    ("chat_input",   "Type Health\nQuestion",          8.0, 13.4,  2.4, 0.55, "rect",    CLR_PROC),
    ("rag_api",      "RAG Query\n(Pinecone + GPT-4o)", 8.0, 12.4,  2.4, 0.55, "data",    CLR_DATA),
    ("chat_resp",    "AI Response +\nFollow-up Qs",    8.0, 11.4,  2.4, 0.55, "rect",    CLR_PROC),
    ("chat_save",    "Chat Saved\nto History",         8.0, 10.4,  2.4, 0.55, "data",    CLR_DATA),
    ("chat_fb",      "Rate Response\n(Helpful / Not)",  8.0,  9.5,  2.4, 0.55, "rect",    CLR_PROC),

    # ── Branch C — Disease Library ──
    ("search_dis",   "Search /\nBrowse Diseases",     12.5, 13.4,  2.4, 0.55, "rect",    CLR_PROC),
    ("dis_detail",   "View Disease\nDetail Page",     12.5, 12.4,  2.4, 0.55, "rect",    CLR_PROC),
    ("dis_info",     "Symptoms · Causes\n· Treatment · Prev.",  12.5, 11.4,  2.4, 0.55, "rect", CLR_PROC),

    # ── Newsletter / notifications ──
    ("notif_q",      "Notifications\nEnabled?",        8.0,  7.5,  1.9, 0.70, "diamond", CLR_DEC),
    ("subscribe",    "Subscribe\n(email opt-in)",       5.5,  6.6,  2.2, 0.55, "rect",    CLR_PROC),
    ("weekly_email", "Weekly Outbreak\nAlert Email",    8.0,  6.6,  2.4, 0.55, "data",    CLR_DATA),

    # ── Account management ──
    ("account",      "Account\nSettings",             10.5,  6.6,  2.2, 0.55, "rect",    CLR_PROC),
    ("account_opts", "Update Profile ·\nToggle Notifs · Reset Pw",  10.5,  5.7,  2.8, 0.55, "rect", CLR_PROC),

    # ── Contact ──
    ("contact",      "Contact\nSupport",              10.5,  4.8,  2.2, 0.55, "rect",    CLR_PROC),
    ("contact_save", "Message Saved\n(admin notified)",10.5,  3.9,  2.4, 0.55, "data",   CLR_DATA),

    # ── End ──
    ("end",          "Session End\n(JWT expires / logout)",  8.0,  2.8,  2.8, 0.55, "oval", CLR_START),
]

# ─── Arrow definitions ───────────────────────────────────────────────────────
# (from_id, to_id, label, dx_from, dy_from, dx_to, dy_to, rad)
ARROWS = [
    ("start",       "auth_q",      "",              0, -0.28, 0,  0.40, 0.0),
    ("auth_q",      "register",    "No",           -0.95, 0, 1.2, 0.28, 0.0),
    ("auth_q",      "login",       "Yes",           0.95, 0,-1.2, 0.28, 0.0),
    ("register",    "jwt",          "",              1.2, 0,  -1.1, 0.28, 0.0),
    ("login",       "jwt",          "",             -1.2, 0,   1.1, 0.28, 0.0),
    ("jwt",         "dashboard",   "",              0, -0.28, 0,  0.28, 0.0),
    ("dashboard",   "choose",      "",              0, -0.28, 0,  0.40, 0.0),

    # choose → branches
    ("choose",      "symptoms",    "Symptom\nCheck", -0.95, 0,  1.2, 0.28, 0.0),
    ("choose",      "chat_input",  "AI Chat",        0, -0.40, 0,  0.28, 0.0),
    ("choose",      "search_dis",  "Disease\nInfo",  0.95, 0, -1.2, 0.28, 0.0),

    # symptom branch
    ("symptoms",    "predict_api", "",              0, -0.28, 0,  0.28, 0.0),
    ("predict_api", "results",     "",              0, -0.28, 0,  0.28, 0.0),
    ("results",     "log_q",       "",              0, -0.28, 0,  0.35, 0.0),
    ("log_q",       "history_save","Yes",           0, -0.35, 0,  0.28, 0.0),
    ("log_q",       "feedback",    "No",            0.95,  0, 1.0, 0,   0.15),
    ("history_save","feedback",    "",              0, -0.28, 0,  0.28, 0.0),

    # chat branch
    ("chat_input",  "rag_api",     "",              0, -0.28, 0,  0.28, 0.0),
    ("rag_api",     "chat_resp",   "",              0, -0.28, 0,  0.28, 0.0),
    ("chat_resp",   "chat_save",   "",              0, -0.28, 0,  0.28, 0.0),
    ("chat_save",   "chat_fb",     "",              0, -0.28, 0,  0.28, 0.0),

    # disease branch
    ("search_dis",  "dis_detail",  "",              0, -0.28, 0,  0.28, 0.0),
    ("dis_detail",  "dis_info",    "",              0, -0.28, 0,  0.28, 0.0),

    # converge to notifications
    ("feedback",    "notif_q",     "",              0, -0.28, -3.5, 0.35, -0.3),
    ("chat_fb",     "notif_q",     "",              0, -0.28,  0,   0.35,  0.0),
    ("dis_info",    "notif_q",     "",              0, -0.28,  4.5, 0.35,  0.3),

    # notif branch
    ("notif_q",     "subscribe",   "No",           -0.95, 0, 1.1, 0.28, 0.0),
    ("notif_q",     "weekly_email","Yes",            0,  -0.35, 0,  0.28, 0.0),
    ("notif_q",     "account",     "Settings",      0.95, 0,-1.1, 0.28, 0.0),

    # account
    ("account",     "account_opts","",              0, -0.28, 0,  0.28, 0.0),
    ("account_opts","contact",     "",              0, -0.28, 0,  0.28, 0.0),
    ("contact",     "contact_save","",              0, -0.28, 0,  0.28, 0.0),

    # converge to end
    ("subscribe",   "end",         "",              0, -0.28,  -2.5, 0.28, -0.2),
    ("weekly_email","end",         "",              0, -0.28,   0,   0.28,  0.0),
    ("contact_save","end",         "",              0, -0.28,   2.5, 0.28,  0.2),
]

# ─── Draw helpers ────────────────────────────────────────────────────────────
node_map = {n[0]: n for n in NODES}

def draw_node(ax, node):
    nid, label, cx, cy, w, h, shape, color = node
    if shape == "oval":
        ax.add_patch(mp.Ellipse((cx, cy), w, h, fc=color, ec=color, lw=1.5, zorder=3))
        ax.add_patch(mp.Ellipse((cx+0.05, cy-0.05), w, h,
                                fc="#94a3b8", ec="none", lw=0, zorder=2, alpha=0.4))
    elif shape == "diamond":
        dx, dy = w/2, h/2
        pts = [(cx, cy+dy), (cx+dx, cy), (cx, cy-dy), (cx-dx, cy)]
        ax.add_patch(mp.Polygon(pts, closed=True, fc=color, ec=color, lw=1.5, zorder=3))
        pts2 = [(p[0]+0.05, p[1]-0.05) for p in pts]
        ax.add_patch(mp.Polygon(pts2, closed=True, fc="#94a3b8", ec="none", lw=0,
                                zorder=2, alpha=0.4))
    elif shape == "data":
        # parallelogram
        s = 0.12
        xs = [cx-w/2+s, cx+w/2+s, cx+w/2-s, cx-w/2-s]
        ys = [cy+h/2, cy+h/2, cy-h/2, cy-h/2]
        ax.add_patch(mp.Polygon(list(zip(xs,ys)), closed=True,
                                fc=color, ec=color, lw=1.5, zorder=3))
        xs2 = [x+0.05 for x in xs]; ys2 = [y-0.05 for y in ys]
        ax.add_patch(mp.Polygon(list(zip(xs2,ys2)), closed=True,
                                fc="#94a3b8", ec="none", lw=0, zorder=2, alpha=0.4))
    else:  # rect
        ax.add_patch(mp.FancyBboxPatch((cx-w/2+0.05, cy-h/2-0.05), w, h,
                                       boxstyle="round,pad=0.04",
                                       fc="#94a3b8", ec="none", lw=0, zorder=2, alpha=0.4))
        ax.add_patch(mp.FancyBboxPatch((cx-w/2, cy-h/2), w, h,
                                       boxstyle="round,pad=0.04",
                                       fc=color, ec=color, lw=1.5, zorder=3))

    lines = label.split("\n")
    for li, line in enumerate(lines):
        offset = (len(lines)-1)*0.10 - li*0.20
        ax.text(cx, cy + offset, line, ha="center", va="center",
                fontsize=6.8, color=CLR_TXT, fontweight="bold",
                zorder=5, linespacing=1.3)


def node_edge(nid, dx, dy):
    _, _, cx, cy, w, h, shape, _ = node_map[nid]
    return cx + dx, cy + dy


def draw_arrow(ax, arrow):
    fid, tid, label, dfx, dfy, dtx, dty, rad = arrow
    _, _, fcx, fcy, fw, fh, fshp, _ = node_map[fid]
    _, _, tcx, tcy, tw, th, tshp, _ = node_map[tid]

    fx = fcx + dfx
    fy = fcy + dfy
    tx = tcx + dtx
    ty = tcy + dty

    ax.annotate("", xy=(tx, ty), xytext=(fx, fy),
        arrowprops=dict(
            arrowstyle="-|>", color=CLR_ARROW, lw=1.1,
            mutation_scale=10,
            connectionstyle=f"arc3,rad={rad}",
        ), zorder=4)

    if label:
        mx = (fx + tx) / 2
        my = (fy + ty) / 2
        ax.text(mx, my, label, ha="center", va="center",
                fontsize=6.0, color=CLR_ANNOT, zorder=6,
                bbox=dict(boxstyle="round,pad=0.08", fc="white", ec="none", alpha=0.9))


# ─── Build figure ────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
ax.set_xlim(0, FIG_W)
ax.set_ylim(2.0, FIG_H)
ax.axis("off")
fig.patch.set_facecolor(CLR_BG)
ax.set_facecolor(CLR_BG)

# Title
ax.text(FIG_W/2, 19.72, "MediGuard — Main User Workflow",
        ha="center", va="center", fontsize=13, fontweight="bold",
        color=CLR_START, zorder=10)
ax.text(FIG_W/2, 19.52, "End-to-end journey from app open to session end",
        ha="center", va="center", fontsize=7.5, color=CLR_ANNOT, zorder=10)

# Column labels
for lbl, cx in [("Symptom Checker", 3.5), ("AI Health Chat", 8.0), ("Disease Library", 12.5)]:
    ax.text(cx, 14.05, lbl, ha="center", va="center", fontsize=6.5,
            color=CLR_ANNOT, style="italic",
            bbox=dict(boxstyle="round,pad=0.15", fc="white", ec=CLR_BORDER, alpha=0.7, lw=0.6))

# Light lane backgrounds
for cx, w_lane in [(3.5, 3.0), (8.0, 3.2), (12.5, 3.0)]:
    ax.add_patch(mp.FancyBboxPatch(
        (cx - w_lane/2, 8.1), w_lane, 5.7,
        boxstyle="round,pad=0.1", fc="#dbeafe", ec="#bae6fd", lw=0.6,
        alpha=0.25, zorder=1))

# Legend
lx, ly = 0.3, 5.4
ax.add_patch(mp.FancyBboxPatch((lx-0.1, ly-1.75), 2.6, 2.0,
             boxstyle="round,pad=0.1", fc="white", ec=CLR_BORDER, lw=0.7, zorder=8))
ax.text(lx+1.1, ly+0.15, "Legend", ha="center", fontsize=7, fontweight="bold",
        color=CLR_START, zorder=9)
legend_items = [
    (CLR_START, "oval",    "Start / End"),
    (CLR_PROC,  "rect",    "Action / Process"),
    (CLR_DEC,   "diamond", "Decision"),
    (CLR_DATA,  "data",    "Data / API Call"),
]
for i, (clr, shp, lbl) in enumerate(legend_items):
    iy = ly - 0.2 - i * 0.38
    # mini shape
    if shp == "oval":
        ax.add_patch(mp.Ellipse((lx+0.22, iy), 0.30, 0.22, fc=clr, ec=clr, lw=0.8, zorder=9))
    elif shp == "diamond":
        ax.add_patch(mp.Polygon([(lx+0.22,iy+0.14),(lx+0.38,iy),(lx+0.22,iy-0.14),(lx+0.06,iy)],
                                fc=clr, ec=clr, lw=0.8, zorder=9))
    elif shp == "data":
        xs = [lx+0.08, lx+0.40, lx+0.36, lx+0.04]
        ys = [iy+0.12, iy+0.12, iy-0.12, iy-0.12]
        ax.add_patch(mp.Polygon(list(zip(xs,ys)), closed=True, fc=clr, ec=clr, lw=0.8, zorder=9))
    else:
        ax.add_patch(mp.FancyBboxPatch((lx+0.05,iy-0.12), 0.34, 0.24,
                                       boxstyle="round,pad=0.02", fc=clr, ec=clr, lw=0.8, zorder=9))
    ax.text(lx+0.55, iy, lbl, va="center", fontsize=6.5, color="#0f172a", zorder=9)

# Draw arrows then nodes (nodes on top)
for arrow in ARROWS:
    draw_arrow(ax, arrow)
for node in NODES:
    draw_node(ax, node)

out = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "MediGuard_User_Workflow.png"))
plt.savefig(out, dpi=180, bbox_inches="tight", facecolor=fig.get_facecolor())
print(f"Saved: {out}")
