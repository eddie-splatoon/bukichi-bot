import json
import pytest

from bukichi_bot.components.salmon_run_stage_image_creator import SalmonRunStageImageCreator
from bukichi_bot.components.splatoon3_api_client import Splatoon3ApiClient


@pytest.mark.asyncio
async def test_salmon_run_stage_image_creator__run():
    stages = read_json()
    creator = SalmonRunStageImageCreator()
    assert await creator.run(stages) == '2024050201.png'

def test_salmon_run_stage_image_creator():
    creator = SalmonRunStageImageCreator()
    assert creator.to_datetime('2024-05-02T11:00:00+09:00') == '2024/05/02 11:00'


def read_json():
    with open('tests/json/salmon_run_stage_info.json') as f:
        return json.load(f)
