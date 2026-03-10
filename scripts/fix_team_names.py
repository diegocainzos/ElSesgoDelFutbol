"""
Normaliza los nombres de club en la tabla players para que coincidan
con las claves de TEAM_LOGOS del dashboard.
"""

import sys
sys.path.insert(0, ".")

from sqlalchemy import text
from data_pipeline import db

# Mapeo: nombre en DB (mayúsculas, del TOML) -> nombre correcto (del dashboard)
TEAM_NAME_MAP = {
    "ATHLETIC CLUB":    "Athletic Club",
    "ATLETICO DE MADRID": "Atlético de Madrid",
    "BETIS":            "Real Betis",
    "ELCHE":            "Elche CF",
    "ESPANYOL":         "RCD Espanyol",
    "FC BARCELONA":     "FC Barcelona",
    "GETAFE":           "Getafe CF",
    "GIRONA":           "Girona FC",
    "LEVANTE":          "Levante UD",
    "MALLORCA":         "RCD Mallorca",
    "OSASUNA":          "CA Osasuna",
    "OVIEDO":           "Real Oviedo",
    "RAYO VALLLECANO":  "Rayo Vallecano",  # también corrige el typo (3 L)
    "RC CELTA DE VIGO": "Celta de Vigo",
    "REAL MADRID":      "Real Madrid",
    "REAL SOCIEDAD":    "Real Sociedad",
    "SEVILLA":          "Sevilla FC",
    "VALENCIA":         "Valencia CF",
    "VILLAREAL":        "Villarreal CF",  # también corrige el typo (1 L)
}

def main():
    with db.engine.begin() as conn:
        # Mostrar estado actual
        rows = conn.execute(text("SELECT DISTINCT club FROM players ORDER BY club")).fetchall()
        print("Clubs actuales en DB:")
        for row in rows:
            canonical = TEAM_NAME_MAP.get(row[0])
            marker = f" -> {canonical}" if canonical else " (ok)"
            print(f"  {row[0]!r}{marker}")

        print()
        updated_total = 0
        for old_name, new_name in TEAM_NAME_MAP.items():
            result = conn.execute(
                text("UPDATE players SET club = :new WHERE club = :old"),
                {"new": new_name, "old": old_name}
            )
            if result.rowcount > 0:
                print(f"  ✅ '{old_name}' -> '{new_name}' ({result.rowcount} jugadores)")
                updated_total += result.rowcount

        print(f"\nTotal: {updated_total} jugadores actualizados.")

        # Verificación final
        rows = conn.execute(text("SELECT DISTINCT club FROM players ORDER BY club")).fetchall()
        print("\nClubs en DB después de la migración:")
        for row in rows:
            print(f"  {row[0]!r}")

if __name__ == "__main__":
    main()
