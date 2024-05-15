import logging
import os
import re
import requests

from datetime import datetime as dt
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger('discord')


class StageImageCreator:
    ENGLISH_FONT_PATH = os.getenv('ENGLISH_FONT_PATH')
    JAPANESE_FONT_PATH = os.getenv('JAPANESE_FONT_PATH')

    FONT_JAPANESE = None
    FONT_ENGLISH = None

    PATTERN_KATAKANA = re.compile('[ア-ンー]+')
    PATTERN_KANA = re.compile('[ア-ンあ-んー・]+')

    def __init__(self):
        self.FONT_JAPANESE = self.load_font(self.JAPANESE_FONT_PATH)
        self.FONT_ENGLISH = self.load_font(self.ENGLISH_FONT_PATH)

    def run(self):
        logger.info('fetching stages...')
        stages = self.fetch_stages()

        logger.info('filtering stages...')
        filtered = self.filter_recent(stages)

        logger.info('creating image...')
        created_img = self.make_stages_image(filtered)

        if created_img is None:
            logger.info('no image created. maybe all fest.')
            return None

        logger.info('saving image...')
        current_time = dt.now().strftime('%Y%m%d%H')
        save_to = f'{current_time}.png'
        created_img.save(save_to)

        return save_to

    @staticmethod
    def fetch_stages():
        url = 'https://spla3.yuu26.com/api/schedule'
        response = requests.get(url)

        return response.json()

    @staticmethod
    def filter_recent(stages):
        current = dt.now()
        filtered = {}
        for k, v in stages['result'].items():
            filtered[k] = []
            for i, d in enumerate(v):
                if i > 3:
                    break
                start = dt.strptime(d['start_time'], '%Y-%m-%dT%H:%M:%S+09:00')
                if start.date() != current.date():
                    continue
                filtered[k].append(d)

        return filtered

    def load_font(self, path=JAPANESE_FONT_PATH, font_size=50):
        logger.info(f'loading font. path: {path} font_size: {font_size}')
        return ImageFont.truetype(path, font_size)

    @staticmethod
    def get_background_img(suffix=''):
        if suffix == '':
            image_name = 'discord_bg.png'
        else:
            image_name = f'discord_bg_{suffix}.png'

        background_img = f'bukichi_bot/assets/img/{image_name}'
        try:
            return Image.open(background_img)
        except FileNotFoundError:
            logger.info(f'file not found. {background_img}')
            return None

    @staticmethod
    def resize_image(img, size_delta=1.5, fixed_width=None, fixed_height=None):
        if fixed_width is None:
            width = round(img.width * size_delta)
        else:
            width = fixed_width

        if fixed_height is None:
            height = round(img.height * size_delta)
        else:
            height = fixed_height

        return img.resize((width, height))

    def download_stage_image(self, save_to, image_url, size_delta=1.5, fixed_width=None, fixed_height=None):
        logger.info(f'downloading image. save_to: {save_to} image_url: {image_url}')
        response = requests.get(image_url, stream=True)
        with open(save_to, 'wb') as f:
            f.write(response.content)

        return self.resize_image(Image.open(save_to), size_delta, fixed_width, fixed_height)

    def append_stage_image(self, background_img, draw, pos_x, pos_y, data):
        if data['stages'] is None or data['rule'] is None:
            return

        text_color = (255, 255, 255)

        rule_name = data['rule']['name']

        # add event time
        start_at = dt.strftime(dt.strptime(data['start_time'], '%Y-%m-%dT%H:%M:%S+09:00'), '%H')
        end_at = dt.strftime(dt.strptime(data['end_time'], '%Y-%m-%dT%H:%M:%S+09:00'), '%H')

        draw.text((pos_x + 8, pos_y - 60), f'{rule_name}({start_at}-{end_at})', fill=text_color,
                  font=self.FONT_JAPANESE)

        for number, stage in enumerate(data['stages']):
            delta_y = 310 * number
            stage_name = stage['name']

            save_to = f"{stage_name}.png"
            save_to = save_to.replace('/', '_')

            stage_img = self.download_stage_image(save_to, stage['image'])

            # add stage image
            background_img.paste(stage_img, (pos_x, pos_y + delta_y))

            # add stage name
            stage_name_kana = self.PATTERN_KATAKANA.findall(stage_name)
            if len(stage_name_kana) == 0:
                stage_name_kana = ''
            else:
                stage_name_kana = ''.join(stage_name_kana).replace('ー', '-')
            draw.text((pos_x + 16, pos_y + 232 + delta_y), stage_name_kana, fill=text_color,
                      font=self.FONT_JAPANESE)

    @staticmethod
    def check_if_is_all_fest(filtered):
        for k, v in filtered.items():
            for d in v:
                if d['is_fest'] is False:
                    return False
        return True

    # def append_rule_name(self, draw, pos_x, pos_y, data):
    #    if data is None or data['rule'] is None:
    #        return

    #    text_color = (255, 255, 255)

    #    rule = data['rule']['name']
    #    logger.info(rule)
    #    draw.text((pos_x + 8, pos_y - 100), rule, fill=text_color, font=self.FONT_JAPANESE)

    def make_stages_image(self, filtered):
        if self.check_if_is_all_fest(filtered):
            return None

        background_img = self.get_background_img()
        draw = ImageDraw.Draw(background_img)

        pos_x = 100
        pos_y = 0

        cursor = ''
        for k, v in filtered.items():
            # logger.info(k)
            if k != cursor:
                logger.info(f'processing stage info. current mode: {k}')
                cursor = k
                pos_x = 100
                # initial position
                if pos_y == 0:
                    pos_y = 200
                else:
                    pos_y += 780

            for d in v:
                # self.append_rule_name(background_img, draw, pos_x, pos_y, d)
                self.append_stage_image(background_img, draw, pos_x, pos_y, d)
                pos_x += 730

        return background_img
