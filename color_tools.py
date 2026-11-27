from PIL import Image, ImageDraw


def image_palette(image, count=8):
    sample = image.convert('RGBA')
    sample.thumbnail((180, 180), Image.Resampling.LANCZOS)
    pixels = [p[:3] for p in sample.getdata() if p[3] >= 128]
    if not pixels:
        return []
    strip = Image.new('RGB', (len(pixels), 1))
    strip.putdata(pixels)
    quantized = strip.quantize(colors=count, method=Image.Quantize.MEDIANCUT)
    palette = quantized.getpalette()
    return ['#{:02X}{:02X}{:02X}'.format(*palette[i*3:i*3+3])
            for _, i in sorted(quantized.getcolors(), reverse=True)]


def magnified_pixel(image, pos):
    x, y = pos
    crop = image.crop((x-5, y-5, x+6, y+6)).convert('RGBA')
    crop = crop.resize((110, 110), Image.Resampling.NEAREST)
    draw = ImageDraw.Draw(crop)
    draw.rectangle((49, 49, 60, 60), outline='#ffffff', width=1)
    draw.rectangle((50, 50, 59, 59), outline='#f04444', width=1)
    return crop
