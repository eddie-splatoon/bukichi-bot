import logging
import os
import re

import PIL.Image
import PIL.ImageDraw
import PIL.ImageFont
import regex

logger = logging.getLogger('discord')


class ImageCreator:
    ENGLISH_FONT_PATH = os.getenv('ENGLISH_FONT_PATH')
    JAPANESE_FONT_PATH = os.getenv('JAPANESE_FONT_PATH')

    REGEX_HIRAGANA_KATAKANA = regex.compile(r'[\p{Script=Hiragana}\p{Script=Katakana}ーa-z]+')
    REGEX_ALPHABETS = re.compile('[a-zA-Z0-9]+')

    def greeting_by_name(self, name):
        image_file_name = 'image.png'
        fontsize = 36

        canvas_size = (800, 180)
        background_color = (0, 0, 0)
        text_color = (255, 255, 255)
        strong_text_color = (255, 165, 0)

        img = PIL.Image.new('RGB', canvas_size, background_color)
        draw = PIL.ImageDraw.Draw(img)

        font_japanese = PIL.ImageFont.truetype(self.JAPANESE_FONT_PATH, fontsize)
        font_english = PIL.ImageFont.truetype(self.ENGLISH_FONT_PATH, fontsize)

        # x
        start_x = 20
        delta = 18
        pos_x = start_x
        # y
        line_1_y = 20
        line_space = 50

        for idx, c in enumerate(name):
            if self.REGEX_ALPHABETS.fullmatch(c):
                name_font = font_english
                delta = 18
                line_1_y = 10
            elif self.REGEX_HIRAGANA_KATAKANA.fullmatch(c):
                name_font = font_japanese
                delta = 28
                line_1_y = 20
            else:
                logger.info(f'invalid character found. name: {name} c: {c}')
                return ''

            #  logger.info(f'c: {c} name_font: {name_font}')
            pos_x = start_x + (delta * idx)
            draw.text((pos_x, line_1_y), c, fill=strong_text_color, font=name_font)
        draw.text((pos_x + delta + 10, 20), 'さん、', fill=text_color, font=font_japanese)
        draw.text((start_x, line_1_y + line_space), 'はじめましてでし！', fill=text_color,
                  font=font_japanese)
        draw.text((start_x, line_1_y + (line_space * 2)), 'まずはルールをよんでね。', fill=text_color,
                  font=font_japanese)

        img.save(image_file_name)

        return image_file_name
