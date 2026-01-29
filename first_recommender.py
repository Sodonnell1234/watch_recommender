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

def addMovie(profile):
    while True:
        setup = {"title": '', "rating": ''}
        answer = input("Enter movie name (-1 to exit) -> ")
        if answer == '-1':
            break
        setup['title'] = answer
        print(f"append {setup['title']}")
        while True:
            answer = input(f"Enter the rating for {setup['title']} (1 worst -> 10 best) -> ")
            if answer.isdigit() and int(answer) >= 1 and int(answer) <= 10:
                break
        rating = int(answer)
        print(f"append {rating}")
        setup["rating"] = rating
        profile["ratings"].append(setup)
    path.write_text(json.dumps(profile, indent=2), encoding="utf-8")
    ratings_df = pd.DataFrame(profile["ratings"])


# User history or create a new user
user = input("Enter your username: ").strip().lower()

profiles_dir = Path("profiles")
profiles_dir.mkdir(exist_ok=True)          # create folder if needed

user = user.strip().lower()
path = profiles_dir / f"{user}.json"

if path.exists():
    print("Profile found!\n")

    profile = json.loads(path.read_text(encoding="utf-8"))
    # profile is a dict like {"username": "...", "ratings": [...]}

    while True:
        action = input(
            "Edit your list? (E)\n"
            "Run recommender? (R)\n"
            "Quit? (Q)\n"
            "-> "
        ).upper()

        if action == "E":
            print("Editing mode")
        elif action == "R":
            print("Recommending mode")
        elif action == "Q":
            print("Quitting")
            break
        else:
            print("Invalid action. Please enter E, R, or Q.")
else:
    print("Profile not found. Creating new profile.\n")

    # Create the .json for the user
    profile = {"username": user, "ratings": []}
    path.write_text(json.dumps(profile, indent=2), encoding="utf-8")

    addMovie(profile)

ratings = pd.DataFrame([
    {"title": "Stranger Things", "rating": 5},
    {"title": "The Office", "rating": 4},
    {"title": "Interstellar", "rating": 5},
    {"title": "Parks and Rec", "rating": 2},
])

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

# Compute preference score per genre as a weighted average
# (rating * genre_indicator), summed across watched items
genre_cols = all_genres
weighted_sum = (rated[genre_cols].T * rated["rating"].values).T.sum(axis=0)

# Normalize so the vector is easier to interpret
user_profile = weighted_sum / weighted_sum.sum()

print("User preference profile (higher = you like that genre more):")
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

def explain(title: str, top_k: int = 3) -> str:
    # Which genres of this item contribute most to the score?
    item_vec = genre_matrix.loc[title]
    contrib = item_vec * user_profile
    top = contrib.sort_values(ascending=False).head(top_k)
    top = top[top > 0]
    if top.empty:
        return "No strong genre match."
    return "Top matches: " + ", ".join([f"{g} ({v:.2f})" for g, v in top.items()])


print("\nRecommendations with explanations:")
for title, score in recs.items():
    print(f"- {title}: {score:.3f} | {explain(title)}")
