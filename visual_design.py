"""Color contrast utilities for readable palette labels."""

def luminance(color):
    values = [int(color[i:i+2], 16) / 255 for i in (1, 3, 5)]
    linear = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in values]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def contrast_ratio(first, second):
    a, b = sorted((luminance(first), luminance(second)))
    return (b + 0.05) / (a + 0.05)


def swatch_text_color(background):
    return '#000000' if contrast_ratio(background, '#000000') >= contrast_ratio(background, '#FFFFFF') else '#FFFFFF'
