### What it does
This code makes an API post request to anilist.com to fetch some details about the anime or manga you searched for.
The idea is that after answering a few questions, you can pull in details on a media and automatically create an md file with the key details.
The md file is formatted with Obsidian in mind, personally I've also set up a main page note that uses DataCards to organize each note into a gallery view, similar to the AniList itself.

- Cover images are downloaded locally, but staff and character images are just URLs since I don't mind as much if those links break.


### Considerations
Make sure to change OUTPUT\_FOLDER since it's currently hardcoded to my personal username.


### Issues
For the cover image, I can't get YAML to accept "[[]]" around the cover image name.
I want "[[]]" because it will reference the YAML to the downloaded image as a note reference, but doing so from Python breaks the YAML, adding it after the fact works fine...



