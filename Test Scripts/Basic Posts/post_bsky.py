#!/usr/bin/env python3
# A script to post up to four images with a caption to Bluesky, that will re-size and/or compress them to fit within file size guidelines.
# Written by Luke Spots (luke_spots.bsky.social, @luke_spots, lukespots.com)

from dotenv import dotenv_values
from atproto import Client
from io import BytesIO
from PIL import Image
import os

# ======== START USER CONFIGURABLE DATA ======== #

post_text = "Compressing images?" # Caption your post here. Currently does not support tagging people (as far as I know).
directory = "media" # Specify the directory where your images are stored.

# ======== END USER CONFIGURABLE DATA ======== #

# Load Bluesky credentials from .env
config = dotenv_values(".env")
BLUESKY_USERNAME = config["BLUESKY_USERNAME"]
BLUESKY_PASSWORD = config["BLUESKY_PASSWORD"]

# Define the client helper
client = Client()
client.login(BLUESKY_USERNAME, BLUESKY_PASSWORD)

def post_images(post_text, directory):
	# Gather all image file paths in the directory
	paths = [
    	os.path.join(directory, file)
    	for file in os.listdir(directory)
    	if file.lower().endswith((".jpg", ".jpeg", ".png", ".gif"))
		]
	
	images = []
	# Function to scale down an image if its longest side exceeds 2000px
	def scale_down_image(img, max_dimension=2000):
		width, height = img.size
		if max(width, height) > max_dimension:
			scaling_factor = max_dimension / max(width, height)
			new_width = int(width * scaling_factor)
			new_height = int(height * scaling_factor)
			img = img.resize((new_width, new_height), Image.LANCZOS)
		return img

	# Function to compress an image to meet size requirements
	def compress_image(img, max_size=1_000_000):
		buffer = BytesIO()
		quality = 85  # Start with high quality
		while True:
			buffer.seek(0)
			buffer.truncate()  # Clear buffer for next attempt
			img.save(buffer, format="JPEG", optimize=True, quality=quality)
			size = buffer.tell()
			if size <= max_size:  # Stop if size is met
				break
			quality -= 5  # Decrease quality incrementally
		return buffer.getvalue(), size

	for path in paths[:4]:  # Limit to the first 4 images if needed
		if not os.path.exists(path):
			print(f"File not found: {path}")
			continue

		try:
			# Open the image using Pillow
			with Image.open(path) as img:
				# Convert image to RGB if not already (to avoid issues with formats like PNG with transparency)
				if img.mode != "RGB":
					img = img.convert("RGB")

				# Save to a temporary buffer to check the initial size
				buffer = BytesIO()
				img.save(buffer, format="JPEG", optimize=True, quality=85)
				initial_size = buffer.tell()

				# Check if the image needs scaling down
				if initial_size > 1_000_000:
					original_width, original_height = img.size
					if max(original_width, original_height) > 2000:
						img = scale_down_image(img)
						# Save the scaled-down image to check size again
						buffer.seek(0)
						buffer.truncate()
						img.save(buffer, format="JPEG", optimize=True, quality=85)
						scaled_size = buffer.tell()
						print(f"Scaled down image: {path}, new size: {scaled_size} bytes")
					else:
						scaled_size = initial_size

					# Compress the image if still over size limit
					if scaled_size > 1_000_000:
						compressed_image, final_size = compress_image(img)
						images.append(compressed_image)
						print(f"Compressed and loaded image: {path}, size: {final_size} bytes")
					else:
						images.append(buffer.getvalue())
						print(f"Loaded scaled image without compression: {path}, size: {scaled_size} bytes")
				else:
					# If already under the size limit, no scaling or compression needed
					images.append(buffer.getvalue())
					print(f"Loaded image without compression: {path}, size: {initial_size} bytes")
		except Exception as e:
			print(f"Error processing image {path}: {e}")

	# Tell the user the number of images loaded
	print(f"Loaded {len(images)} images.")

	# Set up the API call to BSKY
	post_response = client.send_images(text=post_text, images=images)
	return post_response

# Post the Images
post_response = post_images(post_text, directory)