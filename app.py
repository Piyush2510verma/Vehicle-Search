import os
from flask import Flask, request, render_template, url_for
import openpyxl
import re
from fuzzywuzzy import fuzz

app = Flask(__name__)

# Path to the directory where images are stored
REPOSITORY_PATH = os.path.join(app.static_folder, 'vehicle_images_repository')

# Create a dictionary to map car models to their image file paths
car_image_map = {}

# Populate the dictionary with image file paths
if os.path.exists(REPOSITORY_PATH):
    for filename in os.listdir(REPOSITORY_PATH):
        if filename.endswith(".jpg"):
            # Extract model and brand from the filename
            base_name = filename.replace(".jpg", "").replace("_", " ").lower()
            car_image_map[base_name] = filename

def normalize_query(query):
    # Normalize the query by converting to lowercase and removing spaces and special characters
    return re.sub(r'[^a-zA-Z0-9 ]', '', query.lower())

def find_closest_match(query, options):
    # Find the closest match to the query in the list of options
    highest_ratio = 0
    closest_match = None
    for option in options:
        ratio = fuzz.partial_ratio(query, option)
        if ratio > highest_ratio:
            highest_ratio = ratio
            closest_match = option
    return closest_match

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['GET'])
def search_car_image():
    car_model = request.args.get('model')
    if not car_model:
        return render_template('index.html', error="No car model provided")
    
    # Normalize and split the user input
    car_model_words = car_model.lower().split()
    car_model_processed = normalize_query(car_model)
    print(f"Processed car model: {car_model_processed}")  # Debug print

    # Separate brand and model
    brand = car_model_words[0]
    model = " ".join(car_model_words[1:])

    # Attempt to find a matching image using both "Brand + Model" and "Model" formats
    exact_matches = []
    partial_matches = []

    for model_name in car_image_map:
        normalized_model = normalize_query(model_name)
        if car_model_processed == normalized_model:
            exact_matches.append(model_name)
        elif all(word in normalized_model for word in car_model_words):
            partial_matches.append(model_name)

    if exact_matches:
        image_filename = car_image_map[exact_matches[0]]
        image_url = url_for('static', filename=f'vehicle_images_repository/{image_filename}')
        return render_template('index.html', image_url=image_url)
    elif partial_matches:
        image_filename = car_image_map[partial_matches[0]]
        image_url = url_for('static', filename=f'vehicle_images_repository/{image_filename}')
        return render_template('index.html', image_url=image_url)
    else:
        # If no exact or partial matches, try fuzzy matching for both brand and model
        closest_brand = find_closest_match(brand, car_image_map.keys())
        closest_model = find_closest_match(model, car_image_map.keys())
        if closest_model and closest_brand:
            closest_match = f"{closest_brand} {closest_model}"
            image_filename = car_image_map[closest_match]
            image_url = url_for('static', filename=f'vehicle_images_repository/{image_filename}')
            return render_template('index.html', image_url=image_url)
    
    return render_template('index.html', error="Car model not found in the database")

if __name__ == '__main__':
    app.run(debug=True)
