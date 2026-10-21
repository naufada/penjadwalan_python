#!/usr/bin/env python3
"""Simulator penjadwalan CPU - Tugas K-2 Sistem Operasi (Kelas C, IoT & Smart Farming).

Algoritma: FCFS, SJF (non-preemptive), SRTF, Priority (non-preemptive dan preemptive),
Round Robin (quantum bebas). Angka prioritas kecil = prioritas tinggi.

Aturan seri (tie-break) yang dipakai di seluruh simulator:
  1. kriteria utama algoritma (arrival / burst / sisa burst / prioritas),
  2. jika masih seri, proses dengan nomor PID lebih kecil (P1 sebelum P2).
Pada Round Robin, proses yang baru tiba pada saat yang sama dengan kuantum habis
dimasukkan ke antrean SEBELUM proses yang baru saja di-preempt.
"""
from collections import deque

DATASET = [  # (pid, arrival, burst, prioritas)
    ("P1", 0, 3, 1),
    ("P2", 0, 6, 3),
    ("P3", 2, 4, 2),
    ("P4", 3, 8, 4),
    ("P5", 4, 2, 1),
]


def _hasil(proses, gantt):
    """Gabungkan irisan berurutan milik proses yang sama, lalu hitung metrik."""
    gabung = []
    for pid, s, e in gantt:
        if pid != "IDLE" and gabung and gabung[-1][0] == pid and gabung[-1][2] == s:
            gabung[-1] = (pid, gabung[-1][1], e)
        else:
            gabung.append((pid, s, e))
    mulai, selesai = {}, {}
    for pid, s, e in gabung:
        if pid == "IDLE":
            continue
        mulai.setdefault(pid, s)
        selesai[pid] = e
    metrik = {}
    for pid, at, bt, pr in proses:
        ct = selesai[pid]
        tat = ct - at
        metrik[pid] = dict(AT=at, BT=bt, PR=pr, CT=ct, TAT=tat, WT=tat - bt,
                           RT=mulai[pid] - at)
    return gabung, metrik


def non_preemptive(proses, kunci):
    sisa = list(proses)
    t, gantt = 0, []
    while sisa:
        siap = [p for p in sisa if p[1] <= t]
        if not siap:
            nxt = min(p[1] for p in sisa)
            gantt.append(("IDLE", t, nxt))
            t = nxt
            continue
        p = min(siap, key=kunci)
        gantt.append((p[0], t, t + p[2]))
        t += p[2]
        sisa.remove(p)
    return _hasil(proses, gantt)


def fcfs(proses):
    return non_preemptive(proses, lambda p: (p[1], p[0]))


def sjf(proses):
    return non_preemptive(proses, lambda p: (p[2], p[1], p[0]))


def priority_np(proses):
    return non_preemptive(proses, lambda p: (p[3], p[1], p[0]))


def preemptive(proses, kunci):
    """Keputusan dievaluasi tiap satuan waktu (kunci menerima (pid, sisa, prioritas, arrival))."""
    sisa = {p[0]: p[2] for p in proses}
    info = {p[0]: p for p in proses}
    t, gantt = 0, []
    while any(v > 0 for v in sisa.values()):
        siap = [pid for pid in sisa if sisa[pid] > 0 and info[pid][1] <= t]
        if not siap:
            gantt.append(("IDLE", t, t + 1))
            t += 1
            continue
        pid = min(siap, key=lambda x: kunci(x, sisa[x], info[x][3], info[x][1]))
        gantt.append((pid, t, t + 1))
        sisa[pid] -= 1
        t += 1
    return _hasil(proses, gantt)


def srtf(proses):
    return preemptive(proses, lambda pid, sisa, pr, at: (sisa, at, pid))


def priority_p(proses):
    return preemptive(proses, lambda pid, sisa, pr, at: (pr, at, pid))


def rr(proses, q):
    urut = sorted(proses, key=lambda p: (p[1], p[0]))
    sisa = {p[0]: p[2] for p in proses}
    antre, t, gantt, i = deque(), 0, [], 0

    def masuk(sampai):
        nonlocal i
        while i < len(urut) and urut[i][1] <= sampai:
            antre.append(urut[i][0])
            i += 1

    masuk(0)
    while antre or i < len(urut):
        if not antre:
            nxt = urut[i][1]
            gantt.append(("IDLE", t, nxt))
            t = nxt
            masuk(t)
            continue
        pid = antre.popleft()
        jalan = min(q, sisa[pid])
        gantt.append((pid, t, t + jalan))
        t += jalan
        sisa[pid] -= jalan
        masuk(t)                 # pendatang baru dulu ...
        if sisa[pid] > 0:
            antre.append(pid)    # ... baru proses yang di-preempt
    return _hasil(proses, gantt)


ALGORITMA = [
    ("FCFS", fcfs),
    ("SJF (non-preemptive)", sjf),
    ("SRTF (preemptive)", srtf),
    ("Priority (non-preemptive)", priority_np),
    ("Priority (preemptive)", priority_p),
    ("Round Robin q=2", lambda p: rr(p, 2)),
    ("Round Robin q=3", lambda p: rr(p, 3)),
]


def rata2(metrik):
    n = len(metrik)
    return {k: sum(m[k] for m in metrik.values()) / n for k in ("WT", "TAT", "RT")}


def cetak(nama, gantt, metrik):
    print(f"\n=== {nama} ===")
    print("Gantt : " + " ".join(f"|{p} {s}-{e}" for p, s, e in gantt) + "|")
    print(f"{'PID':<4}{'AT':>3}{'BT':>3}{'PR':>3}{'CT':>4}{'TAT':>5}{'WT':>4}{'RT':>4}")
    for pid in sorted(metrik):
        m = metrik[pid]
        print(f"{pid:<4}{m['AT']:>3}{m['BT']:>3}{m['PR']:>3}{m['CT']:>4}{m['TAT']:>5}{m['WT']:>4}{m['RT']:>4}")
    r = rata2(metrik)
    print(f"Rata-rata  WT={r['WT']:.2f}  TAT={r['TAT']:.2f}  RT={r['RT']:.2f}")


if __name__ == "__main__":
    ringkas = []
    for nama, fungsi in ALGORITMA:
        g, m = fungsi(DATASET)
        cetak(nama, g, m)
        ringkas.append((nama, rata2(m)))
    print("\n=== Tabel perbandingan ===")
    print(f"{'Algoritma':<28}{'Avg WT':>8}{'Avg TAT':>9}{'Avg RT':>8}")
    for nama, r in ringkas:
        print(f"{nama:<28}{r['WT']:>8.2f}{r['TAT']:>9.2f}{r['RT']:>8.2f}")
