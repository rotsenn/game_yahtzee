"""Pruebas de las reglas de yahtzee_consola.py.

Uso:  python3 pruebas_reglas.py [partidas]     (por defecto 3000)
Juega partidas completas con jugadas al azar y revisa que los totales y bonos sean coherentes.
"""
import random
import sys

from yahtzee_console import Tarjeta, decidir_ia, puntos_base


def casos_concretos():
    """Casos puntuales de las reglas, calculados a mano."""
    assert puntos_base("full_house", [2, 2, 5, 5, 5]) == 25
    assert puntos_base("full_house", [3, 3, 3, 3, 3]) == 0          # Yahtzee no es Full sin comodín
    assert puntos_base("escalera_pequena", [1, 2, 3, 4, 4]) == 30
    assert puntos_base("escalera_grande", [2, 3, 4, 5, 6]) == 40
    assert puntos_base("trio", [2, 2, 2, 5, 6]) == 17

    t = Tarjeta()                                                    # bono superior: 63 -> +35
    t.p.update(unos=3, doses=6, treses=9, cuatros=12, cincos=15, seises=18)
    assert t.bono_sup == 35 and t.total == 63 + 35

    t = Tarjeta()                                                    # comodín con superior libre
    t.p["yahtzee"] = 50
    assert t.disponibles([4] * 5) == ["cuatros"]
    t.anotar("cuatros", [4] * 5)
    assert t.p["cuatros"] == 20 and t.bono_yahtzee == 100

    t = Tarjeta()                                                    # Yahtzee en 0: sin bono
    t.p["yahtzee"] = 0
    t.anotar("cuatros", [4] * 5)
    assert t.bono_yahtzee == 0


def partida_al_azar(rng):
    t = Tarjeta()
    while not t.completa():
        dice = [rng.randint(1, 6) for _ in range(5)]
        for _ in range(rng.randint(0, 2)):  # relanza al azar hasta 2 veces
            dice = [d if rng.random() < 0.6 else rng.randint(1, 6) for d in dice]
        t.anotar(rng.choice(t.disponibles(dice)), dice)
    return t


def revisar(t):
    suma = sum(t.p.values())
    assert t.total == suma + t.bono_sup + t.bono_yahtzee, "total mal calculado"
    assert t.bono_sup in (0, 35) and (t.bono_sup == 35) == (t.suma_sup >= 63), "bono superior"
    assert t.bono_yahtzee % 100 == 0, "bono Yahtzee no es múltiplo de 100"
    assert t.bono_yahtzee == 0 or t.p["yahtzee"] == 50, "bono Yahtzee sin 50 en Yahtzee"


def partida_ia(seed, sims):
    """Una partida de la IA sola (13 turnos); devuelve el total."""
    rng, t = random.Random(seed), Tarjeta()
    while not t.completa():
        dice, mant = [0] * 5, [False] * 5
        for rest in (2, 1, 0):
            dice = [d if mant[i] else rng.randint(1, 6) for i, d in enumerate(dice)]
            tipo, arg, _ = decidir_ia(dice, rest, t, sims, seed)
            if tipo == "anotar":
                t.anotar(arg, dice)
                break
            mant = arg
    return t.total


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 3000
    casos_concretos()
    print("Casos concretos: OK")
    rng = random.Random(1)
    for _ in range(n):
        revisar(partida_al_azar(rng))
    print(f"{n} partidas al azar: totales y bonos coherentes")
    print("Misma semilla, misma partida:", partida_ia(5, 20) == partida_ia(5, 20))