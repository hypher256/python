#!/usr/bin/python3

import requests
import textwrap
import os

# Defining Key Variables
API_URL = "https://graphql.anilist.co"
OUTPUT_FOLDER = "/home/firefly/Notes/Logs/AniList"

# Function that uses cli input to use in GraphQL query
def search_media(media_type, title):
    query = """
    query ($search: String, $type: MediaType) {
      Page(perPage: 10) {
        media(search: $search, type: $type) {
          id
          title {
            romaji
            english
            native
          }
        }
      }
    }
    """
    variables = {"search": title, "type": media_type.upper()}
    response = requests.post(API_URL, json={"query": query, "variables": variables})
    #Return results for user to select from
    return response.json()["data"]["Page"]["media"]

# Function that gets the full details on seleced media based on the selected media ID
def get_media_details(media_id):
    query = """
    query ($id: Int) {
      Media(id: $id) {
        title {
          romaji
          english
          native
        }
        description(asHtml: false)
        coverImage {
          extraLarge
        }
        studios {
        edges   {
            isMain
            node {
                name
            }
        }
    }
        staff(perPage: 2){
        edges {
        role
        node {
            name {
                full
            }
        image {
            large
        }
    }
}
}
        characters(perPage: 3, sort: [ROLE, RELEVANCE]){
            edges {
                node {
                    name{
                        full
                    }
                    image {
                        large
                        }
                    }
                }
            }
        genres
        siteUrl
        type
      }
    }
    """
    variables = {"id": media_id}
    # Return the full results
    response = requests.post(API_URL, json={"query": query, "variables": variables})
    return response.json()["data"]["Media"]

# Create the .md file for obsidian in the folder we set
def save_markdown(media, score, status):
    folder_name = "Anime" if media["type"] == "ANIME" else "Manga"
    output_path = os.path.join(OUTPUT_FOLDER, folder_name)
    os.makedirs(output_path, exist_ok=True)

    # Title and filename
    title = media["title"].get("english") or media["title"].get("romaji") or media["title"].get("native")
    safe_title = "".join(c if c.isalnum() or c in (" ", "_", "-") else "_" for c in title).strip()
    filename = f"{safe_title}.md".replace("/", "-")

    # Description cleanup
    description = media.get("description") or "No description available."
    description = description.replace("<br>", "\n").replace("<i>", "").replace("</i>", "")
    description = textwrap.fill(description, width=100)

    # Genres
    genres = media.get("genres", [])
    genres_list = [g.replace(" ", "") for g in genres]  

    # --- Download the cover image ---
    cover_url = media["coverImage"]["extraLarge"]
    image_folder = os.path.join(output_path, "Covers")
    os.makedirs(image_folder, exist_ok=True)
    image_filename = f"{safe_title}.jpg"
    image_path = os.path.join(image_folder, image_filename)

    try:
        img_data = requests.get(cover_url).content
        with open(image_path, "wb") as img_file:
            img_file.write(img_data)
    except Exception as e:
        print(f"Failed to download image: {e}")
        image_filename = ""  # fallback if download fails

    # Get Studio
    studio_edges = media["studios"]["edges"]
    main_studio = next((s["node"]["name"] for s in studio_edges if s["isMain"]), None)

    # Get Staff
    staff = media["staff"]["edges"]
    for person in staff:
            name = person["node"]["name"]["full"]
            role = person["role"]
            image = person["node"]["image"]["large"]
    # Get Charcaters
    characters = media["characters"]["edges"]
    for char in characters:
        name = char["node"]["name"]["full"]
        image = char["node"]["image"]["large"]

    # --- Write Markdown File ---
    with open(os.path.join(output_path, filename), "w", encoding="utf-8") as f:
    # --- YAML Properties ---
        f.write(f"---\n")
        f.write(f"status: {status}\n")
        f.write(f'title: "{title}"\n')
        f.write(f"score: {score}\n")
        f.write(f"genres: [{', '.join(genres_list)}]\n")
        f.write(f"cover: {image_filename}\n")
        f.write(f"anilist_url: {media['siteUrl']}\n")
        f.write(f"media_type: {media['type'].lower()}\n")
        f.write(f"---\n\n---\n\n")
    # --- Body of file ---
        f.write(f"### **Score**: {score}\n")
        f.write(f"![[{image_filename}]]\n\n")
        f.write(f"## Description\n{description}\n\n---\n")
        f.write(f"### **Studio**: {main_studio or 'Unknown'}\n---\n") 
        f.write(f"### **Staff**\n\n")
        for staff_member in staff:
            name = staff_member["node"]["name"]["full"]
            role = staff_member["role"]
            img = staff_member["node"]["image"]["large"]
            f.write(f"#### {name} - *{role}*\n")
            f.write(f"![]({img})\n\n")
        f.write("---\n### Characters\n\n")
        for char in characters:
            name = char["node"]["name"]["full"]
            img = char["node"]["image"]["large"]
            f.write(f"#### {name}\n")
            f.write(f"![]({img})\n\n")
def main():

    print("Select type:")
    print("1: Anime")
    print("2: Manga")
    choice = input("Your choice: ").strip()

    media_type = "ANIME" if choice == "1" else "MANGA"
    title = input("Search: ").strip()
    results = search_media(media_type, title)

    if not results:
        print("No results found.")
        return

    print("\nSelect one:")
    for i, media in enumerate(results, 1):
        name = media["title"].get("english") or media["title"].get("romaji") or media["title"].get("native")
        print(f"{i}: {name}")

    selected = int(input("Your choice: ")) - 1
    selected_media = results[selected]
    full_details = get_media_details(selected_media["id"])

    score = input("Score out of 10?: ").strip()
    score = int(score) if score.isdigit() else None
    
    print("\nStatus?")
    print("1: Completed")
    print("2: Watching/Reading")
    print("3: Planning")

    status_choice = input("Status Option: ").strip()

    status_map = {
        "1": "Completed",
        "2": "Watching/Reading",
        "3": "Planning"
    }

    status = status_map.get(status_choice, "Planning")  # default to Planning if invalid

    save_markdown(full_details, score, status)
    print(f"\nEntry for {full_details['title']['english'] or full_details['title']['romaji']} saved!'")


if __name__ == "__main__":
    main()

