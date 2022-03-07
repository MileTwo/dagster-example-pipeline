from dagster import repository, ScheduleDefinition
from dagster.utils.yaml_utils import load_yaml_from_path

from dagster_example_pipeline.hacker_news_job_template import hacker_news
from dagster_example_pipeline.resources import hacker_news_fetcher

@repository
def hacker_news_repo():
    example_job_config = load_yaml_from_path('job_configs/hacker_news_config.yaml')
    top_hacker_news_job = hacker_news.to_job(name='top_hacker_news', resource_defs={
        'hacker_news': hacker_news_fetcher, 
        }, 
        config=example_job_config)
    basic_schedule = ScheduleDefinition(job=top_hacker_news_job, cron_schedule="5 0 * * *", execution_timezone="US/Eastern")
    return [top_hacker_news_job, basic_schedule]
