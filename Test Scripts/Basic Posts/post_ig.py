#!/usr/bin/env python3

import os
import sys
import requests
from dotenv import dotenv_values

# Load config from .env
config = dotenv_values(".env")

########################################################
# Credentials
########################################################

INSTAGRAM_ACCESS_TOKEN = config["INSTAGRAM_ACCESS_TOKEN"]
INSTAGRAM_USER_ID = config["INSTAGRAM_USER_ID"]


########################################################
# Utility: List media files
########################################################
def list_media_files(directory):
    """
    Returns a list of image file paths in the given directory.
    This example filters for typical image extensions.
    """
    if not os.path.exists(directory):
        print(f"Directory '{directory}' does not exist.")
        return []

    valid_extensions = (".png", ".jpg", ".jpeg", ".gif", ".webp")
    files = [
        f for f in os.listdir(directory)
        if f.lower().endswith(valid_extensions)
    ]
    return [os.path.join(directory, f) for f in files]


########################################################
# Posting Function: Instagram
########################################################
def post_to_instagram(image_path, caption):
    """
    Posts a single image + caption to Instagram using the
    Content Publishing API.

    IMPORTANT: This direct local file upload approach may require
               special permissions. If it fails, you likely need
               to host the image at a public URL first, then pass
               'image_url' instead of local file data.
    """
    print(f"\n--- Posting to Instagram ---")

    create_url = f"https://graph.facebook.com/v16.0/{INSTAGRAM_USER_ID}/media"

    # Attempt direct file upload (multipart). Might fail if your app lacks this permission.
    with open(image_path, "rb") as image_file:
        files = {
            'file': (os.path.basename(image_path), image_file, 'image/jpeg')
        }
        data = {
            'caption': caption,
            'access_token': INSTAGRAM_ACCESS_TOKEN
        }
        create_resp = requests.post(create_url, files=files, data=data)

    if create_resp.status_code != 200:
        print("Error creating Instagram container:", create_resp.text)
        return

    creation_id = create_resp.json().get("id")
    if not creation_id:
        print("Could not retrieve creation_id from container response.")
        return

    # Publish the container
    publish_url = f"https://graph.facebook.com/v16.0/{INSTAGRAM_USER_ID}/media_publish"
    publish_data = {
        'creation_id': creation_id,
        'access_token': INSTAGRAM_ACCESS_TOKEN
    }
    publish_resp = requests.post(publish_url, data=publish_data)

    if publish_resp.status_code == 200:
        print("Successfully posted to Instagram.")
    else:
        print("Error publishing Instagram post:", publish_resp.text)


########################################################
# Main
########################################################
def main():
    media_dir = "media"
    image_files = list_media_files(media_dir)

    if not image_files:
        print(f"No images found in directory '{media_dir}'. Exiting.")
        sys.exit(0)

    # If multiple images exist, let user pick one.
    print("Images available in 'media':")
    for idx, fpath in enumerate(image_files, start=1):
        print(f"{idx}. {fpath}")

    if len(image_files) == 1:
        chosen_path = image_files[0]
        print(f"\nOnly one image found. Using: {chosen_path}")
    else:
        choice = input("\nEnter the number of the image you want to post (default=1): ").strip()
        if not choice:
            choice = "1"
        try:
            choice_idx = int(choice) - 1
            chosen_path = image_files[choice_idx]
        except (ValueError, IndexError):
            print("Invalid choice. Defaulting to the first image.")
            chosen_path = image_files[0]

    caption = input("\nEnter a caption for your Instagram post: ").strip()
    if not caption:
        print("No caption entered. Exiting.")
        sys.exit(0)

    post_to_instagram(chosen_path, caption)

    print("\nDone posting to Instagram.")


if __name__ == "__main__":
    main()
