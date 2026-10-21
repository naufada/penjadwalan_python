#!/usr/bin/env python3
"""Pengujian simulator penjadwalan CPU (K-2 Sistem Operasi).
Jalankan: python3 uji_simulator.py
"""
from simulator_penjadwalan import (DATASET, fcfs, sjf, srtf, priority_np, priority_p, rr, rata2)

# ---- Nilai harapan hasil perhitungan manual (Bab 6.1): (avg WT, avg TAT, avg RT)
HARAPAN = {
    "FCFS":      (fcfs,                 (7.40, 12.00, 7.40)),
    "SJF":       (sjf,                  (5.00,  9.60, 5.00)),
    "SRTF":      (srtf,                 (4.80,  9.40, 4.40)),
    "PRIO-NP":   (priority_np,          (5.00,  9.60, 5.00)),
    "PRIO-P":    (priority_p,           (4.80,  9.40, 4.40)),
    "RR q=2":    (lambda p: rr(p, 2),   (8.60, 13.20, 2.60)),
    "RR q=3":    (lambda p: rr(p, 3),   (8.60, 13.20, 4.20)),
}


def referensi(proses, mode, q=None):
    """Implementasi pembanding yang ditulis terpisah: simulasi per satuan waktu,
    tanpa memakai fungsi apa pun dari simulator utama."""
    at = {p[0]: p[1] for p in proses}
    bt = {p[0]: p[2] for p in proses}
    pr = {p[0]: p[3] for p in proses}
    sisa = dict(bt)
    urut, selesai, mulai = [], {}, {}
    t = 0

    if mode == "rr":
        antre, kini, jatah = [], None, 0

        def datang(waktu):
            for pid in sorted(at, key=lambda x: (at[x], x)):
                if at[pid] == waktu:
                    antre.append(pid)

        datang(0)
        while len(selesai) < len(proses):
            if kini is None and antre:
                kini, jatah = antre.pop(0), q
            if kini is None:
                urut.append("IDLE"); t += 1; datang(t); continue
            mulai.setdefault(kini, t)
            urut.append(kini)
            sisa[kini] -= 1; jatah -= 1; t += 1
            datang(t)                          # pendatang pada t masuk lebih dulu
            if sisa[kini] == 0:
                selesai[kini] = t; kini = None
            elif jatah == 0:
                antre.append(kini); kini = None
    else:
        kini = None
        while len(selesai) < len(proses):
            siap = [x for x in at if at[x] <= t and sisa[x] > 0]
            if not siap:
                urut.append("IDLE"); t += 1; continue
            if mode == "fcfs":
                kunci = lambda x: (at[x], x)
            elif mode == "sjf":
                kunci = lambda x: (bt[x], at[x], x)
            elif mode == "srtf":
                kunci = lambda x: (sisa[x], at[x], x)
            elif mode == "prio_np":
                kunci = lambda x: (pr[x], at[x], x)
            else:
                kunci = lambda x: (pr[x], at[x], x)
            preemptif = mode in ("srtf", "prio_p")
            if kini is None or preemptif:
                kini = min(siap, key=kunci)
            mulai.setdefault(kini, t)
            urut.append(kini)
            sisa[kini] -= 1; t += 1
            if sisa[kini] == 0:
                selesai[kini] = t; kini = None
    m = {x: dict(CT=selesai[x], TAT=selesai[x] - at[x], WT=selesai[x] - at[x] - bt[x],
                 RT=mulai[x] - at[x]) for x in at}
    return urut, m


def cek_invarian(proses, gantt, metrik):
    total = sum(e - s for p, s, e in gantt if p != "IDLE")
    assert total == sum(p[2] for p in proses), "total irisan != total burst"
    for (p1, s1, e1), (p2, s2, e2) in zip(gantt, gantt[1:]):
        assert e1 == s2, "ada celah/tumpang tindih pada Gantt"
    at = {p[0]: p[1] for p in proses}
    for p, s, e in gantt:
        if p != "IDLE":
            assert s >= at[p], f"{p} berjalan sebelum tiba"
    for pid, m in metrik.items():
        assert m["TAT"] == m["WT"] + m["BT"], f"TAT != WT+BT untuk {pid}"


def jalankan():
    hasil = []

    def uji(nomor, nama, fn):
        try:
            fn()
            hasil.append((nomor, nama, "LULUS"))
        except AssertionError as err:
            hasil.append((nomor, nama, f"GAGAL: {err}"))

    def u1():
        for nama, (fn, (w, t, r)) in HARAPAN.items():
            _, m = fn(DATASET)
            a = rata2(m)
            assert (round(a["WT"], 2), round(a["TAT"], 2), round(a["RT"], 2)) == (w, t, r), nama

    def u2():
        peta = {"FCFS": ("fcfs", None), "SJF": ("sjf", None), "SRTF": ("srtf", None),
                "PRIO-NP": ("prio_np", None), "PRIO-P": ("prio_p", None),
                "RR q=2": ("rr", 2), "RR q=3": ("rr", 3)}
        for nama, (fn, _) in HARAPAN.items():
            g, m = fn(DATASET)
            mode, q = peta[nama]
            urut_ref, m_ref = referensi(DATASET, mode, q)
            urut_sim = [p for p, s, e in g for _ in range(e - s)]
            assert urut_sim == urut_ref, f"{nama}: urutan Gantt berbeda dari implementasi pembanding"
            for pid in m:
                for k in ("CT", "TAT", "WT", "RT"):
                    assert m[pid][k] == m_ref[pid][k], f"{nama}: {pid}.{k}"

    def u3():
        for nama, (fn, _) in HARAPAN.items():
            g, m = fn(DATASET)
            cek_invarian(DATASET, g, m)

    def u4():
        data = [("A", 0, 2, 1), ("B", 5, 3, 1)]
        g, m = fcfs(data)
        assert ("IDLE", 2, 5) in g and m["B"]["CT"] == 8 and m["B"]["WT"] == 0
        g, m = rr(data, 2)
        assert ("IDLE", 2, 5) in g and m["B"]["CT"] == 8

    def u5():
        g1, m1 = fcfs(DATASET)
        g2, m2 = rr(DATASET, 8)           # kuantum >= burst terbesar
        assert m1 == m2, "RR dengan kuantum besar harus identik dengan FCFS"

    def u6():
        g, _ = fcfs(DATASET)
        assert g[0][0] == "P1" and g[1][0] == "P2"
        g, _ = priority_np([("X", 0, 3, 2), ("Y", 0, 3, 2)])
        assert g[0][0] == "X"

    def u7():
        g, m = srtf([("Z", 0, 4, 1)])
        assert g == [("Z", 0, 4)] and m["Z"]["WT"] == 0 and m["Z"]["RT"] == 0

    uji(1, "Dataset kelas: 7 algoritma sama dengan hitungan manual", u1)
    uji(2, "Silang-periksa dengan implementasi pembanding", u2)
    uji(3, "Invarian metrik (TAT=WT+BT, tanpa celah, tidak jalan sebelum tiba)", u3)
    uji(4, "Kasus CPU idle (jeda antar kedatangan)", u4)
    uji(5, "RR dengan kuantum >= burst terbesar identik dengan FCFS", u5)
    uji(6, "Aturan seri: arrival/prioritas sama -> PID lebih kecil dahulu", u6)
    uji(7, "Satu proses tunggal", u7)
    return hasil


if __name__ == "__main__":
    h = jalankan()
    for n, nama, st in h:
        print(f"Uji {n}: {nama:<66} {st}")
    print(f"\nRingkasan: {sum(s == 'LULUS' for _,_,s in h)}/{len(h)} lulus")
