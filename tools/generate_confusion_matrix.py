#!/usr/bin/env python3
"""Generate a readable confusion matrix PNG for the Random Forest model."""

import os, sys, warnings
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "mediguard-backend"))
warnings.filterwarnings("ignore")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
import pandas as pd
import joblib
from sklearn.metrics import confusion_matrix

BASE   = os.path.join(os.path.dirname(__file__), "..", "mediguard-backend")
TRAIN  = os.path.join(BASE, "data", "processed", "mediguard_train.csv")
TEST   = os.path.join(BASE, "data", "processed", "mediguard_test.csv")
MODELS = os.path.join(BASE, "models")
OUT    = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "MediGuard_Confusion_Matrix.png"))

df_train = pd.read_csv(TRAIN)
df_test  = pd.read_csv(TEST)
symptoms = [c for c in df_train.columns if c != "disease"]

X_test  = df_test[symptoms].astype(int)
y_test  = df_test["disease"]

rf    = joblib.load(os.path.join(MODELS, "random_forest.pkl"))
preds = rf.predict(X_test)

labels = sorted(y_test.unique())
cm     = confusion_matrix(y_test, preds, labels=labels)

# Normalize row-wise (recall per class)
cm_norm = cm.astype(float)
row_sums = cm.sum(axis=1, keepdims=True)
row_sums[row_sums == 0] = 1
cm_norm = cm_norm / row_sums

n = len(labels)
cell = 0.52   # inches per cell
fig_size = n * cell + 3.0
fig, ax = plt.subplots(figsize=(fig_size, fig_size))
fig.patch.set_facecolor("#f8fafc")
ax.set_facecolor("#f8fafc")

# Custom colormap: white → cyan
cmap = mcolors.LinearSegmentedColormap.from_list(
    "mediguard", ["#f8fafc", "#e0f2fe", "#0891b2", "#0e7490"])

im = ax.imshow(cm_norm, cmap=cmap, vmin=0.0, vmax=1.0, aspect="auto")

# Colour bar
cbar = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02)
cbar.set_label("Recall (row-normalised)", fontsize=9, color="#0f172a")
cbar.ax.tick_params(labelsize=7)

# Axis labels
ax.set_xticks(range(n)); ax.set_yticks(range(n))
ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=6.5, fontfamily="monospace")
ax.set_yticklabels(labels, fontsize=6.5, fontfamily="monospace")
ax.set_xlabel("Predicted Label", fontsize=10, labelpad=8, color="#0f172a", fontweight="bold")
ax.set_ylabel("True Label",      fontsize=10, labelpad=8, color="#0f172a", fontweight="bold")
ax.set_title("MediGuard — Random Forest Confusion Matrix\n"
             "(row-normalised; diagonal = recall per disease)",
             fontsize=11, fontweight="bold", color="#0891b2", pad=14)

# Cell annotations
threshold = 0.35
for i in range(n):
    for j in range(n):
        v = cm_norm[i, j]
        if v > 0.01:
            txt_color = "white" if v > threshold else "#0f172a"
            ax.text(j, i, f"{v:.2f}", ha="center", va="center",
                    fontsize=4.8 if n > 30 else 6.0,
                    color=txt_color, fontweight="bold" if i == j else "normal")

plt.tight_layout(pad=1.0)
plt.savefig(OUT, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
print(f"Saved: {OUT}")
