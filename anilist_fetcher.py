import requests
import textwrap
import os

# Defining Key Variables
API_URL = "https://graphql.anilist.co"
OUTPUT_FOLDER = "/home/firefly/Notes/Logs/AniList"

# GraphQL query to search and return media option
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

# Function that gets the full details on seleced media based on the selected media page option
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
          large
        }
        genres
        siteUrl
        type
      }
    }
    """
    variables = {"id": media_id}
    response = requests.post(API_URL, json={"query": query, "variables": variables})
    return response.json()["data"]["Media"]

    ## Create the .md file for obsidian in the folder we set
def save_markdown(media, score, status):
    folder_name = "Anime" if media["type"] == "ANIME" else "Manga"
    output_path = os.path.join(OUTPUT_FOLDER, folder_name)
    os.makedirs(output_path, exist_ok=True)

    # Set the file name as the media title, replacing unsafe chracters
    title = media["title"].get("english") or media["title"].get("romaji") or media["title"].get("native")
    safe_title = "".join(c if c.isalnum() or c in (" ", "_", "-") else "_" for c in title).strip()
    filename = f"{safe_title}.md".replace("/", "-")

    # Description cleanup, replcaing HTML syntax with md syntax
    description = media.get("description") or "No description available."
    description = description.replace("<br>", "\n").replace("<i>", "").replace("</i>", "")
    description = textwrap.fill(description, width=100)

    # Genres, removing spaces for the YAML table
    genres = media.get("genres", [])
    genres_list = [g.replace(" ", "") for g in genres]  

    # --- Download the cover image ---
    cover_url = media["coverImage"]["large"]
    image_folder = os.path.join(output_path, "Covers")
    os.makedirs(image_folder, exist_ok=True)
    image_filename = f"{safe_title}.jpg"
    image_path = os.path.join(image_folder, image_filename)

    try:
        img_data = requests.get(cover_url).content
        with open(image_path, "wb") as img_file:
            img_file.write(img_data)
    except Exception as e:
        print(f"❌ Failed to download image: {e}")
        image_filename = ""  # fallback if download fails

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
        f.write(f"---\n\n")
    # --- Body of file ---
        f.write(f"### **Score**: {score}\n") #Am considering making a dropdown menu for the status
        f.write(f"![[{image_filename}]]\n\n")
        f.write(f"## Description\n{description}\n")

## Main function to use cli input
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

