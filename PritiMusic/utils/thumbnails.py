import os
import re
import random
import aiofiles
import aiohttp
import colorsys
from PIL import (Image, ImageDraw, ImageFilter, ImageFont, ImageOps)
from py_yt import VideosSearch
from PritiMusic import app

def get_glowing_circle(image):
    """
    Crops the image into a circle and applies a multi-layered glow:
    Yellow -> White -> Pink -> White, with a solid white border.
    """
    img = image.convert("RGBA")
    size = min(img.size)
    
    # 1. Crop image into a perfect circle
    img = ImageOps.fit(img, (size, size), centering=(0.5, 0.5))
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size, size), fill=255)
    circular_img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    circular_img.paste(img, (0, 0), mask)

    # 2. Setup canvas for the glow effect (larger than the image)
    offset = 50  # Padding for the glow
    glow_size = size + (offset * 2)
    glow = Image.new("RGBA", (glow_size, glow_size), (0, 0, 0, 0))
    draw_glow = ImageDraw.Draw(glow)

    # 3. Draw concentric circles for the glow effect
    # Outer Yellow Glow
    draw_glow.ellipse((5, 5, glow_size-5, glow_size-5), fill=(255, 255, 0, 60))
    # Outer White Glow
    draw_glow.ellipse((15, 15, glow_size-15, glow_size-15), fill=(255, 255, 255, 80))
    # Pink Glow
    draw_glow.ellipse((25, 25, glow_size-25, glow_size-25), fill=(255, 105, 180, 150))
    # Inner White Glow
    draw_glow.ellipse((35, 35, glow_size-35, glow_size-35), fill=(255, 255, 255, 200))
    
    # Apply Gaussian Blur to make it look like a smooth light glow
    glow = glow.filter(ImageFilter.GaussianBlur(15))
    
    # 4. Draw a solid hard white border directly around where the image will be
    draw_border = ImageDraw.Draw(glow)
    draw_border.ellipse((offset - 4, offset - 4, size + offset + 4, size + offset + 4), outline="white", width=8)

    # 5. Paste the actual circular image on top of the glowing background
    glow.paste(circular_img, (offset, offset), circular_img)
    
    return glow, offset

def draw_text_with_glow(draw, position, text, font, fill, glow_fill):
    x, y = position
    for dx, dy in [(-3, 0), (3, 0), (0, -3), (0, 3)]:
        draw.text((x + dx, y + dy), text, font=font, fill=glow_fill)
    draw.text((x, y), text, font=font, fill=fill)

async def download_user_photo(user_id):
    try:
        async for photo in app.get_chat_photos(user_id, limit=1):
            return await app.download_media(photo.file_id, file_name=f"cache/{user_id}.jpg")
    except: return None
    return None

async def get_thumb(videoid, user_id, user_name):
    os.makedirs("cache", exist_ok=True)
    final_path = f"cache/{videoid}_{user_id}.png"
    if os.path.exists(final_path): return final_path

    try:
        results = VideosSearch(f"https://www.youtube.com/watch?v={videoid}", limit=1)
        data = await results.next()
        result = data["result"][0]
        title = re.sub(r"\W+", " ", result["title"]).title()
        duration = result.get("duration", "00:00")
        views = result.get("viewCount", {}).get("short", "Unknown")
        channel = result.get("channel", {}).get("name", "Unknown Artist")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(result["thumbnails"][0]["url"].split("?")[0]) as resp:
                f = await aiofiles.open(f"cache/temp_{videoid}.jpg", mode="wb")
                await f.write(await resp.read())
                await f.close()

        # Base Image and Gaussian Blur for main background (behind the black card)
        bg = Image.open(f"cache/temp_{videoid}.jpg").convert("RGBA").resize((1920, 1080))
        background = bg.filter(ImageFilter.GaussianBlur(25)).point(lambda p: p * 0.35)
        
        # --- BLACK CARD EFFECT ---
        card_rect = (40, 40, 1880, 940)
        black_card = Image.new("RGBA", background.size, (0, 0, 0, 0))
        draw_card = ImageDraw.Draw(black_card)
        # Draw solid black fill card
        draw_card.rounded_rectangle(card_rect, radius=60, fill=(0, 0, 0, 255), outline=(132, 224, 240, 200), width=6)
        
        # Paste the black card onto the main background
        background = Image.alpha_composite(background, black_card)
        draw = ImageDraw.Draw(background, "RGBA")
        
        # --- RAIN EFFECT ---
        for _ in range(300):
            rx = random.randint(50, 1870)
            ry = random.randint(50, 930)
            length = random.randint(10, 30)
            draw.line([(rx, ry), (rx + 5, ry + length)], fill=(255, 255, 255, 50), width=1)
        
        try:
            f1 = ImageFont.truetype("PritiMusic/assets/font.ttf", 65)
            f2 = ImageFont.truetype("PritiMusic/assets/font2.ttf", 45)
            br = ImageFont.truetype("PritiMusic/assets/font2.ttf", 55)
        except:
            f1 = f2 = br = ImageFont.load_default()

        # --- YOUTUBE & USER GLOWING CIRCLES ---
        # YouTube Thumbnail
        yt_img_glowing, yt_offset = get_glowing_circle(bg.resize((500, 500)))
        background.paste(yt_img_glowing, (80 - yt_offset, 200 - yt_offset), yt_img_glowing)
        
        # User Profile
        u_photo = await download_user_photo(user_id)
        if u_photo:
            u_img_glowing, u_offset = get_glowing_circle(Image.open(u_photo).resize((450, 450)))
            background.paste(u_img_glowing, (1350 - u_offset, 215 - u_offset), u_img_glowing)

        # Texts
        draw.text((650, 300), (title[:22] + "...") if len(title) > 22 else title, fill="white", font=f1)
        draw.text((650, 400), f"Artist: {channel}", fill=(220, 220, 220), font=f2)
        draw.text((650, 460), f"Views: {views}", fill=(190, 190, 190), font=f2)
        draw.text((650, 520), f"Duration: {duration}", fill=(190, 190, 190), font=f2)

        # --- RAINBOW NEON AUDIO WAVE ---
        center_y = 750
        num_bars = 90
        bar_width = 6   
        spacing = 15
        start_x = 350
        
        for i in range(num_bars):
            h = random.randint(40, 80) if i % 5 == 0 else random.randint(10, 45)
            x1 = start_x + (i * spacing)
            x2 = x1 + bar_width
            if x2 > 1800: break
                
            hue = 0.60 + (i / num_bars) * 0.75
            if hue > 1.0: hue -= 1.0
            r, g, b = [int(c * 255) for c in colorsys.hsv_to_rgb(hue, 1.0, 1.0)]
            
            draw.rounded_rectangle((x1 - 8, center_y - h - 8, x2 + 8, center_y + h + 8), radius=8, fill=(r, g, b, 15))
            draw.rounded_rectangle((x1 - 4, center_y - h - 4, x2 + 4, center_y + h + 4), radius=6, fill=(r, g, b, 45))
            draw.rounded_rectangle((x1 - 1, center_y - h - 1, x2 + 1, center_y + h + 1), radius=4, fill=(r, g, b, 120))
            draw.rounded_rectangle((x1 + 2, center_y - h, x2 - 2, center_y + h), radius=2, fill=(255, 255, 255, 255))

        # Play Button icon
        draw.ellipse((930, 830, 990, 890), outline="white", width=4)
        draw.rectangle((950, 845, 960, 875), fill="white")
        draw.rectangle((965, 845, 975, 875), fill="white")

        # Footer Texts
        draw_text_with_glow(draw, (80, 975), "BETA BOT HUB", br, (132, 224, 240), (0, 255, 255, 100))
        draw_text_with_glow(draw, (1480, 975), "THE SHIV", br, (255, 60, 160), (255, 0, 170, 100))

        background.convert("RGB").save(final_path, "PNG")
        return final_path
    except Exception as e:
        print(f"Thumbnail Error: {e}")
        return None
    finally:
        if os.path.exists(f"cache/temp_{videoid}.jpg"): os.remove(f"cache/temp_{videoid}.jpg")
        if 'u_photo' in locals() and u_photo and os.path.exists(u_photo): os.remove(u_photo)
