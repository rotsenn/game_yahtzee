#!/usr/bin/env python3
"""Yahtzee en consola: Tú contra Bill (IA Monte Carlo). Un solo archivo, solo biblioteca estándar.

Uso:  python3 yahtzee_consola.py [--sims 300] [--seed 42]

Reglas especiales (oficiales de Hasbro):
- Yahtzee = 50. Se puede anotar 0 en cualquier categoría libre.
- Sin comodín, un Yahtzee NO cuenta como Full House ni escalera.
- Bono superior +35 si unos..seises suman 63 o más (se calcula solo en el total, una vez).
- Yahtzee adicional (casilla Yahtzee ya ocupada): +100 solo si esa casilla tiene 50 (campo aparte).
  Comodín: 1) casilla superior de ese número si está libre; 2) si no, cualquier inferior libre
  (Full 25, esc. pequeña 30, esc. grande 40 a valor completo); 3) si no, 0 en una superior libre.

IA: heurística Monte Carlo (no se afirma que sea óptima). Evalúa qué dados conservar con N
simulaciones por opción y elige la categoría de mayor utilidad =
puntos − valor_base(categoría) + prima del bono superior [+100 si hay bono de Yahtzee].
Con --seed la decisión de la IA y los dados son reproducibles.
"""
import argparse
import math
import random
from collections import Counter

# ----------------------------------------------------------------- puntuación
UPPER = ["unos", "doses", "treses", "cuatros", "cincos", "seises"]
LOWER = ["trio", "cuatro_iguales", "full_house", "escalera_pequena", "escalera_grande",
         "chance", "yahtzee"]
CATEGORIES = UPPER + LOWER
NOMBRES = {"unos": "Unos", "doses": "Doses", "treses": "Treses", "cuatros": "Cuatros",
           "cincos": "Cincos", "seises": "Seises", "trio": "Trío",
           "cuatro_iguales": "Cuatro iguales", "full_house": "Full House",
           "escalera_pequena": "Escalera pequeña", "escalera_grande": "Escalera grande",
           "chance": "Chance", "yahtzee": "YAHTZEE"}
BONO_SUP, UMBRAL, BONO_YAHTZEE, PTS_YAHTZEE = 35, 63, 100, 50


def es_yahtzee(d):
    return len(set(d)) == 1


def puntos_base(cat, dice):
    c, total, caras = Counter(dice), sum(dice), set(dice)
    if cat in UPPER:
        n = UPPER.index(cat) + 1
        return n * c[n]
    if cat == "trio":
        return total if max(c.values()) >= 3 else 0
    if cat == "cuatro_iguales":
        return total if max(c.values()) >= 4 else 0
    if cat == "full_house":
        return 25 if sorted(c.values()) == [2, 3] else 0
    if cat == "escalera_pequena":
        return 30 if any(s <= caras for s in ({1, 2, 3, 4}, {2, 3, 4, 5}, {3, 4, 5, 6})) else 0
    if cat == "escalera_grande":
        return 40 if caras in ({1, 2, 3, 4, 5}, {2, 3, 4, 5, 6}) else 0
    if cat == "chance":
        return total
    return PTS_YAHTZEE if es_yahtzee(dice) else 0  # yahtzee


class Tarjeta:
    def __init__(self):
        self.p = {c: None for c in CATEGORIES}
        self.bono_yahtzee = 0

    def libres(self):
        return [c for c in CATEGORIES if self.p[c] is None]

    def completa(self):
        return not self.libres()

    def es_comodin(self, d):
        return es_yahtzee(d) and self.p["yahtzee"] is not None

    def disponibles(self, d):
        libres = self.libres()
        if not self.es_comodin(d):
            return libres
        sup = UPPER[d[0] - 1]
        if sup in libres:
            return [sup]
        inf = [c for c in libres if c in LOWER]
        return inf or libres

    def puntos(self, cat, d):
        if self.es_comodin(d) and cat in ("full_house", "escalera_pequena", "escalera_grande"):
            return {"full_house": 25, "escalera_pequena": 30, "escalera_grande": 40}[cat]
        return puntos_base(cat, d)

    def anotar(self, cat, d):
        if cat not in self.disponibles(d):
            raise ValueError(cat)
        pts = self.puntos(cat, d)
        if self.es_comodin(d) and self.p["yahtzee"] == PTS_YAHTZEE:
            self.bono_yahtzee += BONO_YAHTZEE
        self.p[cat] = pts
        return pts

    @property
    def suma_sup(self):
        return sum(self.p[c] or 0 for c in UPPER)

    @property
    def bono_sup(self):
        return BONO_SUP if self.suma_sup >= UMBRAL else 0

    @property
    def total(self):
        return sum(v or 0 for v in self.p.values()) + self.bono_sup + self.bono_yahtzee


# ------------------------------------------------------------------------ IA
BASE = {"unos": 2.1, "doses": 5.3, "treses": 8.6, "cuatros": 12.2, "cincos": 15.7,
        "seises": 19.2, "trio": 21.7, "cuatro_iguales": 13.1, "full_house": 22.6,
        "escalera_pequena": 29.5, "escalera_grande": 32.7, "chance": 22.0, "yahtzee": 16.9}


def utilidad(t, cat, d):
    pts = t.puntos(cat, d)
    sup = t.suma_sup + (pts if cat in UPPER else 0)
    if sup >= UMBRAL:
        prima = BONO_SUP
    else:
        resto = sum(BASE[c] for c in UPPER if t.p[c] is None and c != cat)
        prima = BONO_SUP / (1 + math.exp(-(sup + resto - UMBRAL) / 6.0))
    u = pts - BASE[cat] + prima
    if t.es_comodin(d) and t.p["yahtzee"] == PTS_YAHTZEE:
        u += BONO_YAHTZEE
    return u


def mejor(t, d):
    return max((utilidad(t, c, d), c) for c in t.disponibles(d))


def racha(caras):
    best, cur = [], []
    for f in sorted(caras):
        cur = cur + [f] if cur and f == cur[-1] + 1 else [f]
        best = cur if len(cur) > len(best) else best
    return best


def politica(d, t):
    c = Counter(d)
    if t.p["escalera_grande"] is None or t.p["escalera_pequena"] is None:
        r = racha(c)
        if len(r) >= 4 and max(c.values()) < 3:
            return r
    f = max(c, key=lambda x: (c[x], t.p[UPPER[x - 1]] is None, x))
    return [f] * c[f]


def rollout(kept, restantes, t, rng):
    d = list(kept) + [rng.randint(1, 6) for _ in range(5 - len(kept))]
    for _ in range(restantes - 1):
        k = politica(d, t)
        if len(k) == 5:
            break
        d = k + [rng.randint(1, 6) for _ in range(5 - len(k))]
    return mejor(t, d)[0]


def decidir_ia(dice, restantes, t, sims, seed):
    """-> ('conservar', mascara, texto) | ('anotar', categoria, texto)."""
    u_stop, cat = mejor(t, dice)
    if restantes == 0:
        return "anotar", cat, f"utilidad {u_stop:.1f}"
    rng = random.Random(repr((seed, dice, restantes, sorted(t.p.items()), t.bono_yahtzee))
                        if seed is not None else None)
    semillas = [rng.getrandbits(32) for _ in range(sims)]
    opciones = {}
    for m in range(31):
        idx = [i for i in range(5) if m >> i & 1]
        opciones.setdefault(tuple(sorted(dice[i] for i in idx)), [i in idx for i in range(5)])
    res = sorted(((sum(rollout(k, restantes, t, random.Random(s)) for s in semillas) / sims,
                   k, mask) for k, mask in opciones.items()), key=lambda r: r[0], reverse=True)
    media, kept, mask = res[0]
    if u_stop >= media:
        return "anotar", cat, f"utilidad {u_stop:.1f} frente a {media:.1f} de relanzar"
    rival = max([u_stop] + [r[0] for r in res[1:2]])
    que = "relanza los 5 dados" if not kept else "conserva " + "-".join(map(str, kept))
    return "conservar", mask, (f"{que} (utilidad media {media:.1f} frente a {rival:.1f} "
                               f"de la mejor alternativa; {sims} simulaciones)")


# ------------------------------------------------------------------- consola
def tabla(tarjetas, opciones=None):
    opciones = opciones or {}
    f = lambda a, b, c: f"{a:<20}{b:>8}{c:>8}"
    s = lambda v: "" if v is None else str(v)
    filas = [f("", "Tú", "Bill"), "-" * 36]
    for c in CATEGORIES:
        mio = s(tarjetas[0].p[c]) if tarjetas[0].p[c] is not None else (
            f"({opciones[c]})" if c in opciones else "")
        filas.append(f(NOMBRES[c], mio, s(tarjetas[1].p[c])))
        if c == "seises":
            filas.append(f("Suma", *(str(t.suma_sup) for t in tarjetas)))
            filas.append(f("Bonificación (63+)", *(str(t.bono_sup) for t in tarjetas)))
            filas.append("-" * 36)
    filas.append(f("Bono Yahtzee", *(str(t.bono_yahtzee) for t in tarjetas)))
    filas.append("-" * 36)
    filas.append(f("TOTAL", *(str(t.total) for t in tarjetas)))
    return "\n".join(filas)


def mostrar_dados(d, conservados=()):
    print("   " + "   ".join(f"[{v}]" for v in d))
    print("   " + "   ".join(f" {i + 1} " for i in range(5)))
    if conservados:
        print("   conservados: " + ", ".join(str(i + 1) for i in conservados))


def pedir(texto):
    try:
        return input(texto).strip().lower()
    except EOFError:
        raise SystemExit("\nEntrada finalizada.")


def turno_usuario(t, tarjetas, rng):
    dice, mantener = [0] * 5, [False] * 5
    for restantes in (2, 1, 0):  # tras cada lanzamiento
        dice = [d if mantener[i] else rng.randint(1, 6) for i, d in enumerate(dice)]
        print(f"\nLanzamiento {3 - restantes}/3:")
        mostrar_dados(dice, [i for i, m in enumerate(mantener) if m])
        if restantes == 0:
            break
        while True:
            r = pedir("Dados a CONSERVAR (ej. 1 3 5), Enter = relanzar todos, a = anotar: ")
            if r in ("a", "anotar"):
                restantes = -1
                break
            try:
                idx = {int(x) - 1 for x in r.replace(",", " ").split()}
                if all(0 <= i < 5 for i in idx):
                    mantener = [i in idx for i in range(5)]
                    break
            except ValueError:
                pass
            print("Entrada no válida.")
        if restantes == -1 or all(mantener):
            break
    opc = {c: t.puntos(c, dice) for c in t.disponibles(dice)}
    if t.es_comodin(dice):
        print("¡Yahtzee adicional! Se aplican las reglas de comodín.")
    print("\n" + tabla(tarjetas, opc))
    lista = list(opc)
    for n, c in enumerate(lista, 1):
        print(f"  {n:>2}) {NOMBRES[c]:<18} {opc[c]} pts")
    while True:
        r = pedir("Elige categoría (número): ")
        if r.isdigit() and 1 <= int(r) <= len(lista):
            cat = lista[int(r) - 1]
            print(f"Anotaste {t.anotar(cat, dice)} en {NOMBRES[cat]}.")
            return


def turno_ia(t, rng, sims, seed):
    print("\n--- Turno de Bill ---")
    dice, mantener = [0] * 5, [False] * 5
    for restantes in (2, 1, 0):
        dice = [d if mantener[i] else rng.randint(1, 6) for i, d in enumerate(dice)]
        print(f"Lanzamiento {3 - restantes}/3:")
        mostrar_dados(dice, [i for i, m in enumerate(mantener) if m])
        tipo, arg, texto = decidir_ia(dice, restantes, t, sims, seed)
        if tipo == "anotar":
            print(f"Bill anotó {t.anotar(arg, dice)} en {NOMBRES[arg]} ({texto}).")
            return
        mantener = arg
        print(f"Bill {texto}")


def main():
    ap = argparse.ArgumentParser(description="Yahtzee vs. IA Monte Carlo (consola)")
    ap.add_argument("--sims", type=int, default=300, help="simulaciones por opción (def. 300)")
    ap.add_argument("--seed", type=int, default=None, help="semilla para reproducir partidas")
    a = ap.parse_args()
    if a.sims < 1:
        ap.error("--sims debe ser ≥ 1")
    rng = random.Random(a.seed)
    tarjetas = [Tarjeta(), Tarjeta()]
    print(__doc__.split("IA:")[0].split("Reglas especiales")[0].strip())
    print("\nJuegas tú primero. 3 lanzamientos por turno; 13 categorías cada uno.")
    for ronda in range(1, 14):
        print(f"\n{'=' * 36}\nRONDA {ronda}/13\n{'=' * 36}")
        turno_usuario(tarjetas[0], tarjetas, rng)
        turno_ia(tarjetas[1], rng, a.sims, a.seed)
    print("\n" + tabla(tarjetas))
    x, y = tarjetas[0].total, tarjetas[1].total
    print("\n" + ("¡Empate!" if x == y else "¡Ganaste!" if x > y else "Gana Bill.") +
          f" (Tú {x} - Bill {y})")


if __name__ == "__main__":
    main()