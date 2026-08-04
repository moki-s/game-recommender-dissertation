import csv
import sys

sys.path.insert(0, "src/graph")
from connection import get_driver

# the input files this loader reads (all already normalised so titles match across sources)
INPUT_PATH = "data/processed/games_merged_normalised.csv"
AWARDS_PATH = "data/processed/awards_normalised.csv"
ACCESSIBILITY_PATH = "data/processed/accessibility_normalised.csv"
MOTIVATIONS_PATH = "data/processed/motivations.csv"

# numbers in my csv are stored as text and a few cells are blank so we convert to real number only when data exists and leave others empty
def to_int(value):
    return int(value) if value.strip() else None


RATING_AGES = {
    "PEGI 3": 3, "PEGI 7": 7, "PEGI 12": 12, "PEGI 16": 16, "PEGI 18": 18,
    "ESRB Everyone": 3, "ESRB Everyone 10+": 10, "ESRB Teen": 13,
    "ESRB Mature": 17, "ESRB Adults Only": 18, "Unknown": 99,
}


def get_rating_name(row):
    # we prefer the pegi rating (our target region), and fall back to the esrb rating only when pegi is unknown.
    pegi = row["pegi_rating"].strip()
    esrb = row["esrb_rating"].strip()
    if pegi and pegi != "unknown":
        return f"PEGI {pegi}"
    if esrb and esrb != "unknown":
        return f"ESRB {esrb}"
    return "Unknown"

# to delete deverything first so there are no dupes so script runs safely.
def wipe_database(session):
    session.run("MATCH (n) DETACH DELETE n")


def create_constraints(session):
    session.run("CREATE CONSTRAINT game_slug IF NOT EXISTS FOR (g:Game) REQUIRE g.slug IS UNIQUE")
    session.run("CREATE INDEX game_normalised IF NOT EXISTS FOR (g:Game) ON (g.normalised_title)")


def load_game(session, row):
    # MERGE is used here because it looks for a Game with this slug and creates one only if it doesn't already exist because we wiped the db
    # used llm help here to debug and understand better
    session.run(
        """
        MERGE (g:Game {slug: $slug})
        SET g.title = $title,
            g.normalised_title = $normalised_title,
            g.release_year = $release_year,
            g.metacritic = $metacritic,
            g.summary = $summary
        """,
        slug=row["slug"],
        title=row["title"],
        normalised_title=row["normalised_title"],
        release_year=to_int(row["release_year"]),
        metacritic=to_int(row["metacritic"]),
        summary=row["description"],
    )

    for platform in row["platforms"].split("; "):
        if platform.strip():
            # MERGE the Platform so all pc games point at ONE shared PC node
            session.run(
                """
                MATCH (g:Game {slug: $slug})
                MERGE (p:Platform {name: $name})
                MERGE (g)-[:AVAILABLE_ON]->(p)
                """,
                slug=row["slug"], name=platform.strip(),
            )

    # one shared Genre node per name, linked to this game
    for genre in row["genres"].split("; "):
        if genre.strip():
            session.run(
                """
                MATCH (g:Game {slug: $slug})
                MERGE (genre:Genre {name: $name})
                MERGE (g)-[:HAS_GENRE]->(genre)
                """,
                slug=row["slug"], name=genre.strip(),
            )

    rating_name = get_rating_name(row)
    session.run(
        """
        MATCH (g:Game {slug: $slug})
        MERGE (a:AgeRating {name: $name})
        SET a.age = $age
        MERGE (g)-[:RATED]->(a)
        """,
        # look the numeric age up from the table where the default to 99 if the name isn't listed
        slug=row["slug"], name=rating_name, age=RATING_AGES.get(rating_name, 99),
    )


def link_award(session, row):
    if row["result"] == "won":
        rel_type = "WON"
    else:
        rel_type = "NOMINATED_FOR"

    # we have to MATCH the game first and not MERGE so we never accidentally create an award for a game we don't have in our catalogue.
    # used LLM help here
    query = (
        "MATCH (g:Game {normalised_title: $nt}) "
        "MERGE (a:Award {name: $name, year: $year, category: $category}) "
        "MERGE (g)-[:" + rel_type + "]->(a) "
        "RETURN count(g) AS matched"
    )
    result = session.run(
        query,
        nt=row["normalised_title"],
        name=row["award_name"],
        year=int(row["year"]),
        category=row["category"],
    )
    return result.single()["matched"]


def load_awards(session):
    with open(AWARDS_PATH, encoding="utf-8") as f:
        awards = list(csv.DictReader(f))

    linked = 0
    skipped = 0
    for row in awards:
        matched = link_award(session, row)
        if matched > 0:
            linked += 1
        else:
            skipped += 1

    print(f"awards linked to a game: {linked}")
    print(f"awards skipped (game not in catalogue): {skipped}")

# we MATCH the game first so we never create a feature for a game outside our catalogue. MERGE the feature node on all three of its properties
# LLM used here to understand bugs in query
def link_feature(session, row):
    
    query = (
        "MATCH (g:Game {normalised_title: $nt}) "
        "MERGE (f:AccessibilityFeature {name: $name, category: $category, level: $level}) "
        "MERGE (g)-[r:SUPPORTS]->(f) "
        "SET r.source = $source "
        "RETURN count(g) AS matched"
    )
    result = session.run(
        query,
        nt=row["normalised_title"],
        name=row["feature_name"],
        category=row["category"],
        level=row["level"],
        source=row["source"],
    )
    return result.single()["matched"]


def load_accessibility(session):
    with open(ACCESSIBILITY_PATH, encoding="utf-8") as f:
        features = list(csv.DictReader(f))

    linked = 0
    skipped = 0
    for row in features:
        matched = link_feature(session, row)
        if matched > 0:
            linked += 1
        else:
            skipped += 1

    # ask the graph how many distinct games ended up with at least one accessibility feature
    games_with_access = session.run(
        "MATCH (g:Game)-[:SUPPORTS]->(:AccessibilityFeature) RETURN count(DISTINCT g) AS c"
    ).single()["c"]

    print(f"accessibility features linked: {linked} (skipped: {skipped})")
    print(f"games that now have accessibility data: {games_with_access}")

# themes and game modes are here loaded with the core graph and als oconnect games to it
def load_themes_and_modes(session):
    
    with open(INPUT_PATH, encoding="utf-8") as f:
        games = list(csv.DictReader(f))

    for row in games:
        for theme in row["themes"].split("; "):
            if theme.strip():
                session.run(
                    """
                    MATCH (g:Game {slug: $slug})
                    MERGE (t:Theme {name: $name})
                    MERGE (g)-[:HAS_THEME]->(t)
                    """,
                    slug=row["slug"], name=theme.strip(),
                )
        for mode in row["game_modes"].split("; "):
            if mode.strip():
                session.run(
                    """
                    MATCH (g:Game {slug: $slug})
                    MERGE (m:GameMode {name: $name})
                    MERGE (g)-[:HAS_MODE]->(m)
                    """,
                    slug=row["slug"], name=mode.strip(),
                )


def load_motivations(session):
    with open(MOTIVATIONS_PATH, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    

    label_for_type = {"genre": "Genre", "theme": "Theme", "game_mode": "GameMode"}

    made = 0
    for row in rows:
        session.run(
            "MERGE (m:Motivation {name: $name}) SET m.component = $component",
            name=row["motivation"], component=row["component"],
        )

        label = label_for_type[row["satisfied_by_type"]]

        # design choice i made here is that no direct game to motivation link as a game reaches a motivation through its
        # genres or themes or modes, and that path (game)->(x)<-[:SATISFIED_BY]-(motivation) IS the explanation 
        query = (
            "MATCH (m:Motivation {name: $name}) "
            "MATCH (x:" + label + " {name: $value}) "
            "MERGE (m)-[:SATISFIED_BY]->(x) "
            "RETURN count(x) AS matched"
        )
        result = session.run(query, name=row["motivation"], value=row["satisfied_by_value"])
        made += result.single()["matched"]

    print(f"motivation SATISFIED_BY links created: {made}")


def print_summary(session):
    # count what we ended up with so we can sanity-check the load at a glance.
    # this small inner helper runs a count query and returns the single number it produces.
    def count(query):
        return session.run(query).single()["c"]

    print()
    print("=== load summary ===")
    print("Game nodes:      ", count("MATCH (g:Game) RETURN count(g) AS c"))
    print("Platform nodes:  ", count("MATCH (p:Platform) RETURN count(p) AS c"))
    print("Genre nodes:     ", count("MATCH (g:Genre) RETURN count(g) AS c"))
    print("AgeRating nodes: ", count("MATCH (a:AgeRating) RETURN count(a) AS c"))
    print("Award nodes:     ", count("MATCH (a:Award) RETURN count(a) AS c"))
    print("AccessibilityFeature nodes:", count("MATCH (f:AccessibilityFeature) RETURN count(f) AS c"))
    print("Theme nodes:     ", count("MATCH (t:Theme) RETURN count(t) AS c"))
    print("GameMode nodes:  ", count("MATCH (m:GameMode) RETURN count(m) AS c"))
    print("Motivation nodes:", count("MATCH (m:Motivation) RETURN count(m) AS c"))
    print("AVAILABLE_ON rels:", count("MATCH ()-[r:AVAILABLE_ON]->() RETURN count(r) AS c"))
    print("HAS_GENRE rels:   ", count("MATCH ()-[r:HAS_GENRE]->() RETURN count(r) AS c"))
    print("RATED rels:       ", count("MATCH ()-[r:RATED]->() RETURN count(r) AS c"))
    print("WON rels:         ", count("MATCH ()-[r:WON]->() RETURN count(r) AS c"))
    print("NOMINATED_FOR rels:", count("MATCH ()-[r:NOMINATED_FOR]->() RETURN count(r) AS c"))
    print("SUPPORTS rels:    ", count("MATCH ()-[r:SUPPORTS]->() RETURN count(r) AS c"))
    print("HAS_THEME rels:   ", count("MATCH ()-[r:HAS_THEME]->() RETURN count(r) AS c"))
    print("HAS_MODE rels:    ", count("MATCH ()-[r:HAS_MODE]->() RETURN count(r) AS c"))
    print("SATISFIED_BY rels:", count("MATCH ()-[r:SATISFIED_BY]->() RETURN count(r) AS c"))


if __name__ == "__main__":
    with open(INPUT_PATH, encoding="utf-8") as f:
        games = list(csv.DictReader(f))

    driver = get_driver()
    with driver.session() as session:
        print("clearing any existing data...")
        wipe_database(session)

        print("creating constraints...")
        create_constraints(session)

        print(f"loading {len(games)} games...")
        for i, row in enumerate(games, start=1):
            load_game(session, row)
            if i % 50 == 0:
                print(f"  loaded {i}/{len(games)} games")

        print("loading awards...")
        load_awards(session)

        print("loading accessibility features...")
        load_accessibility(session)

        print("loading themes and game modes...")
        load_themes_and_modes(session)

        print("loading motivations...")
        load_motivations(session)

        print_summary(session)

    driver.close()
    print("\ndone.")
