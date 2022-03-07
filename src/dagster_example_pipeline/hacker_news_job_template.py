import os
from datetime import date

import pandas as pd
import requests
from dagster import op, graph, Out, In, Output, Nothing


@op(required_resource_keys={'hacker_news'}, out={'items': Out(pd.DataFrame, is_required=False), 'empty': Out(Nothing, is_required=False)})
def fetch_hacker_news_data(context):
    df = context.resources.hacker_news.fetch_content(context)
    context.log.info(f"Fetched {len(df)} items")
    if len(df):
        yield Output(df.reset_index(drop=True), 'items')
    else:
        yield Output(None, output_name='empty')
    

def _post_to_slack(context, data=None):
    data = data or {'text': f"No new Hacker News found for {date.today().strftime('%b %d, %Y')}"}
    slack_hook = os.environ.get('SLACK_HOOK')
    if slack_hook is None:
        context.log.warning("Environment variable **`SLACK_HOOK`** not specified. Logging to console only!")
        context.log.info(f"===Begin Message===\n{data}\n===End of Message===")
        return None
    else:
        return requests.post(slack_hook, json=data)


@op(ins={'empty': In(Nothing)})
def post_empty_to_slack(context):
    return _post_to_slack(context, data=None)


@op
def filter_columns(df: pd.DataFrame) -> pd.DataFrame:
    desired_columns = [
        'title',
        'score',
        'url',
        'by',
        'id',
    ]

    df = df[desired_columns]
    df['url'] = df['url'].astype(str)
    return df


@op
def add_metadata(context, df: pd.DataFrame) -> pd.DataFrame:
    df['metadata_run_id'] = context.run_id
    df['metadata_run_date'] = pd.to_datetime('today').normalize()
    return df


@op
def share_hacker_news(context, df: pd.DataFrame):
    def _build_slack_message():
        intro = f"Here are the top {len(df)} items for Hacker News from today\n\n"

        items = []
        for index, row in df.iterrows():
            bullet_point = f"{index+1}."

            title_link = row['url'] if row['url'] != 'nan' else f"https://news.ycombinator.com/item?id={row['id']}"
            clickable_title = f"<{title_link}|{row['title']}>"

            items.append(f"{bullet_point}\t{clickable_title} -- {row['by']} ({row['score']} points)")

        message = intro + '\n'.join(items)
        return message

    data = {"text": _build_slack_message()} if len(df) else None
    return _post_to_slack(context, data)

@graph
def hacker_news():
    result, empty = fetch_hacker_news_data()

    # Successful API call, no items
    no_api_results = post_empty_to_slack(empty)

    # Successful API call, retrieved items
    result = filter_columns(result)
    result = add_metadata(result)
    result = share_hacker_news(result)
