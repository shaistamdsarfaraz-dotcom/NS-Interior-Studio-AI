import os
import time
import sqlite3
import smtplib
import cv2
import numpy as np
import colorsys
import base64
import json
import uuid
import requests
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
IMAGE_PROVIDER = os.getenv("IMAGE_PROVIDER", "stability").strip().lower()

print("Analysis provider: gemini")
print("Gemini key loaded:", bool(GEMINI_API_KEY))
print("Stability key loaded:", bool(STABILITY_API_KEY))
print("Image provider:", IMAGE_PROVIDER)

email_address = os.getenv("EMAIL_ADDRESS")
email_password = os.getenv("EMAIL_APP_PASSWORD")

app = Flask(__name__)
app.secret_key = os.getenv(
    "FLASK_SECRET_KEY",
    "temporary-development-secret"
)

UPLOAD_FOLDER = 'static/uploads'
GENERATED_FOLDER = 'static/generated'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['GENERATED_FOLDER'] = GENERATED_FOLDER

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
            ('Living Room', 'Paint', 'Premium Interior Wall Paint (1 Gal)', 45.00, 'https://www.amazon.com/s?k=interior+wall+paint'),
            ('Living Room', 'Furniture', 'Modern Accent Armchair', 249.99, 'https://www.ikea.com/us/en/cat/armchairs-16239/'),
            ('Living Room', 'Lighting', 'Warm Minimalist Floor Lamp', 79.50, 'https://www.amazon.com/s?k=minimalist+floor+lamp'),
            ('Living Room', 'Decor', 'Neutral Textured Area Rug (8x10)', 189.00, 'https://www.wayfair.com/rugs/sb0/area-rugs-c215385.html'),

            # Bedroom
            ('Bedroom', 'Paint', 'Soft Matte Interior Paint', 40.00, 'https://www.amazon.com/s?k=matte+interior+paint'),
            ('Bedroom', 'Furniture', 'Solid Wood Nightstand Pair', 160.00, 'https://www.ikea.com/us/en/cat/nightstands-20656/'),
            ('Bedroom', 'Lighting', 'Ambient Bedside Table Lamp', 45.00, 'https://www.amazon.com/s?k=bedside+table+lamp'),
            ('Bedroom', 'Decor', 'Blackout Linen Curtain Set', 65.00, 'https://www.wayfair.com/curtains-drapes/sb0/curtains-drapes-c483232.html'),

            # Kitchen
            ('Kitchen', 'Paint', 'Moisture Resistant Cabinet Paint', 55.00, 'https://www.amazon.com/s?k=cabinet+paint'),
            ('Kitchen', 'Lighting', 'Modern Pendant Ceiling Lights', 120.00, 'https://www.ikea.com/us/en/cat/pendant-lights-18750/'),
            ('Kitchen', 'Decor', 'Peel and Stick Backsplash Tiles', 85.00, 'https://www.amazon.com/s?k=peel+and+stick+backsplash'),

            # Bathroom
            ('Bathroom', 'Paint', 'Anti-Mold Bathroom Wall Paint', 50.00, 'https://www.amazon.com/s?k=bathroom+paint'),
            ('Bathroom', 'Lighting', 'LED Vanity Mirror Light Fixture', 95.00, 'https://www.amazon.com/s?k=vanity+mirror+light'),
            ('Bathroom', 'Decor', 'Matte Black Towel Rack & Accessories', 45.00, 'https://www.wayfair.com/bath/sb0/bathroom-hardware-sets-c1868352.html')
        ]
        cursor.executemany('''
            INSERT INTO item_prices (room_type, category, item_name, estimated_price, shopping_url)
            VALUES (?, ?, ?, ?, ?)
        ''', default_items)

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


# Feature 8: Before/After AI Image Generation (Stability AI)
def generate_ai_redesign(
    image_path,
    room_type,
    design_style=None,
    color_palette=None,
    layout_suggestions=None,
    detected_objects=None
):
    """
    Regenerates the uploaded room using the detected colors,
    recommended palette, and layout suggestions.
    """

    if not STABILITY_API_KEY:
        print("--> STABILITY ERROR: STABILITY_API_KEY is not set.")
        return None

    design_style = design_style or "Modern"
    color_palette = color_palette or []
    layout_suggestions = layout_suggestions or []
    detected_objects = detected_objects or []

    # Extract recommended color names and HEX values
    color_lines = []

    for index, color in enumerate(color_palette[:6]):
        if not isinstance(color, dict):
            continue

        name = color.get("name", "recommended color")
        hex_value = color.get("hex", "")
        reason = color.get("reason", "")

        if index == 0:
            use = "main wall and large background surfaces"
        elif index == 1:
            use = "accent wall, sofa, or large chair"
        elif index == 2:
            use = "curtains, cushions, or artwork"
        elif index == 3:
            use = "cushions, ceramics, or decor"
        elif index == 4:
            use = "lamps, frames, handles, or metallic accents"
        else:
            use = "small contrast details and accessories"

        color_lines.append(
            f"{name} ({hex_value}) must be used on {use}. {reason}"
        )

    color_text = " ".join(color_lines)

    if not color_text:
        color_text = (
            "Use a fresh neutral palette with soft ivory, sage green, "
            "dusty blue, warm terracotta, muted gold, and charcoal accents."
        )


    # Extract layout recommendations
    layout_lines = []

    for layout in layout_suggestions[:6]:
        if isinstance(layout, dict):
            title = layout.get("title", "")
            description = layout.get(
                "description",
                layout.get("tip", "")
            )
            layout_lines.append(
                f"{title}: {description}"
            )
        elif isinstance(layout, str):
            layout_lines.append(layout)

    layout_text = " ".join(layout_lines)

    # Extract visible objects so the redesign preserves the original room
    object_lines = []

    for item in detected_objects[:20]:
        if isinstance(item, dict):
            object_lines.append(
                f"{item.get('name', 'object')} "
                f"in {item.get('location', 'the room')}"
            )
        elif isinstance(item, str):
            object_lines.append(item)

    objects_text = ", ".join(object_lines)

    def shorten_text(value, max_length=350):
        value = str(value or "")
        return value[:max_length]


    color_text = shorten_text(color_text, 650)
    layout_text = shorten_text(layout_text, 650)
    objects_text = shorten_text(objects_text, 350)

    redesign_prompt = f"""
Redesign this exact {room_type} using the uploaded image as the source.
The user's selected interior design style is {design_style}. The final room must visibly follow this style.

Use the uploaded image to understand:
- room architecture
- existing furniture
- windows and doors
- floor and ceiling
- camera angle
- room proportions
- natural light
- available circulation space

Keep the architecture and camera angle, but create a clearly different
interior design using the following recommended palette:

{color_text}

The recommended palette is mandatory and must be visibly obvious in the final image.
Apply it across LARGE surfaces, not only accessories:
- Repaint the main visible wall or largest background surface with the first HEX color.
- Recolor the main sofa, bed, or largest furniture with the second HEX color.
- Recolor curtains, bedding, or large textiles with the third HEX color.
- Use the fourth color on a rug, accent chair, or large upholstery area.
- Use the fifth color on lamps, frames, tables, and repeated decor accents.
- Use the sixth color for controlled contrast on furniture legs, shelving, or accessories.
- Replace conflicting original orange, golden, brown, or red tones with the specified palette.
- The result must look like a real renovation with a clearly different color scheme.
- Do not preserve the original color palette except where required for natural wood or plants.

Use this layout guidance, selected for the uploaded room:

{layout_text}

Rearrange furniture to improve:
- circulation
- focal point
- balance
- scale
- lighting
- storage
- visual harmony

Preserve useful room objects, but change their placement or styling
when necessary to follow the recommended layout.

Create a sharp, photorealistic interior-design image.
Do not add people, text, labels, logos, watermarks, unrelated architecture,
extra windows, extra doors, or distorted furniture.
"""

    redesign_prompt = redesign_prompt[:3000]

    try:
        endpoint = (
            "https://api.stability.ai/v1/generation/"
            "stable-diffusion-xl-1024-v1-0/image-to-image"
         )

        original_image = cv2.imread(image_path)

        if original_image is None:
            print("--> Could not read image for redesign.")
            return None

        original_height, original_width = original_image.shape[:2]
        aspect_ratio = original_width / original_height

        # Choose the closest supported Stability SDXL size.
        if aspect_ratio >= 1.45:
            target_width, target_height = 1344, 768
        elif aspect_ratio >= 1.20:
            target_width, target_height = 1152, 896
        elif aspect_ratio >= 0.95:
            target_width, target_height = 1024, 1024
        elif aspect_ratio >= 0.74:
            target_width, target_height = 896, 1152
        elif aspect_ratio >= 0.62:
            target_width, target_height = 832, 1216
        else:
            target_width, target_height = 768, 1344

        resized_image = cv2.resize(
            original_image,
            (target_width, target_height),
            interpolation=cv2.INTER_AREA
        )

        success, encoded_image = cv2.imencode(
            ".jpg",
            resized_image,
            [int(cv2.IMWRITE_JPEG_QUALITY), 95]
        )

        if not success:
            print("--> Could not encode resized image.")
            return None

        endpoint = (
            "https://api.stability.ai/v1/generation/"
            "stable-diffusion-xl-1024-v1-0/image-to-image"
         )

        response = requests.post(
            endpoint,
            headers={
                "Authorization": f"Bearer {STABILITY_API_KEY}",
                "Accept": "application/json"
            },
            files={
                "init_image": (
                    "room_resized.jpg",
                    encoded_image.tobytes(),
                    "image/jpeg"
                )
            },
            data={
                "init_image_mode": "IMAGE_STRENGTH",

                # Higher value means the new palette is applied more strongly.
                "image_strength": "0.38",

                "text_prompts[0][text]": redesign_prompt,
                "text_prompts[0][weight]": "1",

                "text_prompts[1][text]": (
                    "original golden yellow palette, original orange palette, original brown palette, "
                    "original wall colors, unchanged wall colors, unchanged upholstery colors, "
                    "unchanged curtains, unchanged cushions, blurry, low resolution, dull colors, "
                    "washed out, distorted objects, duplicate furniture, deformed sofa, warped table, "
                    "extra windows, extra doors, people, text, logo, watermark, cartoon, illustration"
                ),
                "text_prompts[1][weight]": "-1",

                "cfg_scale": "9",
                "samples": "1",
                "steps": "40"
            },

            timeout=120
        )

        if response.status_code != 200:
            print(
                "--> Stability image generation failed:",
                response.status_code,
                response.text
            )
            return None

        response_data = response.json()
        artifacts = response_data.get("artifacts", [])

        if not artifacts:
            print("--> Stability returned no image.")
            return None

        generated_filename = (
            f"redesign_{uuid.uuid4().hex}.png"
        )

        generated_path = os.path.join(
            app.config["GENERATED_FOLDER"],
            generated_filename
        )

        image_bytes = base64.b64decode(
            artifacts[0]["base64"]
        )

        with open(generated_path, "wb") as output_file:
            output_file.write(image_bytes)

        print(
            f"--> AI redesign saved: {generated_filename}"
        )

        return generated_filename

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
def analyze_room_with_gemini(image_path, room_type_hint):
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

        prompt = f"""
You are an expert interior designer and computer-vision analyst.

Inspect the uploaded room image thoroughly.
The user's selected room type is: {room_type_hint}
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

        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model="gemini-3.6-flash",
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
                break

            except Exception as error:
                error_text = str(error)

                temporary_error = any(
                    code in error_text
                    for code in [
                        "503",
                        "500",
                        "UNAVAILABLE"
                    ]
                )

                if not temporary_error or attempt == 2:
                    raise

                wait_seconds = 3 * (attempt + 1)
                print(f"Gemini busy. Retrying in {wait_seconds} seconds...")
                time.sleep(wait_seconds)

        if getattr(response, "parsed", None):
            parsed = response.parsed
            return parsed.model_dump() if hasattr(parsed, "model_dump") else dict(parsed)

        if getattr(response, "text", None):
            return json.loads(response.text)

        return None

    except Exception as error:
        import traceback
        print("\n=== GEMINI SDK ERROR ===")
        print(f"Error: {error}")
        traceback.print_exc()
        print("========================\n")
        return None



def analyze_room_with_ai(image_path, room_type_hint):
    """Use Gemini for analysis; return None so the route uses local fallback if unavailable."""
    try:
        print("Trying Gemini room analysis...")
        result = analyze_room_with_gemini(image_path, room_type_hint)
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

def build_fallback_palette(color_palette=None):
    """Use a clearly different safe design palette when Gemini is unavailable."""
    return [
        {
            "name": "Soft Ivory",
            "hex": "#F4EFE6",
            "rgb": "rgb(244, 239, 230)",
            "reason": "Use on the main walls and large background surfaces."
        },
        {
            "name": "Sage Green",
            "hex": "#A8B89A",
            "rgb": "rgb(168, 184, 154)",
            "reason": "Use on an accent wall, sofa, chair, or large cushions."
        },
        {
            "name": "Dusty Blue",
            "hex": "#789BC4",
            "rgb": "rgb(120, 155, 196)",
            "reason": "Use for curtains, cushions, artwork, or occasional furniture."
        },
        {
            "name": "Muted Rose",
            "hex": "#C98F9B",
            "rgb": "rgb(201, 143, 155)",
            "reason": "Use for soft furnishings and decorative accents."
        },
        {
            "name": "Muted Gold",
            "hex": "#D2B36C",
            "rgb": "rgb(210, 179, 108)",
            "reason": "Use for lamps, frames, handles, and small highlights."
        },
        {
            "name": "Deep Teal Contrast",
            "hex": "#275C61",
            "rgb": "rgb(39, 92, 97)",
            "reason": "Use for controlled contrast on furniture and accessories."
        }
    ]

@app.route("/upload", methods=["POST"])
def upload():
    # 1. File Validation
    if "room_photo" not in request.files:
        return jsonify({'success': False, 'message': 'No photo provided'}), 400

    photo = request.files["room_photo"]
    if photo.filename == '':
        return jsonify({'success': False, 'message': 'No selected file'}), 400

    # 2. Save Original Image
    safe_filename = secure_filename(photo.filename)
    if not safe_filename:
        return jsonify({'success': False, 'message': 'Invalid file name'}), 400

    save_path = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)
    photo.save(save_path)

    # 3. Form Data Extraction
    room_type = request.form.get('room_type', 'Others')
    design_style = request.form.get('design_style', 'Modern')
    budget_range_param = request.form.get('budget_range', '100000-300000')
    estimated_cost_param = request.form.get('estimated_cost', None)

    try:
        budget_min, budget_max = [float(value) for value in budget_range_param.split('-', 1)]
        estimated_cost_param = str(round((budget_min + budget_max) / 2))
    except (TypeError, ValueError):
        budget_min, budget_max = 100000.0, 300000.0
        estimated_cost_param = '200000'
    date_created = datetime.now().strftime('%Y-%m-%d')

   # 4. Room Analysis (AI Vision with OpenCV fallback)
    try:
        ai_analysis = analyze_room_with_ai(
            save_path,
            f"{room_type}; requested interior style: {design_style}"
        )
    except Exception as e:
        print(f"--> ROUTE ANALYSIS EXCEPTION: {e}")
        ai_analysis = None

    if ai_analysis:
        room_type = ai_analysis.get("roomType", room_type)
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
        color_palette = get_dominant_colors(
            save_path,
            color_count=12
        )
        recommended_palette = build_fallback_palette(
            color_palette
        )
        recommendations = {
            "all": recommended_palette,
            "complementary": recommended_palette[0]["hex"],
            "analogous1": recommended_palette[1]["hex"],
            "analogous2": recommended_palette[2]["hex"]
        }

        fallback_colors = color_palette
        main_color = fallback_colors[0]

        detected_color = main_color["rgb"]
        detected_color_hex = main_color["hex"]
        color_name = main_color["name"]
        color_tag = "Detected room tone"

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

        lighting_level = get_lighting_level(save_path)
        room_size_estimate = estimate_room_size(save_path)

        architectural_style = (
            "Not available because Gemini analysis was unavailable"
        )

        detected_objects = []
        materials = []
        architectural_elements = []

        design_observations = [
            "The image was processed using local computer vision.",
            f"{len(color_palette)} significant colors were detected.",
            "The recommended palette was generated from the detected room colors."
        ]

        layout_suggestions = get_layout_suggestions(room_type)
        analysis_source = "computer_vision_fallback"


    # 5. Cost Estimator & Shopping List Generator
    cost_data, shopping_list = get_cost_and_shopping_list(
    room_type,
    estimated_cost_param
)
    cost_data["min_range"] = f"₹{budget_min:,.0f}"
    cost_data["max_range"] = f"₹{budget_max:,.0f}"
    cost_data["budget_range"] = budget_range_param
    cost_data["planned_total"] = cost_data["total_estimated"]
    
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

    if IMAGE_PROVIDER == "stability" and STABILITY_API_KEY:
        generated_image = generate_ai_redesign(
            image_path=save_path,
            room_type=room_type,
            design_style=design_style,
            color_palette=palette_for_redesign,
            layout_suggestions=layout_suggestions,
            detected_objects=detected_objects
        )

        if generated_image is None:
            print("Image regeneration was unavailable.")
            print("Image provider:", IMAGE_PROVIDER)
    
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
                generated_image,
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
        ai_analysis=ai_analysis,
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
        analysis_source=analysis_source,
        materials=materials,
        architectural_elements=architectural_elements,
        recommendations=recommendations,
        room_type=room_type,
        design_style=design_style,
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
        cursor.execute('SELECT id, username, email, password FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user[3], password):
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['email'] = user[2]
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
                filename = f"avatar_{user_id}_{file.filename}"
                save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(save_path)
                session['avatar'] = filename

        session['full_name'] = request.form.get('full_name')
        session['email'] = request.form.get('email')
        session['phone'] = request.form.get('phone')
        session['location'] = request.form.get('location')

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


if __name__ == "__main__":
    app.run(debug=True)
