"""Generate placeholder PNG icons for sidebar navigation items.
Creates light and dark variants for Translation, Glossary, and Settings."""
from PIL import Image, ImageDraw
import os

OUTPUT = r"E:\secure_translator_pro_backup_phase3\data\assets\icons"
SIZE = (20, 20)

def make_icon(name, draw_fn):
    """Create a 20x20 PNG icon with both light and dark variants."""
    os.makedirs(OUTPUT, exist_ok=True)
    
    # Light background
    light = Image.new("RGBA", SIZE, (0, 0, 0, 0))
    draw_fn(light, (80, 80, 90, 255))
    light.save(os.path.join(OUTPUT, f"{name}_light.png"))
    
    # Dark background
    dark = Image.new("RGBA", SIZE, (0, 0, 0, 0))
    draw_fn(dark, (200, 210, 220, 255))
    dark.save(os.path.join(OUTPUT, f"{name}_dark.png"))
    
    print(f"  ✓ {name} icons created")


# --- Book icon (Translation) ---
def draw_book(img, color):
    # Book shape
    draw = ImageDraw.Draw(img)
    # Left page
    draw.polygon([(4, 4), (10, 4), (10, 17), (4, 17)], fill=color)
    # Right page
    draw.polygon([(10, 3), (16, 3), (16, 16), (10, 17)], fill=color)
    # Spine
    draw.rectangle([(9, 3), (11, 17)], fill=(0, 0, 0, 180))


# --- Glossary icon (Dictionary) ---
def draw_glossary(img, color):
    draw = ImageDraw.Draw(img)
    # Book/Notebook shape
    draw.rectangle([(3, 2), (17, 18)], outline=color, width=2)
    draw.line([(10, 2), (10, 18)], fill=color, width=1)
    # Lines on left
    for y in range(6, 15, 3):
        draw.line([(5, y), (8, y)], fill=color, width=1)
    # Lines on right
    for y in range(5, 15, 3):
        draw.line([(12, y), (15, y)], fill=color, width=1)


# --- Settings icon (Gear) ---
def draw_settings(img, color):
    draw = ImageDraw.Draw(img)
    cx, cy = 10, 10
    r_out = 7
    r_in = 4
    
    # Draw gear shape as circle with teeth
    for angle in range(0, 360, 30):
        rad = angle * 3.14159 / 180
        x1 = cx + (r_in) * 0.9 * (1 if angle % 60 < 30 else 1.1) * (0.3 if angle % 60 < 15 else 0.7)
        y1 = cy + (r_in) * 0.9 * (1 if angle % 60 < 30 else 1.1) * (0.3 if angle % 60 < 15 else 0.7)
    
    # Simplified: circle with inner hole
    draw.ellipse([(3, 3), (17, 17)], outline=color, width=2)
    draw.ellipse([(6, 6), (14, 14)], outline=color, width=2)
    draw.ellipse([(8, 8), (12, 12)], fill=color)


for name, draw_fn in [("book", draw_book), ("glossary", draw_glossary), ("settings", draw_settings)]:
    make_icon(name, draw_fn)

print("All icons generated successfully!")
