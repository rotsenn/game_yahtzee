"""Compara la IA Monte Carlo de yahtzee_consola.py con un jugador simple.

Uso:  python3 comparar_ia.py [simulaciones] [partidas]     (por defecto 60 y 20)
Jugador simple: conserva los dados que más se repiten y anota donde más puntos gana en ese momento.
"""
import random
import statistics as st
import sys
import time
from collections import Counter

from yahtzee_console import Tarjeta, decidir_ia


def simple(dice, rest, t):
    """Misma salida que decidir_ia: ('conservar', mascara) o ('anotar', categoria)."""
    if rest > 0:
        moda = Counter(dice).most_common(1)[0][0]
        mask = [d == moda for d in dice]
        if not all(mask):
            return "conservar", mask
    opc = {c: t.puntos(c, dice) for c in t.disponibles(dice)}
    return "anotar", max(opc, key=opc.get)


def turno(t, quien, rng, sims, seed):
    dice, mant = [0] * 5, [False] * 5
    for rest in (2, 1, 0):
        dice = [d if mant[i] else rng.randint(1, 6) for i, d in enumerate(dice)]
        tipo, arg = (decidir_ia(dice, rest, t, sims, seed)[:2] if quien == "ia"
                     else simple(dice, rest, t))
        if tipo == "anotar":
            t.anotar(arg, dice)
            return
        mant = arg


def solitario(quien, seed, sims):
    """Partida de un solo jugador; devuelve su total."""
    rng, t = random.Random(seed), Tarjeta()
    while not t.completa():
        turno(t, quien, rng, sims, seed)
    return t.total


def duelo(seed, sims):
    """IA contra jugador simple; alterna quién empieza. Devuelve (total_ia, total_simple)."""
    rng = random.Random(seed)
    t = {"ia": Tarjeta(), "simple": Tarjeta()}
    orden = ["ia", "simple"] if seed % 2 == 0 else ["simple", "ia"]
    for _ in range(13):
        for quien in orden:
            turno(t[quien], quien, rng, sims, seed)
    return t["ia"].total, t["simple"].total


if __name__ == "__main__":
    sims = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    ini = time.time()
    ia = [solitario("ia", s, sims) for s in range(n)]
    simp = [solitario("simple", s, sims) for s in range(10 * n)]
    print(f"IA ({sims} sim.): media {st.mean(ia):.1f}, desv. {st.pstdev(ia):.1f}, {n} partidas")
    print(f"Simple: media {st.mean(simp):.1f}, desv. {st.pstdev(simp):.1f}, {10 * n} partidas")
    duelos = [duelo(s, sims) for s in range(n)]
    gana = sum(a > b for a, b in duelos)
    empata = sum(a == b for a, b in duelos)
    print(f"Duelos IA vs simple: gana la IA {gana}/{n}, empates {empata}")
    print(f"Tiempo: {time.time() - ini:.0f} s")