import json
import os
import pandas as pd
import requests
import asyncio
from concurrent.futures import ThreadPoolExecutor
import nest_asyncio


class Scraper():

    def __init__(self,url, zip_range=[1000,10000]):
        self.url = url
        self.parameters = {
            "page": 0,
            "zipcodeFrom":zip_range[0],
            "zipcodeTo":zip_range[1]
        }
        nest_asyncio.apply()

    def fetch(self,session, idx):
        parameters = self.parameters
        parameters["page"] = idx
        with session.get(self.url, params=parameters) as response:
            #data = response.text
            data = pd.DataFrame(response.json()['results'])
            if response.status_code != 200:
                print("FAILURE::{0}".format(self.url))
            
            print("success at index " + str(idx))
            return data

    async def get_data_asynchronous(self,url_range):
        results = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            with requests.Session() as session:
                # Set any session parameters here before calling `fetch`
                loop = asyncio.get_event_loop()
                tasks = [
                    loop.run_in_executor(
                        executor,
                        self.fetch,
                        *(session, idx) # Allows us to pass in multiple arguments to `fetch`
                    )
                    for idx in url_range
                ]
                for response in await asyncio.gather(*tasks):
                    results.append(response)

        return results

    def test_fetch(self):
        return self.fetch(requests.Session(),"1")

    def get_data_in_range(self,url_range):
        loop = asyncio.get_event_loop()
        future = asyncio.ensure_future(self.get_data_asynchronous(url_range))
        res_as_list = loop.run_until_complete(future)
        res_as_data_frame = pd.concat(res_as_list)

        return res_as_data_frame

    
def get_historic_sales(loop_range = range(1,100), zip_range = None):
    base_url = "https://api.boliga.dk/api/v2/sold/search/results"

    return Scraper(base_url, zip_range=zip_range).get_data_in_range(loop_range)

def get_current_sales(loop_range = range(1,100), zip_range = None):
    base_url = "https://api.boliga.dk/api/v2/search/results"
    
    return Scraper(base_url, zip_range=zip_range).get_data_in_range(loop_range)
