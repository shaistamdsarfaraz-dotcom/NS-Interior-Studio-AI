import os
import time
import random
import sqlite3
import smtplib
import cv2
import numpy as np
import colorsys
import json
import uuid
import requests
import threading
import queue
from collections import Counter
from werkzeug.utils import secure_filename
from urllib import request as urlrequest
from urllib.error import HTTPError
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
load_dotenv()
AI_ANALYSIS_PROVIDER = "gemini"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
STABILITY_API_KEY = os.getenv("STABILITY_API_KEY")
IMAGE_PROVIDER = "stability"

print("Analysis provider: gemini")
print("Gemini key loaded:", bool(GEMINI_API_KEY))
print("Stability key loaded:", bool(STABILITY_API_KEY))
print("Image provider: stability (Stability AI only)")

email_address = os.getenv("EMAIL_ADDRESS")
email_password = os.getenv("EMAIL_APP_PASSWORD")

app = Flask(__name__)
app.secret_key = os.getenv(
    "FLASK_SECRET_KEY",
    "temporary-development-secret"
)

UPLOAD_FOLDER = 'static/uploads'
GENERATED_FOLDER = 'static/generated'
YOLO_MODEL_CACHE = None

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_ROOMS = ["Living Room", "Bedroom", "Kitchen", "Bathroom"]
ALLOWED_STYLES = ["Modern", "Minimalist", "Scandinavian", "Luxury"]
ALLOWED_RENOVATION_SCOPES = [
    "entire_room", "furniture_only", "colours_only",
    "lighting_only", "decor_only"
]
RENOVATION_SCOPE_LABELS = {
    "entire_room": "Entire room",
    "furniture_only": "Furniture only",
    "colours_only": "Colours only",
    "lighting_only": "Lighting only",
    "decor_only": "Decor only",
}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024   # 10 MB upload limit
app.config['GENERATED_FOLDER'] = GENERATED_FOLDER


def run_with_timeout(function, timeout_seconds, label):
    """Run a provider call without allowing it to freeze the Flask upload route."""
    result_queue = queue.Queue(maxsize=1)

    def worker():
        try:
            result_queue.put((True, function()))
        except Exception as error:
            result_queue.put((False, error))

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    thread.join(timeout_seconds)

    if thread.is_alive():
        print(f"--> {label} timed out after {timeout_seconds} seconds; continuing without it.")
        return None

    try:
        succeeded, value = result_queue.get_nowait()
    except queue.Empty:
        print(f"--> {label} returned no result; continuing without it.")
        return None

    if not succeeded:
        print(f"--> {label} failed inside timeout wrapper: {value}")
        return None
    return value

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(GENERATED_FOLDER, exist_ok=True)

# Initialize SQLite Database with Cost Estimator & Shopping Tables
def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Users Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            phone TEXT,
            location TEXT,
            style_preference TEXT,
            avatar TEXT
        )
    ''')

    # Designs History Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS designs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            room_type TEXT,
            image_path TEXT,
            generated_image_path TEXT,
            estimated_cost TEXT,
            date_created TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Migration: add generated_image_path column if it doesn't exist yet
    # (needed because CREATE TABLE IF NOT EXISTS won't add columns to an
    # already-existing table from before this column was introduced)
    cursor.execute("PRAGMA table_info(designs)")
    existing_columns = [col[1] for col in cursor.fetchall()]
    if 'generated_image_path' not in existing_columns:
        cursor.execute('ALTER TABLE designs ADD COLUMN generated_image_path TEXT')
        
    # Feature 6: Renovation Price Catalog Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS item_prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_type TEXT NOT NULL,
            category TEXT NOT NULL,
            item_name TEXT NOT NULL,
            estimated_price REAL NOT NULL,
            shopping_url TEXT NOT NULL
        )
    ''')
    

    # Seed Default Renovation Items & Shopping Links if empty
    cursor.execute('SELECT COUNT(*) FROM item_prices')
    if cursor.fetchone()[0] == 0:
        default_items = [
    # Living Room
    (
        "Living Room",
        "Paint",
        "Premium Interior Wall Paint",
        8500,
        "https://www.asianpaints.com/"
    ),
    (
        "Living Room",
        "Furniture",
        "Modern Accent Chair",
        18000,
        "https://www.urbanladder.com/search?query=accent%20chair"
    ),
    (
        "Living Room",
        "Lighting",
        "Warm LED Floor Lamp",
        7500,
        "https://www.amazon.in/s?k=warm+led+floor+lamp"
    ),
    (
        "Living Room",
        "Decor",
        "Neutral Textured Area Rug",
        12000,
        "https://www.jaipurrugs.com/search?q=area%20rug"
    ),

    # Bedroom
    (
        "Bedroom",
        "Paint",
        "Soft Matte Interior Paint",
        7000,
        "https://www.asianpaints.com/"
    ),
    (
        "Bedroom",
        "Furniture",
        "Solid Wood Nightstand",
        9500,
        "https://www.urbanladder.com/search?query=bedside%20table"
    ),
    (
        "Bedroom",
        "Lighting",
        "Ambient Bedside Table Lamp",
        3500,
        "https://www.amazon.in/s?k=bedside+table+lamp"
    ),
    (
        "Bedroom",
        "Decor",
        "Blackout Curtain Set",
        6000,
        "https://www.pepperfry.com/site_product/search?q=blackout%20curtains"
    ),

    # Kitchen
    (
        "Kitchen",
        "Paint",
        "Moisture Resistant Cabinet Paint",
        6500,
        "https://www.asianpaints.com/"
    ),
    (
        "Kitchen",
        "Lighting",
        "Modern Pendant Ceiling Light",
        5500,
        "https://www.amazon.in/s?k=modern+pendant+light"
    ),
    (
        "Kitchen",
        "Decor",
        "Peel and Stick Backsplash Tiles",
        4500,
        "https://www.amazon.in/s?k=peel+and+stick+backsplash+tiles"
    ),

    # Bathroom
    (
        "Bathroom",
        "Paint",
        "Anti-Mold Bathroom Wall Paint",
        5000,
        "https://www.bergerpaints.com/"
    ),
    (
        "Bathroom",
        "Lighting",
        "LED Vanity Mirror Light",
        6500,
        "https://www.amazon.in/s?k=led+vanity+mirror+light"
    ),
    (
        "Bathroom",
        "Decor",
        "Matte Black Towel Rack Set",
        3500,
        "https://www.pepperfry.com/site_product/search?q=bathroom%20towel%20rack"
    )
    ]
    cursor.executemany('''
            INSERT INTO item_prices (room_type, category, item_name, estimated_price, shopping_url)
            VALUES (?, ?, ?, ?, ?)
        ''', default_items)

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS budgets (
            user_id INTEGER PRIMARY KEY,
            data TEXT NOT NULL,
            updated TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    conn.commit()
    conn.close()

init_db()


# Feature 4: Color Analysis Helpers
def get_dominant_colors(image_path, color_count=12):
    """Extract 8-12 meaningful colors from the complete uploaded image."""
    img = cv2.imread(image_path)

    if img is None:
        return [{
            "name": "Unknown",
            "hex": "#CCCCCC",
            "rgb": "rgb(204, 204, 204)",
            "percentage": 100.0,
            "category": "unknown",
            "location": "unknown"
        }]

    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = cv2.resize(img, (180, 180), interpolation=cv2.INTER_AREA)
    pixels = img.reshape((-1, 3)).astype(np.float32)

    color_count = max(4, min(int(color_count), 16))
    criteria = (
        cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER,
        30,
        0.5
    )

    _, labels, centers = cv2.kmeans(
        pixels,
        color_count,
        None,
        criteria,
        5,
        cv2.KMEANS_PP_CENTERS
    )

    labels = labels.flatten()
    counts = np.bincount(labels, minlength=color_count)
    total_pixels = len(labels)
    colors = []

    for index, count in enumerate(counts):
        if count == 0:
            continue

        r, g, b = centers[index].astype(int)
        r = max(0, min(255, int(r)))
        g = max(0, min(255, int(g)))
        b = max(0, min(255, int(b)))
        percentage = round((count / total_pixels) * 100, 2)

        # Ignore tiny compression/noise colors.
        if percentage < 1.0:
            continue

        colors.append({
            "name": get_color_name(r, g, b),
            "hex": f"#{r:02X}{g:02X}{b:02X}",
            "rgb": f"rgb({r}, {g}, {b})",
            "percentage": percentage,
            "category": classify_color_area(r, g, b),
            "location": "whole image (computer-vision estimate)"
        })

    colors.sort(key=lambda item: item["percentage"], reverse=True)
    return colors


def get_dominant_color(image_path):
    """Backward-compatible helper returning the first detected RGB color."""
    colors = get_dominant_colors(image_path)
    if not colors:
        return 204, 204, 204

    values = colors[0]["rgb"].replace("rgb(", "").replace(")", "").split(",")
    return tuple(int(value.strip()) for value in values[:3])

def get_color_name(r, g, b):
    """
    Gives a readable name to a detected RGB color.
    """
    h, l, s = colorsys.rgb_to_hls(
        r / 255.0,
        g / 255.0,
        b / 255.0
    )

    if l < 0.12:
        return "Deep Black"

    if l > 0.94 and s < 0.15:
        return "Pure White"

    if s < 0.12:
        if l < 0.35:
            return "Charcoal Gray"
        elif l < 0.65:
            return "Medium Gray"
        elif l < 0.85:
            return "Light Gray"
        return "Warm White"

    if h < 0.04 or h > 0.95:
        return "Red / Coral"

    if h < 0.10:
        return "Orange / Terracotta"

    if h < 0.17:
        return "Golden Yellow"

    if h < 0.28:
        return "Olive / Lime"

    if h < 0.45:
        return "Green"

    if h < 0.58:
        return "Teal / Cyan"

    if h < 0.72:
        return "Blue"

    if h < 0.86:
        return "Purple"

    return "Pink / Magenta"


def classify_color_area(r, g, b):
    """
    Gives a general category for the color.
    The AI will provide more accurate locations.
    """
    h, l, s = colorsys.rgb_to_hls(
        r / 255.0,
        g / 255.0,
        b / 255.0
    )

    if l > 0.78:
        return "walls / ceiling / bright surfaces"

    if l < 0.22:
        return "shadows / dark furniture / accents"

    if 0.05 < h < 0.15:
        return "wood / warm materials"

    if 0.42 < h < 0.75:
        return "plants / blue accents / cool materials"

    return "furniture / decor / surfaces"


def rgb_string_to_hex(rgb_str):
    """Converts 'rgb(r, g, b)' -> '#RRGGBB' for display."""
    nums = rgb_str.replace("rgb(", "").replace(")", "").split(",")
    r, g, b = [int(n.strip()) for n in nums]
    return f"#{r:02X}{g:02X}{b:02X}"


def describe_wall_color(r, g, b):
    """Simple heuristic name + warmth tag for the detected wall color."""
    h, l, s = colorsys.rgb_to_hls(r / 255.0, g / 255.0, b / 255.0)
    if s < 0.12:
        warmth = "Warm" if r >= b else "Cool"
        name = f"{warmth} Gray" if l < 0.85 else f"{warmth} White"
        tag = "Neutral"
    else:
        warmth = "Warm" if (h < 0.17 or h > 0.92) else ("Cool" if 0.45 < h < 0.75 else "Balanced")
        name = f"{warmth} Tone"
        tag = warmth
    return name, tag


def get_lighting_level(image_path):
    """Buckets ambient lighting quality from mean image brightness (0-255 grayscale)."""
    img = cv2.imread(image_path)
    if img is None:
        return "Unknown"
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    mean_brightness = np.mean(gray)
    if mean_brightness < 80:
        return "Low Light"
    elif mean_brightness < 130:
        return "Moderate Light"
    elif mean_brightness < 180:
        return "Natural Light (Good)"
    else:
        return "Bright"


def estimate_room_size(image_path):
    """Rough SIZE CATEGORY estimate based on visible clutter/edge density -- not a real
    measurement, since a single 2D photo has no reference object or depth data."""
    img = cv2.imread(image_path)
    if img is None:
        return "Unknown"
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    edge_density = np.sum(edges > 0) / edges.size
    if edge_density < 0.05:
        return "Large (approx. estimate)"
    elif edge_density < 0.12:
        return "Medium (approx. estimate)"
    else:
        return "Small (approx. estimate)"


def detect_objects_with_yolo(image_path):
    """Detect common room objects locally with YOLO when Ultralytics is installed.

    YOLO is optional so the application still works with OpenCV-only analysis.
    The model is loaded lazily to avoid slowing down Flask startup.
    """
    global YOLO_MODEL_CACHE

    try:
        # Optional dependency: the app gracefully falls back when YOLO is not installed.
        from ultralytics import YOLO  # type: ignore[import-not-found]
    except ImportError:
        print("YOLO unavailable; install ultralytics for local object detection.")
        return []

    try:
        model_name = os.getenv("YOLO_MODEL", "yolo11n.pt")
        if YOLO_MODEL_CACHE is None:
            YOLO_MODEL_CACHE = YOLO(model_name)
        model = YOLO_MODEL_CACHE
        results = model.predict(source=image_path, conf=0.25, verbose=False)
        if not results:
            return []

        result = results[0]
        names = result.names or {}
        image = cv2.imread(image_path)
        height, width = image.shape[:2] if image is not None else (1, 1)
        objects = []

        for box in result.boxes:
            class_id = int(box.cls[0])
            confidence = float(box.conf[0])
            label = str(names.get(class_id, "object"))
            x1, y1, x2, y2 = [float(value) for value in box.xyxy[0].tolist()]
            center_x = ((x1 + x2) / 2) / max(width, 1)
            center_y = ((y1 + y2) / 2) / max(height, 1)

            horizontal = "left" if center_x < 0.34 else "right" if center_x > 0.66 else "center"
            vertical = "upper" if center_y < 0.34 else "lower" if center_y > 0.66 else "middle"

            objects.append({
                "name": label.replace("_", " ").title(),
                "category": "detected room object",
                "location": f"{vertical} {horizontal} of the image",
                "condition": "visible in uploaded image",
                "confidence": round(confidence, 3)
            })

        return objects[:30]
    except Exception as error:
        print(f"YOLO object detection unavailable: {error}")
        return []


def build_local_vision_context(image_path):
    """Create the low-cost local vision context used by Gemini and the fallback."""
    colors = get_dominant_colors(image_path, color_count=12)
    lighting = get_lighting_level(image_path)
    room_size = estimate_room_size(image_path)
    objects = detect_objects_with_yolo(image_path)

    if colors:
        first = colors[0]
        rgb_values = first.get("rgb", "rgb(204, 204, 204)")
        values = rgb_values.replace("rgb(", "").replace(")", "").split(",")
        r, g, b = [int(value.strip()) for value in values[:3]]
        wall_name, wall_mood = describe_wall_color(r, g, b)
        wall_colour = {
            "name": wall_name,
            "mood": wall_mood,
            "hex": first.get("hex", "#CCCCCC"),
            "rgb": rgb_values
        }
    else:
        wall_colour = {
            "name": "Unknown tone",
            "mood": "Neutral",
            "hex": "#CCCCCC",
            "rgb": "rgb(204, 204, 204)"
        }

    return {
        "colorPalette": colors,
        "lighting": lighting,
        "roomSize": room_size,
        "detectedObjects": objects,
        "wallColour": wall_colour
    }


def get_recommended_colors(r, g, b):
    """Generates complementary and analogous color recommendations using color theory."""
    h, l, s = colorsys.rgb_to_hls(r / 255.0, g / 255.0, b / 255.0)

    if s < 0.12:
        h = 0.08 if r >= b else 0.58

    accent_s = max(s, 0.45)
    accent_l = min(max(l, 0.35), 0.55)

    def make_color(hue_shift):
        new_h = (h + hue_shift) % 1.0
        cr, cg, cb = [int(c * 255) for c in colorsys.hls_to_rgb(new_h, accent_l, accent_s)]
        return f"rgb({cr}, {cg}, {cb})"

    return {
        "complementary": make_color(0.5),
        "analogous1": make_color(0.083),
        "analogous2": make_color(-0.083)
    }
def build_recommended_palette(color_palette):
    """
    Create a larger recommendation palette from all detected colors.
    This works even when Gemini is temporarily unavailable.
    """

    recommendations = []

    for color in color_palette[:6]:
        if not isinstance(color, dict):
            continue

        hex_value = color.get("hex", "#CCCCCC")
        rgb_value = color.get("rgb", "rgb(204, 204, 204)")
        color_name = color.get("name", "Detected color")
        category = color.get("category", "room surface")

        recommendations.append({
            "name": f"{color_name} Recommendation",
            "hex": hex_value,
            "rgb": rgb_value,
            "reason": (
                f"Matches the detected {category} tone and can be used "
                "for coordinated walls, furniture, textiles, or decor."
            )
        })

    # Guarantee at least six recommendations.
    fallback_colors = [
        {
            "name": "Soft Ivory",
            "hex": "#F4EFE6",
            "rgb": "rgb(244, 239, 230)",
            "reason": "Creates a brighter and calmer base for the room."
        },
        {
            "name": "Sage Green",
            "hex": "#A8B89A",
            "rgb": "rgb(168, 184, 154)",
            "reason": "Adds a natural, relaxing accent without overpowering the room."
        },
        {
            "name": "Dusty Blue",
            "hex": "#789BC4",
            "rgb": "rgb(120, 155, 196)",
            "reason": "Adds a cool balancing accent for warm furniture and flooring."
        },
        {
            "name": "Warm Terracotta",
            "hex": "#C87962",
            "rgb": "rgb(200, 121, 98)",
            "reason": "Adds warmth and depth to cushions, artwork, or accessories."
        },
        {
            "name": "Muted Gold",
            "hex": "#D2B36C",
            "rgb": "rgb(210, 179, 108)",
            "reason": "Works well for lighting, handles, frames, and small decor accents."
        },
        {
            "name": "Charcoal Accent",
            "hex": "#3E3E46",
            "rgb": "rgb(62, 62, 70)",
            "reason": "Adds contrast and definition to furniture or architectural details."
        }
    ]

    existing_hexes = {
        item.get("hex", "").upper()
        for item in recommendations
    }

    for item in fallback_colors:
        if len(recommendations) >= 6:
            break

        if item["hex"].upper() not in existing_hexes:
            recommendations.append(item)

    return recommendations[:6]


# Feature 5: Furniture Layout Rules
LAYOUT_LIBRARY = {
    "Living Room": [
        {"title": "Anchor to a focal point", "tip": "Face main seating toward TV, fireplace, or largest window."},
        {"title": "Keep traffic flow open", "tip": "Leave at least 30 inches (75 cm) of walkway between furniture pieces."},
        {"title": "Float larger sofas", "tip": "Pull sofa away from walls to create conversational zones."},
        {"title": "Balance the room", "tip": "Pair a large sofa with two armchairs or a loveseat to avoid a boxy look."}
    ],
    "Bedroom": [
        {"title": "Center the bed", "tip": "Place bed on wall opposite main door with equal nightstand space."},
        {"title": "Mind swing zones", "tip": "Leave 24-30 inches around bed and wardrobes for full door opening."},
        {"title": "Clear entry path", "tip": "Maintain an unobstructed walking line from doorway to bed."}
    ],
    "Kitchen": [
        {"title": "Respect the work triangle", "tip": "Keep sink, stove, and fridge in a triangle layout."},
        {"title": "Allow counter landing space", "tip": "Leave 12-18 inches of counter space next to fridge and cooktop."}
    ],
    "Bathroom": [
        {"title": "Keep sink area clear", "tip": "Avoid placing tall units that block mirror or sink access."},
        {"title": "Allow door clearance", "tip": "Ensure door swings fully without hitting fixtures."}
    ]
}

def get_layout_suggestions(room_type):
    return LAYOUT_LIBRARY.get((room_type or "").title().strip(), LAYOUT_LIBRARY["Living Room"])


# Feature 6 & 7: Renovation Cost Estimator & Shopping List Generator
SHOPPING_CATALOG = {
    "Living Room": [
        {
            "category": "Lighting",
            "name": "Warm LED Floor Lamp",
            "share": 0.10,
            "links": [
                {
                    "store": "IKEA",
                    "url": "https://www.ikea.com/in/en/search/?q=floor%20lamp"
                },
                {
                    "store": "Amazon India",
                    "url": "https://www.amazon.in/s?k=warm+led+floor+lamp"
                },
                {
                    "store": "Pepperfry",
                    "url": "https://www.pepperfry.com/site_product/search?q=floor%20lamp"
                }
            ]
        },
        {
            "category": "Furniture",
            "name": "Modern Accent Chair",
            "share": 0.22,
            "links": [
                {
                    "store": "IKEA",
                    "url": "https://www.ikea.com/in/en/search/?q=accent%20chair"
                },
                {
                    "store": "Amazon India",
                    "url": "https://www.amazon.in/s?k=modern+accent+chair"
                },
                {
                    "store": "Urban Ladder",
                    "url": "https://www.urbanladder.com/search?query=accent%20chair"
                }
            ]
        },
        {
            "category": "Textiles",
            "name": "Neutral Area Rug",
            "share": 0.18,
            "links": [
                {
                    "store": "IKEA",
                    "url": "https://www.ikea.com/in/en/search/?q=area%20rug"
                },
                {
                    "store": "Amazon India",
                    "url": "https://www.amazon.in/s?k=neutral+area+rug"
                },
                {
                    "store": "Jaipur Rugs",
                    "url": "https://www.jaipurrugs.com/search?q=area%20rug"
                }
            ]
        },
        {
            "category": "Paint",
            "name": "Premium Interior Wall Paint",
            "share": 0.16,
            "links": [
                {
                    "store": "Asian Paints",
                    "url": "https://www.asianpaints.com/"
                },
                {
                    "store": "Amazon India",
                    "url": "https://www.amazon.in/s?k=interior+wall+paint"
                },
                {
                    "store": "Berger Paints",
                    "url": "https://www.bergerpaints.com/"
                }
            ]
        },
        {
            "category": "Decor",
            "name": "Indoor Plant and Planter",
            "share": 0.08,
            "links": [
                {
                    "store": "Ugaoo",
                    "url": "https://www.ugaoo.com/collections/indoor-plants"
                },
                {
                    "store": "Amazon India",
                    "url": "https://www.amazon.in/s?k=indoor+plant+planter"
                },
                {
                    "store": "IKEA",
                    "url": "https://www.ikea.com/in/en/search/?q=plant%20pot"
                }
            ]
        },
        {
            "category": "Decor",
            "name": "Wall Art and Mirror",
            "share": 0.12,
            "links": [
                {
                    "store": "Pepperfry",
                    "url": "https://www.pepperfry.com/site_product/search?q=wall%20art"
                },
                {
                    "store": "Amazon India",
                    "url": "https://www.amazon.in/s?k=wall+art+mirror+decor"
                },
                {
                    "store": "Etsy",
                    "url": "https://www.etsy.com/in-en/search?q=wall%20art"
                }
            ]
        },
        {
            "category": "Storage",
            "name": "Low TV Console or Sideboard",
            "share": 0.14,
            "links": [
                {
                    "store": "IKEA",
                    "url": "https://www.ikea.com/in/en/search/?q=tv%20unit"
                },
                {
                    "store": "Urban Ladder",
                    "url": "https://www.urbanladder.com/search?query=tv%20unit"
                },
                {
                    "store": "Amazon India",
                    "url": "https://www.amazon.in/s?k=modern+tv+unit"
                }
            ]
        }
    ]
}
def get_cost_and_shopping_list(room_type, budget_inr=None ):
    """Return an INR budget plan whose allocations add up exactly to the user's target."""
    normalized_room = (room_type or "Living Room").title().strip()
    catalog = SHOPPING_CATALOG.get(normalized_room, SHOPPING_CATALOG["Living Room"])

    try:
        target = float(budget_inr) if budget_inr not in (None, "") else 0
    except (TypeError, ValueError):
        target = 0

    # If the user entered a budget, use it as the exact planning target.
    if target > 0:
        total = round(target, 2)
        allocations = []
        allocated = 0.0

        for index, item in enumerate(catalog):
            if index == len(catalog) - 1:
                amount = round(total - allocated, 2)
            else:
                amount = round(total * float(item["share"]), 2)
                allocated += amount

            allocations.append({
                "category": item["category"],
                "name": item["name"],
                "price": f"₹{amount:,.2f}",
                "url": item["links"][0]["url"],
                "links": item["links"]
            })

        return {
            "itemized": allocations,
            "total_estimated": f"₹{total:,.2f}",
            "min_range": f"₹{total:,.2f}",
            "max_range": f"₹{total:,.2f}",
            "currency": "INR",
            "budget_target": True
        }, allocations

    # No user budget: show a planning estimate using sensible Indian retail ranges.
    default_total = 0.0
    allocations = []
    default_prices = [8500, 18000, 12000, 9500, 4500, 7500, 14000]

    for index, item in enumerate(catalog):
        amount = default_prices[index % len(default_prices)]
        default_total += amount
        allocations.append({
            "category": item["category"],
            "name": item["name"],
            "price": f"₹{amount:,.2f}",
            "url": item["links"][0]["url"],
            "links": item["links"]
        })

    return {
        "itemized": allocations,
        "total_estimated": f"₹{default_total:,.2f}",
        "min_range": f"₹{default_total * .85:,.2f}",
        "max_range": f"₹{default_total * 1.20:,.2f}",
        "currency": "INR",
        "budget_target": False
    }, allocations


# Feature 8: Before/After AI Image Generation

STYLE_INSTRUCTIONS = {
    "Modern": (
        "Use clean contemporary lines, practical proportions, restrained decoration, "
        "a confident, clearly defined colour scheme, and refined black or brushed-metal accents."
    ),
    "Minimalist": (
        "Use a calm minimal composition with fewer carefully chosen objects, uncluttered "
        "surfaces, simple furniture, concealed storage, and generous visual breathing room."
    ),
    "Scandinavian": (
        "Use light wood, softly coloured walls, pale textiles, functional furniture, cosy layered "
        "textures, daylight, and restrained pastel accents."
    ),
    "Luxury": (
        "Use visibly premium materials, elegant furniture proportions, richer upholstery, "
        "stone or marble accents where appropriate, refined metallic details, layered warm lighting, "
        "symmetry, and sophisticated high-end styling. Do not produce a generic modern room."
    ),
}

SCOPE_INSTRUCTIONS = {
    "entire_room": (
        "Renovate the whole visible room while preserving the believable architectural shell "
        "and camera viewpoint. You may update movable furniture, colours, textiles, decor, layout, "
        "and lighting."
    ),
    "furniture_only": (
        "CHANGE ONLY MOVABLE FURNITURE: sofas, chairs, tables, beds, cabinets, shelves, and "
        "similar freestanding pieces. Keep walls, wall colours, flooring, ceiling, windows, doors, "
        "architecture, curtains, permanent fixtures, lighting fixtures, decor, and camera viewpoint "
        "unchanged. Do not repaint, remodel, or rearrange the architecture."
    ),
    "colours_only": (
        "CHANGE ONLY COLOURS and colour finishes visible in the room, including walls, upholstery, "
        "curtains, rugs, cushions, and small accents. Keep furniture identity, shape, position, "
        "layout, flooring, windows, doors, architecture, lighting fixtures, decor objects, and camera "
        "viewpoint unchanged. Do not replace furniture or add architecture."
    ),
    "lighting_only": (
        "CHANGE ONLY THE LIGHTING EXPERIENCE: brightness, colour temperature, lamp glow, practical "
        "fixtures, and believable light distribution. Keep furniture, colours, decor, layout, walls, "
        "flooring, windows, doors, architecture, and camera viewpoint unchanged."
    ),
    "decor_only": (
        "CHANGE ONLY SMALL DECOR AND SOFT ACCESSORIES such as cushions, artwork, vases, plants, "
        "rugs, throws, and styling objects. Keep furniture, walls, flooring, architecture, layout, "
        "windows, doors, and permanent lighting fixtures unchanged."
    ),
}


def get_scope_instruction(scope):
    return SCOPE_INSTRUCTIONS.get(scope, SCOPE_INSTRUCTIONS["entire_room"])


def get_style_scope_instruction(style, scope):
    """Apply the chosen style only to the requested renovation scope."""
    style = style or "Modern"
    if scope == "furniture_only":
        return (
            f"Apply {style} ONLY to replacement movable furniture. Do not use the style to change "
            "walls, ceiling, flooring, windows, doors, curtains, permanent fixtures, lighting, "
            "or decorative objects."
        )
    if scope == "colours_only":
        return (
            f"Apply the colour expression of {style} ONLY through permitted colour changes. Do not "
            "change furniture design, furniture position, architecture, objects, or lighting."
        )
    if scope == "lighting_only":
        return (
            f"Use {style} only as a subtle reference for the lighting mood. Do not redesign any "
            "furniture, colour, decor, layout, or architecture."
        )
    if scope == "decor_only":
        return (
            f"Apply {style} ONLY to replacement small decor and soft accessories. Do not change "
            "furniture, walls, floor, architecture, layout, or permanent lighting."
        )
    return f"Apply {style} consistently throughout the permitted full-room renovation."


def get_style_exclusions(style, scope):
    if style == "Modern":
        guardrail = (
            "Avoid Scandinavian or Nordic styling: no pale oak, light pine, hygge styling, pastel "
            "wash, boucle-heavy upholstery, woven-rattan emphasis, farmhouse details, or cottage "
            "decoration. Prefer crisp geometric forms, flat-panel finishes, the chosen colour scheme, "
            "controlled contrast, black or brushed-metal accents, and polished contemporary "
            "surfaces."
        )
        return guardrail + (" Apply this only to the selected editable elements." if scope != "entire_room" else "")
    if style == "Scandinavian":
        return "Use light natural wood, soft coloured tones, functional silhouettes, cosy textiles, and restrained pastel accents, without luxury ornament or excessive glossy surfaces."
    return "Do not introduce visual cues from a different named interior style."


def get_scope_palette_instruction(scope, palette_text):
    if scope == "furniture_only":
        return f"Use this palette ONLY on the replacement furniture: {palette_text}."
    if scope == "colours_only":
        return f"Use this palette ONLY for permitted colour changes: {palette_text}."
    if scope == "lighting_only":
        return "Do not apply the design palette to walls, furniture, flooring, or decor. Change only light and shadow."
    if scope == "decor_only":
        return f"Use this palette ONLY on replacement decor and soft accessories: {palette_text}."
    return f"Use this exact recommended palette throughout the permitted renovation: {palette_text}."


def get_scope_layout_instruction(scope, layout_text):
    if scope != "entire_room":
        return "Do not use layout guidance. Keep the existing layout and camera composition unchanged."
    return f"Follow this layout guidance: {layout_text}."


def get_lighting_instruction(lighting_level):
    level = (lighting_level or "Moderate Light").strip()
    if level == "Low Light":
        return (
            "The source room is dim. Use a clear layered lighting plan with warm-white ceiling "
            "lighting, practical floor or table lamps, gentle wall or indirect light, and realistic "
            "2700K-3000K warm light. Brighten the room without blowing out windows."
        )
    if level == "Natural Light (Good)":
        return (
            "Preserve the natural daylight and add subtle 3000K-4000K warm-neutral practical and "
            "accent lighting. Keep exposure balanced and materials readable."
        )
    if level == "Bright":
        return (
            "Keep the room bright but comfortable using balanced daylight, soft ceiling light, and "
            "controlled warm accent lamps. Avoid glare, overexposure, and unnaturally white light."
        )
    return (
        "Use balanced moderate layered lighting: soft ceiling light, practical task lighting, and "
        "gentle accent lighting around 3000K-3500K so the room is clear, comfortable, and realistic."
    )

# Feature 8: Before/After AI Image Generation (Stability AI)

# Rotating colour schemes so every regeneration looks different.
# (scheme name, wall colour, furniture colours, accent colours)
COLOUR_SCHEMES = {
    "Modern": [
        ("Slate Blue & Graphite", "muted slate blue", "graphite grey and crisp white", "brushed brass and matte black"),
        ("Deep Teal & Steel", "deep teal green", "light grey and steel blue", "chrome and warm white"),
        ("Sage & Charcoal", "muted sage green", "charcoal and soft grey", "black metal and walnut"),
        ("Navy & Silver", "dark navy blue", "light cool grey and white", "silver and glass"),
        ("Olive & Stone", "muted olive green", "stone grey and dark brown", "antique brass"),
        ("Cool Grey & Rust", "cool mid-grey", "deep rust orange and white", "black and copper"),
    ],
    "Minimalist": [
        ("Misty Blue", "soft misty blue", "white and light grey", "pale oak and matte white"),
        ("Pale Mint", "pale mint green", "white and soft charcoal", "light wood and nickel"),
        ("Cool Grey", "light cool grey", "white and slate", "matte black accents"),
        ("Lavender Grey", "pale lavender grey", "white and pale grey", "light ash wood"),
        ("Powder Blue", "light powder blue", "white and graphite", "brushed steel"),
        ("Soft Green-Grey", "muted green-grey", "white and dark grey", "natural oak"),
    ],
    "Scandinavian": [
        ("Duck-Egg & Birch", "pale duck-egg blue", "white and light grey with birch wood", "soft grey textiles and a touch of mustard"),
        ("Sage & Pine", "soft sage green", "white and pale grey with pine wood", "muted blue textiles"),
        ("Dusty Blue & Oak", "pale dusty blue", "light grey and white with light oak", "dusty pink and grey throws"),
        ("Pistachio & Ash", "pale pistachio green", "white and soft grey with ash wood", "charcoal accents"),
        ("Blue-Grey & Linen", "light grey-blue", "white and mid-grey with light wood", "forest green plants and textiles"),
        ("Lilac-Grey & Birch", "soft lilac grey", "white and light grey with birch", "sage green accents"),
    ],
    "Luxury": [
        ("Emerald & Gold", "deep emerald green", "dove grey and deep green velvet", "polished gold and marble"),
        ("Royal Navy & Brass", "rich navy blue", "charcoal and sapphire velvet", "polished brass and white marble"),
        ("Burgundy & Bronze", "deep burgundy wine red", "charcoal and plum velvet", "bronze and dark marble"),
        ("Aubergine & Silver", "regal aubergine plum", "silver grey and deep purple velvet", "polished nickel and crystal"),
        ("Dark Teal & Gold", "dark teal", "slate and teal velvet", "gold and black marble"),
        ("Graphite & Champagne", "glossy graphite charcoal", "pearl grey and black leather", "champagne metal and veined marble"),
    ],
}

_LAST_SCHEME = {}

def pick_colour_scheme(style):
    """Pick a random scheme, never the same one twice in a row for a style."""
    pool = COLOUR_SCHEMES.get(style, COLOUR_SCHEMES["Modern"])
    options = [s for s in pool if s[0] != _LAST_SCHEME.get(style)] or pool
    scheme = random.choice(options)
    _LAST_SCHEME[style] = scheme[0]
    return scheme


def generate_stability_redesign(
    image_path,
    room_type,
    design_style=None,
    color_palette=None,
    layout_suggestions=None,
    detected_objects=None,
    lighting_level=None,
    renovation_scope="entire_room"
):
    """Generate a style- and scope-controlled image-to-image redesign with Stability AI."""
    if not STABILITY_API_KEY:
        print("--> STABILITY_API_KEY is missing.")
        return None

    design_style = design_style or "Modern"
    color_palette = color_palette or []
    layout_suggestions = layout_suggestions or []
    detected_objects = detected_objects or []
    lighting_level = lighting_level or "Moderate Light"
    renovation_scope = renovation_scope if renovation_scope in ALLOWED_RENOVATION_SCOPES else "entire_room"
    style_instruction = STYLE_INSTRUCTIONS.get(design_style, STYLE_INSTRUCTIONS["Modern"])
    scope_instruction = get_scope_instruction(renovation_scope)
    style_scope_instruction = get_style_scope_instruction(design_style, renovation_scope)
    style_exclusions = get_style_exclusions(design_style, renovation_scope)
    lighting_instruction = get_lighting_instruction(lighting_level)

    scheme_name, scheme_walls, scheme_furniture, scheme_accents = pick_colour_scheme(design_style)
    print(f"--> Colour scheme chosen for this redesign: {scheme_name}")

    palette_text = (
        f"walls in {scheme_walls}; furniture in {scheme_furniture}; "
        f"accents in {scheme_accents}"
    )

    if renovation_scope in ("entire_room", "colours_only"):
        colour_directive = f"""
MANDATORY COLOUR SCHEME: "{scheme_name}"
- Wall colour: {scheme_walls}. Walls must be ONE flat, even, solid colour with no gradient,
  no colour wash, no vignette and no two-tone fade.
- Main furniture and upholstery: {scheme_furniture}.
- Accents and metals: {scheme_accents}.
- The walls must NOT be cream, beige, ivory, peach, off-white, sand, tan or any pale yellowish
  tone. If the original room is cream or beige, change it completely to the wall colour above.
- The colour change must be clearly visible compared with the original photo.
"""
    else:
        colour_directive = ""

    layout_text = "; ".join(
        f"{item.get('title', '')}: {item.get('description', item.get('tip', ''))}"
        for item in layout_suggestions[:5]
        if isinstance(item, dict)
    ) or "rearrange furniture for clear circulation and a strong focal point"

    object_text = ", ".join(
        f"{item.get('name', 'object')} in {item.get('location', 'the room')}"
        for item in detected_objects[:16]
        if isinstance(item, dict)
    ) or "the visible furniture and room elements"

    prompt = f"""
Create a premium, photorealistic interior-design renovation of the uploaded {room_type} photo.
This must look like a professionally photographed, fully resolved interior project—not a generic
AI room, catalogue render, concept sketch, or simple colour filter.

PRIMARY DESIGN DECISION
The user's selected style is EXACTLY {design_style}. Style direction: {style_instruction}
Style scope: {style_scope_instruction}
Style guardrail: {style_exclusions}
Do not blend this with Scandinavian, rustic, farmhouse, bohemian, industrial, or another named style
unless that style was selected. Make the chosen style obvious through furniture silhouette, materials,
proportions, colour balance, lighting, and accessories.

RENOVATION SCOPE
The selected renovation scope is {renovation_scope}. Follow it exactly:
{scope_instruction}

{get_scope_palette_instruction(renovation_scope, palette_text)}
{get_scope_layout_instruction(renovation_scope, layout_text)}
The visible room objects include: {object_text}.

{colour_directive}
WALLS AND MATERIALS — IMPORTANT
Do not automatically apply the same wall treatment used in previous generations. Choose a deliberate,
style-appropriate wall finish for this specific room and composition. Prefer smooth, clean, realistic
paint on most walls unless a feature treatment is clearly justified. If a feature wall is appropriate,
use ONE controlled treatment such as refined wood slats, subtle stone, elegant wall panelling, or a
single tasteful accent colour—not full-room repetitive texture. Keep wall planes straight and natural.
Do not cover every wall with rough plaster, stucco, microcement, noisy grain, random mottling, fake
brush marks, or a repeated procedural texture. Materials must have believable scale, seams, edges,
thickness, reflections, and contact shadows.

LIGHTING AND PHOTOGRAPHIC QUALITY
The lighting condition is {lighting_level}. {lighting_instruction}
Use a layered lighting plan: realistic daylight direction, soft ceiling illumination, practical lamps,
and subtle accent lighting only where appropriate. Use warm-neutral 2700K–3500K light unless the
selected design clearly requires otherwise. Make the room bright, balanced, and readable without
blown-out windows, green/orange colour casts, harsh hotspots, or dark crushed corners. Show natural
shadows, accurate material response, realistic reflections, and professional interior-photography
exposure. Use a believable wide-angle camera at the original viewpoint with straight vertical lines.

DESIGN QUALITY CHECKLIST
Create a coherent focal point, clear circulation, correctly scaled furniture, balanced negative space,
layered textiles, restrained decor, realistic joinery, and a convincing relationship between floor,
walls, ceiling, windows, furniture, and lighting. Change enough movable elements to make the redesign
visibly meaningful, but keep the room recognisable and architecturally believable.

SOURCE IMAGE AND PROTECTED ELEMENTS
Use the uploaded image as the source of truth. Do not change any protected element outside the selected
scope. Keep protected furniture, colours, objects, architecture, lighting, layout, and camera viewpoint
unchanged. If a selective edit cannot be performed safely, return an almost identical image with only
the permitted elements changed; never redesign protected areas.

FINAL OUTPUT
Preserve believable architecture, windows, doors, proportions, perspective, and camera viewpoint.
Do not add people, text, labels, logos, watermarks, extra windows, extra doors, duplicate furniture,
floating objects, warped geometry, malformed lamps, impossible reflections, or distorted furniture.
Return one sharp, high-resolution, professional interior-design photograph with natural materials,
clean edges, realistic shadows, and a polished editorial finish.
"""[:12000]

    try:
        original = cv2.imread(image_path)
        if original is None:
            print("--> Could not read the uploaded image.")
            return None

        height, width = original.shape[:2]
        ratio = width / max(height, 1)
        if ratio >= 1.45:
            target = (1344, 768)
        elif ratio >= 1.20:
            target = (1152, 896)
        elif ratio >= 0.95:
            target = (1024, 1024)
        elif ratio >= 0.74:
            target = (896, 1152)
        else:
            target = (768, 1344)

        resized = cv2.resize(original, target, interpolation=cv2.INTER_AREA)
        success, encoded = cv2.imencode(
            ".jpg", resized, [int(cv2.IMWRITE_JPEG_QUALITY), 94]
        )
        if not success:
            print("--> Could not prepare the uploaded image for Stability.")
            return None

        response = requests.post(
            "https://api.stability.ai/v2beta/stable-image/generate/sd3",
            headers={
                "Authorization": f"Bearer {STABILITY_API_KEY}",
                "Accept": "image/*"
            },
            files={
                "image": ("room.jpg", encoded.tobytes(), "image/jpeg")
            },
            data={
                "mode": "image-to-image",
                "prompt": prompt,
                "negative_prompt": (
                    "cream walls, beige walls, peach walls, ivory walls, off-white walls, sand walls, yellowish tint, "
                    "gradient wall wash, colour gradient on walls, vignette, "
                    "generic AI room, catalogue render, concept sketch, low-detail 3D render, "
                    "repetitive wall texture, rough stucco, fake plaster, microcement everywhere, "
                    "procedural noise, mottled walls, random brush marks, wall texture covering every "
                    "surface, flat beige room, Scandinavian styling when not selected, rustic styling "
                    "when not selected, near-identical copy, unchanged design, original colour scheme, "
                    "blurry, low resolution, underexposed, overexposed windows, orange or green colour cast, "
                    "harsh hotspots, crushed shadows, distorted furniture, warped walls, bad perspective, "
                    "duplicate objects, floating objects, impossible reflections, people, text, logo, watermark"
                ),
                "strength": "0.72",
                "model": "sd3.5-medium",
                "output_format": "png",
                "cfg_scale": "8"
            },
            timeout=(10, 60)
        )

        if response.status_code != 200 or not response.content:
            print(
                "--> Stability image generation failed:",
                response.status_code,
                response.text[:2000]
            )
            return None

        filename = f"redesign_{uuid.uuid4().hex}.png"
        output_path = os.path.join(app.config["GENERATED_FOLDER"], filename)
        with open(output_path, "wb") as output_file:
            output_file.write(response.content)

        print(f"--> Stability redesign saved: {filename}")
        return filename

    except requests.RequestException as error:
        print(f"--> Stability network error: {error}")
        return None
    except Exception as error:
        print(f"--> Stability redesign error: {error}")
        return None

# Feature: Real AI Room Analysis (Google Gemini Vision)
ROOM_ANALYSIS_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "roomType": {"type": "STRING"},
        "roomSize": {"type": "STRING"},
        "lighting": {"type": "STRING"},
        "architecturalStyle": {"type": "STRING"},

        "wallColour": {
            "type": "OBJECT",
            "properties": {
                "name": {"type": "STRING"},
                "mood": {"type": "STRING"},
                "hex": {"type": "STRING"},
                "rgb": {"type": "STRING"}
            },
            "required": ["name", "mood", "hex", "rgb"]
        },

        "colorPalette": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "name": {"type": "STRING"},
                    "hex": {"type": "STRING"},
                    "rgb": {"type": "STRING"},
                    "percentage": {"type": "NUMBER"},
                    "category": {"type": "STRING"},
                    "location": {"type": "STRING"}
                },
                "required": [
                    "name",
                    "hex",
                    "rgb",
                    "percentage",
                    "category",
                    "location"
                ]
            }
        },

        "recommendedColors": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "name": {"type": "STRING"},
                    "hex": {"type": "STRING"},
                    "rgb": {"type": "STRING"},
                    "reason": {"type": "STRING"}
                },
                "required": ["name", "hex", "rgb", "reason"]
            }
        },

        "detectedObjects": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "name": {"type": "STRING"},
                    "category": {"type": "STRING"},
                    "location": {"type": "STRING"},
                    "condition": {"type": "STRING"},
                    "confidence": {"type": "NUMBER"}
                },
                "required": [
                    "name",
                    "category",
                    "location",
                    "condition",
                    "confidence"
                ]
            }
        },

        "materials": {
            "type": "ARRAY",
            "items": {"type": "STRING"}
        },

        "architecturalElements": {
            "type": "ARRAY",
            "items": {"type": "STRING"}
        },

        "designObservations": {
            "type": "ARRAY",
            "items": {"type": "STRING"}
        },

        "layouts": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "title": {"type": "STRING"},
                    "description": {"type": "STRING"}
                },
                "required": ["title", "description"]
            }
        }
    },
    "required": [
        "roomType",
        "roomSize",
        "lighting",
        "architecturalStyle",
        "wallColour",
        "colorPalette",
        "recommendedColors",
        "detectedObjects",
        "materials",
        "architecturalElements",
        "designObservations",
        "layouts"
    ]
}

# --- Structured Gemini response models ---
class ColorItem(BaseModel):
    name: str
    hex: str
    rgb: str
    percentage: float
    category: str
    location: str


class RecommendedColorItem(BaseModel):
    name: str
    hex: str
    rgb: str
    reason: str


class WallColour(BaseModel):
    name: str
    mood: str
    hex: str
    rgb: str


class DetectedObject(BaseModel):
    name: str
    category: str
    location: str
    condition: str
    confidence: float


class LayoutSuggestion(BaseModel):
    title: str
    description: str


class RoomAnalysisResponse(BaseModel):
    roomType: str
    roomSize: str
    lighting: str
    architecturalStyle: str
    wallColour: WallColour
    colorPalette: list[ColorItem]
    recommendedColors: list[RecommendedColorItem]
    detectedObjects: list[DetectedObject]
    materials: list[str]
    architecturalElements: list[str]
    designObservations: list[str]
    layouts: list[LayoutSuggestion]


# --- Gemini SDK Analysis Function ---
def analyze_room_with_gemini(image_path, room_type_hint, local_vision=None):
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        print("GEMINI_API_KEY is missing")
        return None

    try:
        client = genai.Client(api_key=api_key)

        with open(image_path, "rb") as image_file:
            image_bytes = image_file.read()

        extension = os.path.splitext(image_path)[1].lower()

        mime_type = {
            ".png": "image/png",
            ".webp": "image/webp",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg"
        }.get(extension, "image/jpeg")

        local_vision = local_vision or {}
        local_colors = json.dumps(local_vision.get("colorPalette", []), ensure_ascii=False)
        local_objects = json.dumps(local_vision.get("detectedObjects", []), ensure_ascii=False)
        local_lighting = local_vision.get("lighting", "Unknown")
        local_wall = json.dumps(local_vision.get("wallColour", {}), ensure_ascii=False)

        prompt = f"""
You are an expert interior designer and computer-vision analyst.

Inspect the uploaded room image thoroughly.
The user's selected room type is: {room_type_hint}

Low-cost local vision has already measured this image. Treat these values as the
source of truth for colours, brightness, and YOLO object labels. Use Gemini mainly
for room interpretation, style recommendations, layouts, materials, observations,
and the redesign plan. Do not invent different colours or objects.

OpenCV colour palette: {local_colors}
OpenCV wall-colour estimate: {local_wall}
OpenCV lighting estimate: {local_lighting}
YOLO object labels: {local_objects}
Requirements:
- Identify the room type, approximate size, lighting, and architectural style.
- Detect the dominant wall colour and return accurate HEX and RGB values.
- Return 10-14 meaningful colors visible in the complete image, not generic design colors.
- For each detected color return name, HEX, RGB, percentage, category, and visible location.
- Recommend at least 6 suitable colors for this exact room image. Base the recommendations on
  the detected wall, floor, furniture, lighting, and accent colors. Include the name, HEX, RGB,
  and a short reason for each recommendation.
- Identify every visible item: furniture, decor, fixtures, appliances, windows, doors, plants,
  artwork, rugs, cushions, curtains, tables, chairs, sofas, cabinets, shelves, lamps, books,
  vases, mirrors, and architectural elements.
- Return 5-8 strong layout recommendations for this exact room. Each layout must include a
  short title and a practical description mentioning placement, circulation, focal point,
  balance, or lighting.
- List visible materials and architectural elements.
- Provide 5-8 specific observations about scale, circulation, lighting, texture, color balance,
  storage, and composition.
- Do not return generic filler. Describe only visible or strongly supported details.

Return a detailed JSON analysis.

Analyze all visible details, including:

1. Room type
2. Approximate room size
3. Lighting quality
4. Architectural style
5. Wall color with HEX and RGB
6. At least 8 meaningful colors from the whole image
7. Furniture
8. Decor
9. Lighting fixtures
10. Windows and doors
11. Plants
12. Artwork
13. Rugs, cushions, curtains, and textiles
14. Tables, chairs, sofas, cabinets, and shelves
15. Visible materials
16. Architectural elements
17. Room layout and circulation
18. Design observations
19. Practical layout recommendations

For every detected color, return:

- name
- hex
- rgb
- percentage
- category
- location

For every detected object, return:

- name
- category
- location
- condition
- confidence from 0 to 1

Only describe things that are visible in the image.
Do not return generic filler.
"""
        response = None

        # Make one Gemini attempt only. If Gemini returns 503/429 or times out,
        # analyze_room_with_ai() immediately uses the local OpenCV/YOLO fallback.
        try:
            response = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=[
                    types.Part.from_bytes(
                        data=image_bytes,
                        mime_type=mime_type
                    ),
                    prompt
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=RoomAnalysisResponse
                )
            )
        except Exception:
            raise

        if getattr(response, "parsed", None):
            parsed = response.parsed
            result = parsed.model_dump() if hasattr(parsed, "model_dump") else dict(parsed)
            return merge_local_vision_into_analysis(result, local_vision)

        if getattr(response, "text", None):
            return merge_local_vision_into_analysis(json.loads(response.text), local_vision)

        return None

    except Exception as error:
        # 503/429 errors are expected provider failures; keep the terminal
        # readable because the local fallback will handle the analysis.
        error_text = str(error)
        temporary_error = any(
            code in error_text
            for code in ("503", "500", "429", "UNAVAILABLE", "RESOURCE_EXHAUSTED")
        )
        if temporary_error:
            print(f"Gemini unavailable ({error_text[:220]}). Using local fallback.")
        else:
            import traceback
            print("\n=== GEMINI SDK ERROR ===")
            print(f"Error: {error}")
            traceback.print_exc()
            print("========================\n")
        return None


def merge_local_vision_into_analysis(result, local_vision):
    """Keep measured OpenCV and YOLO facts authoritative in Gemini's response."""
    if not isinstance(result, dict) or not local_vision:
        return result

    if local_vision.get("colorPalette"):
        result["colorPalette"] = local_vision["colorPalette"]
    if local_vision.get("detectedObjects"):
        result["detectedObjects"] = local_vision["detectedObjects"]
    if local_vision.get("lighting") and local_vision["lighting"] != "Unknown":
        result["lighting"] = local_vision["lighting"]
    if local_vision.get("roomSize") and local_vision["roomSize"] != "Unknown":
        result["roomSize"] = local_vision["roomSize"]
    if local_vision.get("wallColour"):
        result["wallColour"] = local_vision["wallColour"]
    return result


def analyze_room_with_ai(image_path, room_type_hint, local_vision=None):
    """Use Gemini for analysis; return None so the route uses local fallback if unavailable."""
    try:
        print("Trying Gemini room analysis...")
        result = run_with_timeout(
            lambda: analyze_room_with_gemini(
                image_path,
                room_type_hint,
                local_vision
            ),
            timeout_seconds=18,
            label="Gemini room analysis"
        )
        if result:
            print("Gemini analysis succeeded")
            return result
    except Exception as error:
        print(f"Gemini analysis failed: {error}")

    print("Gemini unavailable; using local fallback analysis.")
    return None


# Web Application Routes
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/studio")
def studio():
    username = session.get('username', 'Guest')
    return render_template("studio.html", username=username)


@app.route("/budget-planner")
def budget_planner():
    """Render the planner using the latest plan created from the user's budget."""
    budget_plan = session.get("budget_plan", {})
    return render_template(
        "budget.html",
        user_name=session.get("username", "there"),
        budget_plan=budget_plan
    )


# ---------------------------------------------------------------------------
# Rich fallback analysis (used when Gemini is unavailable)
# ---------------------------------------------------------------------------
def _hex_from_hls(h, l, s):
    r, g, b = [int(round(c * 255)) for c in colorsys.hls_to_rgb(
        h % 1.0, max(0.0, min(1.0, l)), max(0.0, min(1.0, s)))]
    return f"#{r:02X}{g:02X}{b:02X}", f"rgb({r}, {g}, {b})"


def _designer_colour_name(h, l, s):
    families = [(0.03, "Coral"), (0.08, "Terracotta"), (0.13, "Amber"), (0.19, "Mustard"),
                (0.27, "Olive"), (0.42, "Sage Green"), (0.50, "Teal"), (0.58, "Aqua"),
                (0.68, "Dusty Blue"), (0.76, "Indigo"), (0.84, "Plum"), (0.93, "Rose"),
                (1.01, "Coral")]
    family = next(name for limit, name in families if (h % 1.0) < limit)
    if l < 0.28:
        tone = "Deep"
    elif l < 0.40:
        tone = "Rich"
    elif l > 0.78:
        tone = "Pale"
    elif l > 0.64:
        tone = "Soft"
    elif s < 0.35:
        tone = "Muted"
    else:
        tone = ""
    return f"{tone} {family}".strip()


def _parse_rgb(rgb_str):
    values = rgb_str.replace("rgb(", "").replace(")", "").split(",")
    return [int(v.strip()) for v in values[:3]]


def build_fallback_palette(color_palette=None, design_style="Modern", count=12):
    """Build a varied, room-aware recommendation palette using colour theory."""
    base_h = None
    for c in (color_palette or []):
        try:
            r, g, b = [v / 255.0 for v in _parse_rgb(c["rgb"])]
            h, l, s = colorsys.rgb_to_hls(r, g, b)
            if s >= 0.18 and 0.15 < l < 0.85:
                base_h = h
                break
        except Exception:
            continue
    if base_h is None:
        base_h = random.random()
    base_h = (base_h + random.uniform(-0.03, 0.03)) % 1.0

    tone = {"Modern": (0.42, 0.38), "Minimalist": (0.62, 0.22),
            "Scandinavian": (0.66, 0.26), "Luxury": (0.28, 0.45)}
    base_l, base_s = tone.get(design_style, (0.45, 0.35))

    roles = [
        ("Accent wall", 0.50, 0.00, 0.05, "Sits opposite the room's main hue on the colour wheel. Ideal for an accent wall or a statement armchair."),
        ("Harmony", 0.083, 0.05, 0.00, "A neighbouring hue that blends with the existing tones for a layered, harmonious look on walls or large textiles."),
        ("Harmony", -0.083, 0.05, 0.00, "A calming adjacent shade that softens the transition between walls, flooring and furniture."),
        ("Balance", 0.333, 0.00, -0.05, "Adds balanced variety on curtains, cushions and artwork without clashing with the base palette."),
        ("Balance", -0.333, 0.00, -0.05, "Brings depth to rugs, throws and decorative accessories."),
        ("Contrast", 0.42, 0.08, 0.00, "A gentler contrast option, well suited to feature furniture and upholstery."),
        ("Contrast", 0.58, 0.08, 0.00, "A refined secondary contrast for shelving, curtains or a reading corner."),
        ("Light tint", 0.04, 0.22, -0.10, "A light, airy tone for ceilings, trims or sheer curtains that brightens the whole room."),
        ("Deep shade", 0.00, -0.18, 0.00, "A deeper shade of the dominant tone for grounding pieces such as sofas, shelves or a dark feature wall."),
    ]

    palette, seen = [], set()
    for role, shift, dl, ds, reason in roles:
        h = (base_h + shift) % 1.0
        l = max(0.15, min(0.88, base_l + dl))
        s = max(0.15, min(0.70, base_s + ds))
        hex_value, rgb_value = _hex_from_hls(h, l, s)
        name = _designer_colour_name(h, l, s)
        if name in seen:
            name = f"{name} ({role})"
        seen.add(name)
        palette.append({"name": name, "hex": hex_value, "rgb": rgb_value, "reason": reason})

    palette += [
        {"name": "Graphite Charcoal", "hex": "#3A3D44", "rgb": "rgb(58, 61, 68)",
         "reason": "Adds contrast and definition to frames, legs, handles and architectural lines."},
        {"name": "Muted Brass", "hex": "#B89B5E", "rgb": "rgb(184, 155, 94)",
         "reason": "A warm metallic for lamps, mirror frames, cabinet pulls and small highlights."},
        {"name": "Soft Stone Grey", "hex": "#B9BDC2", "rgb": "rgb(185, 189, 194)",
         "reason": "A cool neutral for rugs, throws and large surfaces that need to stay quiet."},
    ]
    return palette[:count]


FALLBACK_LAYOUTS = {
    "Living Room": [
        ("Anchor the seating to a focal point", "Face the main sofa toward the TV wall, fireplace or largest window so the room has a clear centre."),
        ("Create a conversation zone", "Place two armchairs or a loveseat at an angle to the sofa, around a central coffee table, so guests can talk comfortably."),
        ("Float the furniture", "Pull the sofa 30 to 40 cm from the wall to add depth and define the seating area."),
        ("Keep circulation open", "Leave at least 75 cm of clear walkway between furniture groups and along the door path."),
        ("Layer the lighting", "Combine ceiling light with a floor lamp beside the sofa and a table lamp for warm evening ambience."),
        ("Ground the zone with a rug", "Use a rug large enough for the front legs of all seating to rest on it, which unifies the group."),
    ],
    "Bedroom": [
        ("Centre the bed on the main wall", "Place the bed on the wall opposite the door with matching nightstands on both sides for symmetry."),
        ("Respect the swing zones", "Leave 60 to 75 cm around the bed and in front of wardrobes so doors and drawers open fully."),
        ("Keep the entry path clear", "Maintain an unobstructed line from the doorway to the bed and wardrobe."),
        ("Add soft, layered lighting", "Use bedside lamps, a dimmable ceiling light and optional wall washers for a restful evening mood."),
        ("Use the window wall wisely", "Keep tall furniture away from the window to protect daylight and add full-length curtains for height."),
        ("Add a reading or dressing corner", "A small chair with a floor lamp in a free corner makes the room feel complete and balanced."),
    ],
    "Kitchen": [
        ("Respect the work triangle", "Keep the sink, hob and refrigerator in a compact triangle with no obstruction between them."),
        ("Protect counter landing space", "Leave 30 to 45 cm of clear counter beside the hob and the refrigerator for safe, easy handling."),
        ("Add task lighting", "Install under-cabinet lighting along the main prep counter and a pendant above any island or dining nook."),
        ("Zone the storage", "Keep everyday items between hip and shoulder height and put bulky appliances in lower cabinets."),
        ("Keep aisles comfortable", "Allow about 100 to 120 cm between opposing counters so two people can work at once."),
        ("Add a visual feature", "A backsplash in a contrasting tone or textured tile gives the room a clear focal point."),
    ],
    "Bathroom": [
        ("Keep the vanity area clear", "Avoid tall units beside the mirror so the sink and mirror stay bright and accessible."),
        ("Allow full door clearance", "Make sure the door swings fully without touching fixtures, and leave about 60 cm in front of the toilet."),
        ("Use vertical storage", "Wall-mounted cabinets or niches above the toilet and beside the mirror free up floor space."),
        ("Light the mirror evenly", "Place lights at both sides of the mirror or use a backlit mirror to avoid shadows on the face."),
        ("Separate wet and dry zones", "Keep the shower area visually distinct with a glass screen or a change of tile tone."),
        ("Add warmth with textiles", "Towels, a bath mat and a small plant soften the hard surfaces and tie the colour scheme together."),
    ],
}

def get_fallback_layouts(room_type):
    items = FALLBACK_LAYOUTS.get((room_type or "").title().strip(), FALLBACK_LAYOUTS["Living Room"])
    return [{"title": t, "description": d, "tip": d} for t, d in items]


OBJECT_MATERIALS = {
    "couch": "Upholstered fabric", "chair": "Wood frame with upholstery", "bed": "Mattress and soft bedding textiles",
    "dining table": "Solid wood or laminate", "tv": "Glass and plastic casing", "potted plant": "Natural foliage and ceramic planter",
    "vase": "Ceramic or glass", "book": "Paper and print", "refrigerator": "Stainless steel finish",
    "oven": "Stainless steel and glass", "sink": "Ceramic or stainless steel", "toilet": "Glazed ceramic",
    "clock": "Metal and glass", "laptop": "Aluminium and plastic", "bench": "Wood or metal",
}

ROOM_MATERIALS = {
    "Living Room": ["Painted wall surfaces", "Flooring (tile or wood-look)", "Soft furnishings and textiles"],
    "Bedroom": ["Painted wall surfaces", "Flooring (tile or wood-look)", "Bedding and curtain fabrics"],
    "Kitchen": ["Painted or tiled walls", "Countertop surface", "Cabinet fronts", "Floor tile"],
    "Bathroom": ["Glazed wall tile", "Floor tile", "Ceramic sanitaryware", "Metal fittings"],
}

ROOM_ELEMENTS = {
    "Living Room": ["Wall surfaces", "Ceiling and general lighting", "Flooring", "Window and natural light source", "Door and circulation path"],
    "Bedroom": ["Wall surfaces", "Ceiling and general lighting", "Flooring", "Window and curtain area", "Door and entry path", "Wardrobe or storage wall"],
    "Kitchen": ["Wall surfaces and backsplash zone", "Ceiling and general lighting", "Flooring", "Window and ventilation", "Door and entry path", "Countertop and cabinet run"],
    "Bathroom": ["Wall tile surfaces", "Ceiling and general lighting", "Flooring", "Ventilation or window", "Door and entry path", "Vanity and fixture zone"],
}

def infer_fallback_materials(detected_objects, room_type):
    materials = list(ROOM_MATERIALS.get(room_type, ROOM_MATERIALS["Living Room"]))
    for obj in detected_objects or []:
        mat = OBJECT_MATERIALS.get(str(obj.get("name", "")).lower())
        if mat and mat not in materials:
            materials.append(mat)
    return materials[:10]


def build_fallback_observations(room_type, design_style, lighting, room_size, color_palette, detected_objects):
    obs = []
    room = (room_type or "room").lower()

    if color_palette:
        top = color_palette[0]
        obs.append(
            f"The dominant tone is {top['name']} ({top['hex']}), covering about "
            f"{top['percentage']:.0f}% of the scene, and it sets the overall mood of the {room}."
        )
        warm = cool = 0.0
        lightness = []
        for c in color_palette:
            try:
                r, g, b = [v / 255.0 for v in _parse_rgb(c["rgb"])]
                h, l, s = colorsys.rgb_to_hls(r, g, b)
                lightness.append(l)
                if s >= 0.12:
                    if h < 0.17 or h > 0.92:
                        warm += c["percentage"]
                    elif 0.45 < h < 0.75:
                        cool += c["percentage"]
            except Exception:
                continue
        if warm + cool > 0:
            if warm >= cool * 1.5:
                obs.append("The colour balance leans warm, which feels inviting. Cooler accents would add contrast and depth.")
            elif cool >= warm * 1.5:
                obs.append("The colour balance leans cool and calm. A few warm accents such as wood, brass or terracotta would add warmth.")
            else:
                obs.append("Warm and cool tones are fairly balanced, which gives a flexible base for introducing new accent colours.")
        if lightness and (max(lightness) - min(lightness)) > 0.5:
            obs.append("There is strong light-to-dark contrast between surfaces, so a mid-tone accent would help bridge the two.")
        else:
            obs.append("Tonal contrast between surfaces is soft, so adding a deeper accent colour would give the room more definition.")

    lighting_notes = {
        "Low Light": "Ambient light is low. Layered lighting (ceiling, floor lamp and accent lights) would improve both comfort and how colours appear.",
        "Moderate Light": "Lighting is moderate. Adding task and accent lights would make the room feel brighter and more dimensional.",
        "Natural Light (Good)": "The room receives good natural light, so lighter fabrics and reflective accents will make the most of it.",
        "Bright": "The room is very bright. Soft textiles, sheer curtains and warm lamps will keep the brightness comfortable.",
    }
    if lighting in lighting_notes:
        obs.append(lighting_notes[lighting])

    if room_size and room_size != "Unknown":
        size_word = room_size.split()[0].lower()
        size_notes = {
            "large": "The space reads as generous, so it can support distinct zones and larger statement pieces.",
            "medium": "The space reads as medium-sized, so proportionate furniture and clear walkways will keep it balanced.",
            "small": "The space reads as compact, so multi-purpose furniture, vertical storage and lighter tones will help it feel larger.",
        }
        if size_word in size_notes:
            obs.append(size_notes[size_word])

    if detected_objects:
        names = [n for n, _ in Counter(str(o.get("name", "")).title() for o in detected_objects).most_common(4)]
        obs.append(f"Visible items such as {', '.join(names)} anchor the current layout. Their placement should guide the circulation plan.")
    else:
        obs.append("Surfaces appear relatively open, which leaves room to introduce focal furniture and layered decor.")

    obs.append(f"A {design_style.lower()} direction would work well here by refining materials, proportions and accessories while keeping the room's character.")
    return obs[:8]


@app.route("/upload", methods=["POST"])
def upload():
    # 1. File Validation
    if "room_photo" not in request.files:
        return jsonify({'success': False, 'message': 'No photo provided'}), 400

    photo = request.files["room_photo"]
    if photo.filename == '':
        return jsonify({'success': False, 'message': 'No selected file'}), 400

    # 2. Save Original Image. Every upload gets a brand-new unique file name,
    #    so one design session can never overwrite or reuse another one's photo.
    original_name = secure_filename(photo.filename)
    extension = os.path.splitext(original_name)[1].lower()
    if not original_name or extension not in ALLOWED_EXTENSIONS:
        return jsonify({'success': False, 'message': 'Please upload a JPG, PNG or WEBP image.'}), 400
 
    safe_filename = f"room_{uuid.uuid4().hex}{extension}"
    save_path = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)
    photo.save(save_path)
 
    # 3. Form Data Extraction (only the four allowed rooms and styles)
    room_type = request.form.get('room_type', 'Living Room')
    if room_type not in ALLOWED_ROOMS:
        room_type = 'Living Room'
    design_style = request.form.get('design_style', 'Modern')
    if design_style not in ALLOWED_STYLES:
        design_style = 'Modern'
    # Renovation-scope choices were removed from the UI. Every redesign now
    # follows the single, supported full-room workflow.
    renovation_scope = "entire_room"

    budget_range_param = request.form.get('budget_range', '10000-25000')
    try:
        budget_min, budget_max = [float(value) for value in budget_range_param.split('-', 1)]
        estimated_cost_param = str(round((budget_min + budget_max) / 2))
    except (TypeError, ValueError):
        budget_min, budget_max = 10000.0, 25000.0
        estimated_cost_param = '17500'
    date_created = datetime.now().strftime('%Y-%m-%d')

   # 4. Local vision first: OpenCV handles colours/lighting and YOLO handles objects.
    local_vision = build_local_vision_context(save_path)

    # Gemini receives the local facts and focuses on design interpretation.
    try:
        ai_analysis = analyze_room_with_ai(
            save_path,
            f"{room_type}; requested interior style: {design_style}",
            local_vision
        )
    except Exception as e:
        print(f"--> ROUTE ANALYSIS EXCEPTION: {e}")
        ai_analysis = None

    # What the results template receives as "ai_analysis" (for the recommended colour section).
    template_analysis = ai_analysis

    if ai_analysis:
        room_size_estimate = ai_analysis.get("roomSize", "Unknown")
        lighting_level = ai_analysis.get("lighting", "Unknown")

        wall_info = ai_analysis.get("wallColour", {}) or {}
        color_name = wall_info.get("name", "Detected Tone")
        color_tag = wall_info.get("mood", "Neutral")
        detected_color_hex = wall_info.get("hex", "#CCCCCC")
        detected_color = wall_info.get("rgb", detected_color_hex)

        recommended = ai_analysis.get("recommendedColors", []) or []
        defaults = ["#6B8FB8", "#A7C957", "#D96B6B"]

        def get_hex_safe(items, index, fallback):
            if index >= len(items):
                return fallback
            item = items[index]
            if isinstance(item, dict):
                return item.get("hex", fallback)
            return item if isinstance(item, str) else fallback

        complementary_hex = get_hex_safe(recommended, 0, defaults[0])
        analogous1_hex = get_hex_safe(recommended, 1, defaults[1])
        analogous2_hex = get_hex_safe(recommended, 2, defaults[2])
        recommendations = {
            "complementary": complementary_hex,
            "analogous1": analogous1_hex,
            "analogous2": analogous2_hex
        }

        architectural_style = ai_analysis.get("architecturalStyle", "Not detected")
        color_palette = ai_analysis.get("colorPalette", []) or []
        detected_objects = ai_analysis.get("detectedObjects", []) or []
        design_observations = ai_analysis.get("designObservations", []) or []
        materials = ai_analysis.get("materials", []) or []
        architectural_elements = ai_analysis.get("architecturalElements", []) or []
        layout_suggestions = ai_analysis.get("layouts", []) or []
        layout_suggestions += get_layout_suggestions(room_type)
        analysis_source = "ai"
    else:
        color_palette = local_vision.get("colorPalette", [])
        recommended_palette = build_fallback_palette(color_palette, design_style)

        main_color = color_palette[0]
        detected_color = main_color["rgb"]
        detected_color_hex = main_color["hex"]
        color_name = main_color["name"]
        color_tag = "Neutral"   # refined below once r, g, b are parsed

        values = (
            detected_color
            .replace("rgb(", "")
            .replace(")", "")
            .split(",")
        )

        r, g, b = [
            int(value.strip())
            for value in values[:3]
        ]
        color_tag = describe_wall_color(r, g, b)[1]

        # Keep the distinct fallback palette; do not overwrite it with detected colors.
        recommendations = {
            "complementary": recommended_palette[0]["hex"],
            "analogous1": recommended_palette[1]["hex"],
            "analogous2": recommended_palette[2]["hex"],
            "all": recommended_palette
        }

        complementary_hex = recommended_palette[0]["hex"]
        analogous1_hex = recommended_palette[1]["hex"]
        analogous2_hex = recommended_palette[2]["hex"]

        lighting_level = local_vision.get("lighting", get_lighting_level(save_path))
        room_size_estimate = local_vision.get("roomSize", estimate_room_size(save_path))

        architectural_style = f"Contemporary residential {room_type.lower()} interior"

        detected_objects = local_vision.get("detectedObjects", [])
        materials = infer_fallback_materials(detected_objects, room_type)
        architectural_elements = ROOM_ELEMENTS.get(room_type, ROOM_ELEMENTS["Living Room"])

        design_observations = build_fallback_observations(
            room_type, design_style, lighting_level,
            room_size_estimate, color_palette, detected_objects
        )

        layout_suggestions = get_fallback_layouts(room_type)
        analysis_source = "computer_vision_fallback"

        # Lets the results page show the full recommended palette (not just 3 swatches).
        template_analysis = {"recommendedColors": recommended_palette}


    # 5. Cost Estimator & Shopping List Generator
    cost_data, shopping_list = get_cost_and_shopping_list(
    room_type,
    estimated_cost_param
)
    cost_data["min_range"] = f"₹{budget_min:,.0f}"
    cost_data["max_range"] = f"₹{budget_max:,.0f}"
    cost_data["budget_range"] = budget_range_param
    cost_data["planned_total"] = cost_data["total_estimated"]

    # Make the exact upload budget and generated shopping allocations available
    # to the standalone Budget Planner page. Values are stored as numbers so
    # the planner can recalculate quantities and totals accurately in JavaScript.
    budget_items = []
    for item in cost_data.get("itemized", []):
        raw_price = str(item.get("price", "0"))
        numeric_price = float(
            raw_price.replace("₹", "").replace(",", "").strip() or 0
        )
        budget_items.append({
            "name": item.get("name", "Planned item"),
            "category": item.get("category", "Other"),
            "cost": numeric_price,
            "quantity": 1,
            "total": numeric_price,
            "url": item.get("url", "")
        })

    session["budget_plan"] = {
        "room_type": room_type,
        "budget_range": budget_range_param,
        "total_budget": float(estimated_cost_param),
        "estimated_cost": float(
            str(cost_data.get("total_estimated", "0"))
            .replace("₹", "")
            .replace(",", "")
            .strip() or 0
        ),
        "min_range": budget_min,
        "max_range": budget_max,
        "items": budget_items
    }
    
    # Use form's estimated_cost if supplied; otherwise use calculated total
    final_cost = (
        estimated_cost_param
        if estimated_cost_param not in (None, "")
        else cost_data["total_estimated"]
    )

    # Select the palette for the regenerated image.
    palette_for_redesign = []

    if isinstance(ai_analysis, dict):
        palette_for_redesign = (
            ai_analysis.get("recommendedColors")
            or ai_analysis.get("recommended_colors")
            or []
        )

    if not palette_for_redesign:
        palette_for_redesign = recommendations.get("all", [])

    print("Palette sent to redesign:", palette_for_redesign)

    # Generate the redesigned image only once.
    generated_image = None

    # Stability AI is the only image-regeneration provider.
    if STABILITY_API_KEY:
        generated_image = run_with_timeout(
            lambda: generate_stability_redesign(
                image_path=save_path,
                room_type=room_type,
                design_style=design_style,
                color_palette=palette_for_redesign,
                layout_suggestions=layout_suggestions,
                detected_objects=detected_objects,
                lighting_level=lighting_level,
                renovation_scope=renovation_scope
            ),
            timeout_seconds=45,
            label="Stability image editing"
        )
    else:
        print("Stability image regeneration skipped: STABILITY_API_KEY is missing.")

    if generated_image is None:
        print("Image regeneration was unavailable.")
    
    # 7. Save Record to Database (If User Logged In)
    if 'user_id' in session:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute(
            '''INSERT INTO designs
               (user_id, room_type, image_path, generated_image_path, estimated_cost, date_created)
               VALUES (?, ?, ?, ?, ?, ?)''',
            (
                session['user_id'],
                room_type,
                f'uploads/{safe_filename}',
                (
                    f'generated/{generated_image}'
                    if generated_image
                    else None
                ),
                final_cost,
                date_created
            )
        )
        conn.commit()
        conn.close()

    # 8. Render Integrated Results Page
    return render_template(
        "result.html",
        image_file=safe_filename,
        generated_image=generated_image,
        ai_analysis=template_analysis,
        detected_color=detected_color,
        detected_color_hex=detected_color_hex,
        color_name=color_name,
        color_tag=color_tag,
        complementary_hex=complementary_hex,
        analogous1_hex=analogous1_hex,
        analogous2_hex=analogous2_hex,
        lighting_level=lighting_level,
        room_size_estimate=room_size_estimate,
        detected_objects=detected_objects,
        architectural_style=architectural_style,
        color_palette=color_palette,
        design_observations=design_observations,
        analysis_source="ai",
        materials=materials,
        architectural_elements=architectural_elements,
        recommendations=recommendations,
        room_type=room_type,
        design_style=design_style,
        renovation_scope=renovation_scope,
        renovation_scope_label=RENOVATION_SCOPE_LABELS.get(renovation_scope, "Entire room"),
        layout_suggestions=layout_suggestions,
        cost_data=cost_data,
        shopping_list=shopping_list
    )


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        if not username or not email or not password:
            return jsonify({'success': False, 'message': 'All fields are required'}), 400

        hashed_password = generate_password_hash(password)

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        try:
            cursor.execute(
                'INSERT INTO users (username, email, password) VALUES (?, ?, ?)',
                (username, email, hashed_password)
            )
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            return jsonify({'success': False, 'message': 'Email already registered'}), 409
        conn.close()

        return jsonify({'success': True, 'message': 'Registration successful'}), 200

    return render_template("register.html")


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if not email or not password:
            return jsonify({'success': False, 'message': 'Email and password required'}), 400

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute(
    '''SELECT id, username, email, password, phone, location,
              style_preference, avatar
       FROM users
       WHERE email = ?''',
    (email,)
)

        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user[3], password):
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['email'] = user[2]
            session['full_name'] = user[1]
            session['phone'] = user[4] or ''
            session['location'] = user[5] or ''
            session['style_preference'] = user[6] or ''
            session['avatar'] = user[7] or None

            return jsonify({'success': True, 'message': 'Login successful'}), 200
        else:
            return jsonify({'success': False, 'message': 'Invalid email or password'}), 401

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/reset-password', methods=['POST'])
def reset_password():
    email = request.form.get('email')
    new_password = request.form.get('new_password')

    if not email or not new_password:
        return jsonify({'success': False, 'message': 'Email and new password are required.'}), 400

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
    user = cursor.fetchone()

    if not user:
        conn.close()
        return jsonify({'success': False, 'message': 'No account found with this email.'}), 404

    hashed_password = generate_password_hash(new_password)
    cursor.execute('UPDATE users SET password = ? WHERE email = ?', (hashed_password, email))
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'message': 'Password reset successful! Please log in.'}), 200


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.route("/design-ideas")
def design_ideas():
    return render_template("design_ideas.html")


@app.route('/send-message', methods=['POST'])
def send_message():
    name = request.form.get('name')
    user_email = request.form.get('email')
    subject_input = request.form.get('subject')
    message_text = request.form.get('message')

    if not name or not user_email or not message_text:
        return jsonify({'success': False, 'message': 'Please fill in all required fields.'}), 400

    try:
        msg = MIMEMultipart()
        msg['From'] = email_address
        msg['To'] = email_address
        msg['Subject'] = f"Contact Form: {subject_input or 'New Inquiry'}"

        body = f"Name: {name}\nEmail: {user_email}\n\nMessage:\n{message_text}"
        msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(email_address, email_password)
            server.send_message(msg)

        return jsonify({'success': True, 'message': "Message sent! We'll get back to you within 24 hours."}), 200

    except Exception as e:
        print("SMTP Error Details:", e)
        return jsonify({'success': False, 'message': f'Failed to send message: {str(e)}'}), 500


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']

    if request.method == 'POST':
        if request.form.get('remove_avatar') == 'true':
            session.pop('avatar', None)

        if 'avatar' in request.files:
            file = request.files['avatar']
            if file and file.filename != '':
                extension = os.path.splitext(secure_filename(file.filename))[1].lower()
                if extension in ALLOWED_EXTENSIONS:
                    filename = f"avatar_{user_id}_{uuid.uuid4().hex[:8]}{extension}"
                    save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(save_path)
                    session['avatar'] = filename

        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        location = request.form.get('location', '').strip()

        avatar_filename = session.get('avatar')

        conn = sqlite3.connect('database.db')
        conn.execute(
            '''
            UPDATE users
            SET username = ?,
                email = ?,
                phone = ?,
                location = ?,
                avatar = ?
            WHERE id = ?
            ''',
            (
                full_name,
                email,
                phone,
                location,
                avatar_filename,
                session['user_id']
            )
        )

        conn.commit()
        conn.close()

        session['username'] = full_name
        session['full_name'] = full_name
        session['email'] = email
        session['phone'] = phone
        session['location'] = location
        session['avatar'] = avatar_filename


    user_data = {
        'full_name': session.get('full_name', session.get('username', 'User')),
        'email': session.get('email', ''),
        'phone': session.get('phone', ''),
        'location': session.get('location', ''),
        'avatar': session.get('avatar', None)
    }

    return render_template('profile.html', user=user_data)


@app.route('/gallery')
def gallery():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute(
        'SELECT id, room_type, image_path, generated_image_path, estimated_cost, date_created FROM designs WHERE user_id = ?',
        (session['user_id'],)
    )
    rows = cursor.fetchall()
    conn.close()

    designs = []
    for r in rows:
        designs.append({
            'id': r[0],
            'room_type': r[1],
            'image_path': r[2],
            'generated_image_path': r[3],
            'estimated_cost': r[4],
            'date_created': r[5]
        })

    return render_template('gallery.html', designs=designs)


@app.route('/delete_design/<int:design_id>')
def delete_design(design_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute(
        'DELETE FROM designs WHERE id = ? AND user_id = ?',
        (design_id, session['user_id'])
    )
    conn.commit()
    conn.close()
    return redirect(url_for('gallery'))
@app.errorhandler(413)
def file_too_large(error):
    return jsonify({'success': False, 'message': 'That image is larger than 10 MB. Please choose a smaller one.'}), 413

@app.route('/api/budget', methods=['GET'])
def api_budget_get():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please log in to save budgets.'}), 401
    conn = sqlite3.connect('database.db')
    row = conn.execute('SELECT data FROM budgets WHERE user_id = ?', (session['user_id'],)).fetchone()
    conn.close()
    return jsonify({'success': True, 'budget': json.loads(row[0]) if row else None})
 
 
@app.route('/api/budget', methods=['POST'])
def api_budget_save():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please log in to save to your account.'}), 401
 
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not isinstance(data.get('rows'), list) or len(data['rows']) > 200:
        return jsonify({'success': False, 'message': 'Invalid budget data.'}), 400
 
    room = data.get('room') if data.get('room') in ALLOWED_ROOMS else 'Living Room'
    try:
        budget = max(0.0, float(data.get('budget') or 0))
    except (TypeError, ValueError):
        budget = 0.0
 
    clean_rows = []
    for row in data['rows']:
        if not isinstance(row, dict):
            continue
        try:
            actual = row.get('actual')
            clean_rows.append({
                'name': str(row.get('name', ''))[:80],
                'category': str(row.get('category', 'Other'))[:40],
                'unit': max(0.0, float(row.get('unit') or 0)),
                'qty': max(1, int(float(row.get('qty') or 1))),
                'actual': None if actual in (None, '') else max(0.0, float(actual)),
                'url': str(row.get('url') or '')[:500],
            })
        except (TypeError, ValueError):
            continue
 
    payload = json.dumps({'room': room, 'budget': budget, 'rows': clean_rows})
    conn = sqlite3.connect('database.db')
    conn.execute(
        'INSERT OR REPLACE INTO budgets (user_id, data, updated) VALUES (?, ?, ?)',
        (session['user_id'], payload, datetime.now().strftime('%Y-%m-%d %H:%M'))
    )
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Budget saved.'})

if __name__ == "__main__":
    app.run(debug=False, use_reloader=False)