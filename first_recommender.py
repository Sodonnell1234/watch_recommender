import pandas as pd
import numpy as np
from pathlib import Path
import json

# A tiny "catalog" of movies/shows
items = pd.DataFrame([
    {"title": "Stranger Things", "genres": ["Sci-Fi", "Drama", "Thriller"]},
    {"title": "The Office", "genres": ["Comedy"]},
    {"title": "Breaking Bad", "genres": ["Crime", "Drama", "Thriller"]},
    {"title": "Interstellar", "genres": ["Sci-Fi", "Drama"]},
    {"title": "Parks and Rec", "genres": ["Comedy"]},
    {"title": "The Dark Knight", "genres": ["Action", "Crime", "Drama"]},
    {"title": "Black Mirror", "genres": ["Sci-Fi", "Drama", "Thriller"]},
    {"title": "Brooklyn Nine-Nine", "genres": ["Comedy", "Crime"]},
    {"title": "The Matrix", "genres": ["Action", "Sci-Fi"]},
    {"title": "Severance", "genres": ["Sci-Fi", "Drama", "Thriller"]},
])

def norm_title(s: str) -> str:
    return s.strip().lower()

# Build normalized catalog helpers
catalog_keys = {norm_title(t) for t in items["title"]}
title_lookup = {norm_title(t): t for t in items["title"]}


# Method for adding movies to a profile
def addMovie(profile, path):
    while True:
        setup = {"title": '', "rating": 0}
        answer = input("Enter movie/show name (-1 to exit) -> ")
        if answer == '-1':
            break

        user_key = norm_title(answer)

        if user_key not in catalog_keys:
            print("Movie/Show not in dataset\n")
            continue

        # Use the title from the dataset
        nice_title = title_lookup[user_key]

        already_rated = any(norm_title(entry["title"]) == user_key
            for entry in profile["ratings"])

        if already_rated:
            print("Movie/Show already logged\n")
            continue

        setup['title'] = nice_title
        print(f"append {setup['title']}")

        while True:
            answer = input(f"Enter the rating for {setup['title']} (1 worst -> 10 best) -> ")
            if answer.isdigit() and 1 <= int(answer) <= 10:
                break

        rating = int(answer)
        print(f"append {rating}")
        setup["rating"] = rating
        profile["ratings"].append(setup)

    path.write_text(json.dumps(profile, indent=2), encoding="utf-8")
    return pd.DataFrame(profile["ratings"])


# Method for removing a movie from a profile
def removeMovie(profile, path):
    while True:
        answer = input("Enter movie/show name (-1 to exit) -> ")
        if answer == '-1':
            break

        user_key = norm_title(answer)

        in_list = any(
            norm_title(entry["title"]) == user_key
            for entry in profile["ratings"]
        )

        if not in_list:
            print("Movie/Show not in profile\n")
            continue

        print(f"removing {answer}")

        i = -1
        for entry in profile["ratings"]:
            i += 1
            if norm_title(entry["title"]) == user_key:
                del profile["ratings"][i]
                path.write_text(json.dumps(profile, indent=2), encoding="utf-8")
                break


# Method for changing the rating of a movie in your profile list
def changeRating(profile):
    while True:
        answer = input("Enter movie/show name (-1 to exit) -> ")
        if answer == '-1':
            break

        user_key = norm_title(answer)

        already_rated = any(
            norm_title(entry["title"]) == user_key
            for entry in profile["ratings"]
        )

        if not already_rated:
            print("Movie/Show not in profile\n")
            continue

        print(f"editing {answer}\n")

        while True:
            change = input("Enter your new rating -> ").strip()

            if change.isdigit() and 1 <= int(change) <= 10:
                for entry in profile["ratings"]:
                    if norm_title(entry["title"]) == user_key:
                        entry["rating"] = int(change)
                        break
                break
            else:
                print("Enter a valid number!\n")
                continue

def showList(profile, path):
    for entry in profile["ratings"]:
        print(f"Movie/Show: {entry['title']} Rating: {entry['rating']}")
    print()

def editMode(profile, path):
    while True:
        edit = input("What would you like to do? (-1 to quit)\n"
                     "See your list? (S)\n"
                     "Add a movie/show? (A)\n"
                     "Remove a movie/show? (R)\n"
                     "Change a rating? (C)\n"
                     "-> ").lower()
        if edit == '-1':
            break
        if edit not in {'a', 'r', 'c', 's'}:
            print("Not a valid choice!")
            continue
        if edit == 'a':
            addMovie(profile, path)
        elif edit == 'r':
            removeMovie(profile, path)
        elif edit == 's':
            showList(profile, path)
        else:
            changeRating(profile)


def explain(genre_matrix, user_profile, title: str, top_k: int = 3) -> str:
    # Which genres of this item contribute most to the score?
    item_vec = genre_matrix.loc[title]
    contrib = item_vec * user_profile
    top = contrib.sort_values(ascending=False).head(top_k)
    top = top[top > 0]
    if top.empty:
        return "No strong genre match."
    return "Top matches: " + ", ".join([f"{g} ({v:.2f})" for g, v in top.items()])


def main() -> None:
    # User history or create a new user
    user = input("Enter your username: ").strip().lower()

    profiles_dir = Path("profiles")
    profiles_dir.mkdir(exist_ok=True)  # create folder if needed

    path = profiles_dir / f"{user}.json"

    if path.exists():
        print("Profile found!\n")

        profile = json.loads(path.read_text(encoding="utf-8"))
        # profile is a dict like {"username": "...", "ratings": [...]}

        while True:
            action = input(
                "Edit your list? (E)\n"
                "Run recommender? (R)\n"
                "Show current list? (S)\n"
                "Quit? (Q)\n"
                "-> "
            ).upper()

            if action == "E":
                print("Editing mode\n")
                editMode(profile, path)
            elif action == "R":
                print("Recommending mode\n")
                break
            elif action == "S":
                print("Showing your list\n")
                showList(profile, path)
            elif action == "Q":
                print("Quitting")
                return
            else:
                print("Invalid action. Please enter E, R, or Q.")
    else:
        print("Profile not found. Creating new profile.\n")

        # Create the .json for the user
        profile = {"username": user, "ratings": []}
        path.write_text(json.dumps(profile, indent=2), encoding="utf-8")

        addMovie(profile, path)

    # Build ratings DataFrame from stored ratings
    ratings = pd.DataFrame(profile["ratings"])

    if ratings.empty:
        print("\nNo ratings found. Add some titles first.")
        return

    # 1) Find all unique genres in the catalog
    all_genres = sorted({g for gs in items["genres"] for g in gs})

    # 2) Build a one-hot matrix: each row = item, each column = genre
    genre_matrix = pd.DataFrame(0, index=items["title"], columns=all_genres)

    for _, row in items.iterrows():
        for g in row["genres"]:
            genre_matrix.loc[row["title"], g] = 1

    # Join ratings with the genre vectors of those titles
    rated = ratings.merge(
        genre_matrix.reset_index().rename(columns={"index": "title"}),
        on="title",
        how="inner"
    )

    if rated.empty:
        print("\nNone of your rated titles matched the catalog. (Check titles / normalization.)")
        return

    # Compute preference score per genre as a weighted average
    # (rating * genre_indicator), summed across watched items
    genre_cols = all_genres
    weighted_sum = (rated[genre_cols].T * rated["rating"].values).T.sum(axis=0)

    # Normalize so the vector is easier to interpret
    user_profile = weighted_sum / weighted_sum.sum()

    print("\nUser preference profile (higher = you like that genre more):")
    print(user_profile.sort_values(ascending=False))

    # Titles already rated should not be recommended
    rated_titles = set(ratings["title"])

    # Score = dot(item_genre_vector, user_profile)
    scores = genre_matrix.dot(user_profile)

    # Remove already-rated items
    scores = scores[~scores.index.isin(rated_titles)]

    # Top recommendations
    top_n = 5
    recs = scores.sort_values(ascending=False).head(top_n)

    print("\nTop recommendations:")
    print(recs)

    print("\nRecommendations with explanations:")
    for title, score in recs.items():
        print(f"- {title}: {score:.3f} | {explain(genre_matrix, user_profile, title)}")


if __name__ == "__main__":
    main()