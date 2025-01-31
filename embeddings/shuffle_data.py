import json
import os
import random

# Initialize a list to store all image URLs
all_image_urls = []

# Loop through all JSON files in the backup_data directory
for filename in os.listdir('backup_data'):
    if filename.endswith('.json'):
        with open(os.path.join('backup_data', filename), 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Extract image_url from each recipe
            for recipe in data:
                if 'details' in recipe and 'image_url' in recipe['details']:
                    all_image_urls.append(recipe['details']['image_url'])

# Shuffle the list of image URLs to ensure randomness
random.shuffle(all_image_urls)

# Create 4 lists, each with 6 random image URLs
list1 = all_image_urls[:6]
list2 = all_image_urls[6:12]
list3 = all_image_urls[12:18]
list4 = all_image_urls[18:24]

# Print the lists
print("List1 =", list1)
print("List2 =", list2)
print("List3 =", list3)
print("List 4 =", list4)