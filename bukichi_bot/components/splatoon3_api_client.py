import requests


class Splatoon3ApiClient():
    @staticmethod
    async def fetch_salmon_run_stages():
        url = 'https://spla3.yuu26.com/api/coop-grouping/schedule'
        response = requests.get(url)

        return response.json()
