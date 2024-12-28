#!/usr/bin/env python3

import os
import sys
import requests
from dotenv import dotenv_values
from requests_oauthlib import OAuth1

# Load config from .env (not merged into OS environ)
config = dotenv_values(".env")

########################################################
# Credentials
########################################################

X_CONSUMER_KEY = config["X_CONSUMER_KEY"]
X_CONSUMER_SECRET = config["X_CONSUMER_SECRET"]
X_ACCESS_TOKEN = config["X_ACCESS_TOKEN"]
X_ACCESS_SECRET = config["X_ACCESS_SECRET"]


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
# Posting Function: X (Twitter) using OAuth 1.0a
########################################################
def post_to_x(image_path, caption):
    """
    Posts a single image + caption to X (formerly Twitter) via v1.1 endpoints.
    Uses OAuth 1.0a with consumer and access tokens.
    """
    print(f"\n--- Posting to X ---")

    # Prepare OAuth 1.0a session
    oauth = OAuth1(
        client_key=X_CONSUMER_KEY,
        client_secret=X_CONSUMER_SECRET,
        resource_owner_key=X_ACCESS_TOKEN,
        resource_owner_secret=X_ACCESS_SECRET
    )

    # 1) Upload media
    upload_url = "https://upload.twitter.com/1.1/media/upload.json"
    with open(image_path, "rb") as f:
        files = {"media": f}
        upload_resp = requests.post(upload_url, auth=oauth, files=files)

    if upload_resp.status_code != 200:
        print("Error uploading media to X:", upload_resp.text)
        return

    media_id_str = upload_resp.json().get("media_id_string")
    if not media_id_str:
        print("Could not retrieve media_id_string from upload response.")
        return

    # 2) Post tweet with media
    post_url = "https://api.twitter.com/1.1/statuses/update.json"
    data = {
        "status": caption,
        "media_ids": media_id_str
    }
    resp = requests.post(post_url, auth=oauth, data=data)

    if resp.status_code == 200:
        print("Successfully posted to X.")
    else:
        print("Error posting to X:", resp.text)


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

    caption = input("\nEnter a caption for your X post: ").strip()
    if not caption:
        print("No caption entered. Exiting.")
        sys.exit(0)

    post_to_x(chosen_path, caption)

    print("\nDone posting to X.")


if __name__ == "__main__":
    main()
