import os
from pathlib import Path

import pandas as pd
import requests
from dagster import Field, resource


class APIFetcher:
    def __init__(self) -> None:
        pass

    def fetch_content(self, context):
        raise NotImplementedError()


class HackerNewsFetcher(APIFetcher):
    def __init__(self, endpoint='https://hacker-news.firebaseio.com/v0/') -> None:
        self.endpoint = endpoint

    def _fetch_top_stories(self, context, top_stories=5):
        assert top_stories > 0
        topstories_endpoint = os.path.join(self.endpoint, 'topstories.json')
        
        context.log.info(f"Retrieving IDs for top stories from: {topstories_endpoint}")
        response = requests.get(topstories_endpoint)
        
        def _get_item(content_id):
            item_endpoint = os.path.join(self.endpoint, 'item', f"{content_id}.json")
            item = requests.get(item_endpoint).json()
            return item
        
        items = [_get_item(content_id) for content_id in response.json()[:top_stories]]
        # fetching items as a one-liner
        # items = [requests.get(os.path.join(self.endpoint, 'item', f"{content_id}.json")).json() for content_id in response.json()[:top_stories]]
        
        df = pd.concat(pd.json_normalize(item) for item in items)
        return df

    def fetch_content(self, context) -> pd.DataFrame:
        return self._fetch_top_stories(context)


class LocalHackerNewsFetcher(APIFetcher):
    def __init__(self, path=None) -> None:
        self.path = Path(path) if path else Path("data") / "dag" / "cache" / "cached_raw.snappy.parquet"

    def fetch_content(self, context) -> pd.DataFrame:
        context.log.info("Loading from file instead of API! For debugging purposes only!")
        df = pd.read_parquet(self.path)
        return df


@resource(config_schema={
    "endpoint": Field(str, is_required=False, default_value='https://hacker-news.firebaseio.com/v0/'),
    })
def hacker_news_fetcher(init_context):
    return HackerNewsFetcher(endpoint=init_context.resource_config['endpoint'])


@resource(config_schema={
    "path": Field(str, is_required=False, default_value='')
})
def local_hacker_news_fetcher(init_context):
    return LocalHackerNewsFetcher(path=init_context.resource_config['path'])
