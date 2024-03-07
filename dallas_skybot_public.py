import os
import time
import tweepy
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from PIL import Image, ImageEnhance, ImageFont, ImageDraw
from wordsegment import load, segment

# credentials to access Twitter API
API_KEY='your_key_here'
API_KEY_SECRET='your_secret_key_here'

BEARER_TOKEN='your_bearer_token_here'

ACCESS_TOKEN='your_access_token_here'
ACCESS_TOKEN_SECRET='your_secret_access_token_here'

# Set up tweepy
client = tweepy.Client(consumer_key = API_KEY,
                       consumer_secret = API_KEY_SECRET,
                       access_token = ACCESS_TOKEN,
                       access_token_secret = ACCESS_TOKEN_SECRET)

auth = tweepy.OAuth1UserHandler(API_KEY, API_KEY_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
api = tweepy.API(auth)

# URL of the livestream video
LIVESTREAM_URL = 'https://www.earthcam.com/clients/reuniontower/embed.php?type=h264&vid=7524.flv&w=auto&company=ReunionTower&timezone=America/Chicago&metar=KDAL&ecn=0&requested_version=current'

# Function to get a screenshot from the livestream video
def get_screenshot(url):
    # Specify the path to the Chrome WebDriver executable
    chromedriver_path = "/usr/local/bin/chromedriver"  # Replace with the path to your chromedriver executable

    # Configure the Chrome WebDriver
    options = ChromeOptions()
    options.add_argument("--headless")  # Run Chrome in headless mode (no UI)
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1920,1080")  # Set window size to 1920x1080
    service = ChromeService(executable_path=chromedriver_path)

    # Create a new Chrome WebDriver instance
    driver = webdriver.Chrome(service=service, options=options)

    try:
        # Open the desired EarthCam stream URL
        driver.get(url)

        # Wait for the page to load and video to start streaming (you may need to adjust the wait time)
        time.sleep(10)  # Adjust this wait time as needed

        # Take a screenshot of the video feed
        screenshot_path = "screenshot.png"  # Specify the path to save the screenshot
        driver.save_screenshot(screenshot_path)

        # Close the browser
        driver.quit()

        return screenshot_path
    except Exception as e:
        print("Error capturing screenshot using web automation:", e)
        driver.quit()
        return None

def crop_screenshot(image_path):
    # Open the saved screenshot image with Pillow
    image = Image.open(image_path)

    # Get image dimensions
    width, height = image.size

    # Crop the top 35 and bottom 40 rows of pixels
    cropped_image = image.crop((0, 35, width, height - 40))

    # Save the cropped image
    cropped_image_path = "cropped_screenshot.png"
    cropped_image.save(cropped_image_path)

    return cropped_image_path

def enhance_image(image, brightness_factor=1.15, contrast_factor=1.1, saturation_factor=1.15):
    # Apply brightness enhancement
    enhancer_brightness = ImageEnhance.Brightness(image)
    brightened_image = enhancer_brightness.enhance(brightness_factor)

    # Apply contrast enhancement
    enhancer_contrast = ImageEnhance.Contrast(brightened_image)
    contrast_enhanced_image = enhancer_contrast.enhance(contrast_factor)

    # Apply saturation enhancement
    enhancer_saturation = ImageEnhance.Color(contrast_enhanced_image)
    final_enhanced_image = enhancer_saturation.enhance(saturation_factor)

    return final_enhanced_image

def hex_to_rgb(hex_code):
    hex_code = hex_code.lstrip('#')
    return tuple(int(hex_code[i:i + 2], 16) for i in (0, 2, 4))

# Function to load Pantone colors from the JSON file
def load_pantone_colors(file_path):
    with open(file_path) as file:
        pantone_colors = json.load(file)
    return pantone_colors

# Function to find the closest Pantone color name
def closest_pantone_color(hex_code, pantone_colors):
    target_rgb = hex_to_rgb(hex_code)
    min_distance = float('inf')
    closest_pantone_color = None

    for color_name, color_hex in pantone_colors.items():
        rgb = hex_to_rgb(color_hex)
        distance = sum((x - y) ** 2 for x, y in zip(target_rgb, rgb))
        if distance < min_distance:
            min_distance = distance
            closest_pantone_color = color_name

    return closest_pantone_color

def split_color_name(color_name):
    # Load Pantone colors from the JSON file
    with open("pantone_colors.json") as file:
        pantone_colors = json.load(file)

    # Check if the color name exists in the JSON file
    if color_name in pantone_colors:
        return pantone_colors[color_name].capitalize()

    # If the color name is not in the JSON file, remove any leading/trailing whitespaces and return
    return color_name.strip().title()

def get_average_color(image):
    # Get the top 540 rows of pixels
    top_rows = image.crop((0, 0, image.width, 540))

    # Calculate the average color of the top rows
    average_color = tuple(int(sum(x) / len(x)) for x in zip(*top_rows.getdata()))

    # Convert the average color to its hex representation
    average_color_hex = f'#{average_color[0]:02x}{average_color[1]:02x}{average_color[2]:02x}'

    # Load Pantone colors from the JSON file
    pantone_colors = load_pantone_colors("pantone_colors.json")

    # Get the closest Pantone color name
    closest_pantone_color_name = closest_pantone_color(average_color_hex, pantone_colors)
    closest_pantone_color_name = split_color_name(closest_pantone_color_name.replace("-", " "))

    # Create an image with the average color
    average_color_image = Image.new('RGB', (860, 980), average_color)
    average_color_image_path = "average_color.png"
    average_color_image.save(average_color_image_path)

    # Return the hex value and color name
    return average_color_hex, closest_pantone_color_name

def add_text_overlay(image, average_color_hex, pantone_color_name, leading = 20):
    draw = ImageDraw.Draw(image)

    # Set the font and font size for the text overlay
    font_path = "Helvetica-Bold.ttf"  # Replace with the path to your font file
    font_size = 84
    font = ImageFont.truetype(font_path, font_size)

    # Set the position for the text overlay
    text_position = (40, image.height - 200)

    # Set the color for the text overlay (black in this case)
    text_color = (255, 255, 255)

    # Set the tracking for the text overlay (-50)
    tracking = 50

    # Create the text to be displayed
    text = f" {average_color_hex}\n {pantone_color_name}"

    # Split the text into lines
    lines = text.split("\n")

    # Calculate the height of each line based on font size and leading
    line_height = font_size + leading

    # Calculate the initial Y-coordinate for the first line
    current_y = text_position[1]

    # Add the text overlay to the image with custom leading
    for line in lines:
        draw.text((text_position[0], current_y), line, fill=text_color, font=font, spacing=tracking)
        current_y += line_height

    return image

def tweet_images(enhanced_image_path, average_color_with_overlay_path):
    try:
        # Upload the enhanced image as media and get media id
        enhanced_response = api.media_upload(enhanced_image_path)
        print(enhanced_response)
        enhanced_media_id = enhanced_response.media_id_string

        # Upload the average color image as media and get media id
        average_color_response = api.media_upload(average_color_with_overlay_path)
        print(average_color_response)
        average_color_media_id = average_color_response.media_id_string        

        # Tweet the image with the uploaded media ID
        tweet_response = client.create_tweet(media_ids= [enhanced_media_id, average_color_media_id])
        print("Images tweeted successfully!")
    except Exception as e:
        print("Error tweeting image:", e)

def main():
        try:
            # Step 1: Get a screenshot from the livestream video
            screenshot_path = get_screenshot(LIVESTREAM_URL)
            if screenshot_path:
                # Step 2: Crop the screenshot
                cropped_screenshot_path = crop_screenshot(screenshot_path)

                # Step 3: Enhance the cropped screenshot
                cropped_screenshot = Image.open(cropped_screenshot_path)
                enhanced_screenshot = enhance_image(cropped_screenshot)
                # Save the enhanced screenshot
                enhanced_screenshot_path = "enhanced_screenshot.png"
                enhanced_screenshot.save(enhanced_screenshot_path)

                # Step 4: Get the average color of the top rows
                average_color_hex, color_name = get_average_color(enhanced_screenshot)

                # Step 5: Load Pantone colors from the JSON file
                pantone_colors = load_pantone_colors("pantone_colors.json")
                
                # Step 6: Get the closest Pantone color name (split if necessary)
                closest_pantone_color_name = closest_pantone_color(average_color_hex, pantone_colors)
                closest_pantone_color_name = split_color_name(closest_pantone_color_name.replace("-", " "))

                # Step 7: Display the results
                print("Average color hex value:", average_color_hex)
                print("Closest Pantone color name:", closest_pantone_color_name)

                # Step 8: Open the "average_color.png" image and add the text overlay
                average_color_image = Image.open("average_color.png")
                image_with_overlay = add_text_overlay(
                    average_color_image, average_color_hex, closest_pantone_color_name, leading=-12
                )
                # Save the image with the text overlay
                image_with_overlay.save("average_color_with_overlay.png")
                average_color_image_path = "average_color_with_overlay.png"
                
                # Step 9: Tweet the enhanced screenshot and average color
                tweet_images(enhanced_screenshot_path, average_color_image_path)

                # Step 10: Delete the local screenshot and cropped screenshot files
                os.remove(screenshot_path)
                os.remove(cropped_screenshot_path)
                os.remove(enhanced_screenshot_path)
                os.remove("average_color.png")
                os.remove("average_color_with_overlay.png")
            else:
                print("Skipping screenshot due to an error.")
        except Exception as e:
            print("Error:", e)

if __name__ == "__main__":
    main()