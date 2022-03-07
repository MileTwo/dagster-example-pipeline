import pandas as pd
from dagster import ExecuteInProcessResult
from dagster_example_pipeline.hacker_news_job_template import hacker_news
from dagster_example_pipeline.resources import APIFetcher


class MockHackerNewsFetcher(APIFetcher):
    def fetch_content(self, context):

        records = [
            {'title': f"Title {i}", 'score': i + 10, 'url': 'https://www.miletwo.us/', 'by': 'aservice@miletwo.us', 'id': i}
            for i in range(5)
            ]
        df = pd.DataFrame.from_records(records)
        return df

def test_job():
    result = hacker_news.execute_in_process(
        resources={'hacker_news': MockHackerNewsFetcher()}
    )

    # return type is ExecuteInProcessResult
    assert isinstance(result, ExecuteInProcessResult)
    assert result.success
    # inspect individual op result
    assert isinstance(result.output_for_node("filter_columns"), pd.DataFrame)
    assert isinstance(result.output_for_node("add_metadata"), pd.DataFrame)