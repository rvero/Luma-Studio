"""Small line icons drawn consistently for the Luma interface."""
from PIL import Image, ImageDraw
import customtkinter as ctk


def make_icon(name):
    scale = 3
    image = Image.new('RGBA', (24*scale, 24*scale))
    draw = ImageDraw.Draw(image)
    color = '#c4d3ec'
    def line(points, width=1.7):
        draw.line([(int(x*scale), int(y*scale)) for x,y in points], fill=color, width=round(width*scale), joint='curve')
    def rect(box, radius=2):
        draw.rounded_rectangle(tuple(int(v*scale) for v in box), radius=radius*scale, outline=color, width=round(1.7*scale))
    if name == 'download':
        line([(12,3),(12,15)]); line([(8,11),(12,15),(16,11)]); line([(4,16),(4,20),(20,20),(20,16)])
    elif name == 'convert':
        line([(4,8),(19,8),(16,5)]); line([(19,8),(16,11)]); line([(20,16),(5,16),(8,13)]); line([(5,16),(8,19)])
    elif name == 'image':
        rect((3,4,21,20)); line([(5,17),(10,12),(13,15),(16,12),(20,16)]); draw.ellipse((15*scale,7*scale,18*scale,10*scale), fill=color)
    elif name == 'picker':
        line([(7,17),(16,8),(19,11),(10,20),(5,21),(6,17)]); line([(14,6),(17,3),(21,7),(18,10)])
    elif name == 'upscale':
        rect((3,3,21,21)); line([(8,16),(16,8)]); line([(10,8),(16,8),(16,14)])
    elif name == 'compress':
        rect((4,3,20,21)); line([(12,5),(12,8)]); line([(12,11),(12,14)]); line([(12,17),(12,19)])
    return ctk.CTkImage(light_image=image, dark_image=image, size=(20,20))


def logo_image(size=128):
    """Draw the Luma mark as a scalable geometric asset."""
    unit = 4
    dim = size * unit
    canvas = Image.new('RGBA', (dim, dim))
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle((0, 0, dim-1, dim-1), radius=int(dim * .24), fill='#7497FF')
    draw.polygon([(int(dim*.20), int(dim*.72)), (int(dim*.39), int(dim*.32)),
                  (int(dim*.50), int(dim*.56)), (int(dim*.64), int(dim*.25)),
                  (int(dim*.81), int(dim*.72))], fill='#14223D')
    draw.ellipse((int(dim*.67), int(dim*.16), int(dim*.78), int(dim*.27)), fill='#ECF2FF')
    return canvas.resize((size, size), Image.Resampling.LANCZOS)


def make_logo(size=40):
    image = logo_image(128)
    return ctk.CTkImage(light_image=image, dark_image=image, size=(size, size))
