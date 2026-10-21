#!/usr/bin/env python3
"""Membuat gambar Gantt chart (PNG) dari simulator. Jalankan: python3 buat_gantt.py"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from simulator_penjadwalan import DATASET, ALGORITMA

WARNA = {"P1": "#8FB8DE", "P2": "#F4B183", "P3": "#A9D18E", "P4": "#FFD966", "P5": "#C9A7E8", "IDLE": "#D9D9D9"}
BERKAS = ["fcfs", "sjf", "srtf", "prio_np", "prio_p", "rr2", "rr3"]

for kode, (nama, fungsi) in zip(BERKAS, ALGORITMA):
    gantt, _ = fungsi(DATASET)
    akhir = gantt[-1][2]
    fig, ax = plt.subplots(figsize=(7.0, 1.25), dpi=200)
    for pid, s, e in gantt:
        ax.barh(0, e - s, left=s, height=0.6, color=WARNA[pid], edgecolor="black", linewidth=0.8)
        ax.text((s + e) / 2, 0, pid, ha="center", va="center", fontsize=8, fontweight="bold")
    ticks = sorted({0} | {s for _, s, _ in gantt} | {e for _, _, e in gantt})
    ax.set_xticks(ticks)
    ax.set_xlim(0, akhir)
    ax.set_ylim(-0.5, 0.5)
    ax.set_yticks([])
    ax.tick_params(axis="x", labelsize=7)
    for sp in ("left", "right", "top"):
        ax.spines[sp].set_visible(False)
    ax.set_title(f"Gantt chart {nama}", fontsize=9, loc="left")
    fig.tight_layout()
    fig.savefig(f"gantt_{kode}.png")
    plt.close(fig)
print("selesai")
