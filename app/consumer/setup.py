from app.consumer import jobs
from app.consumer.types import TaskHandler
from app.topics import Topics

TASKS: dict[Topics, TaskHandler] = {
    Topics.RECOMMENDATIONS_BUDGETS: jobs.consume_recommendation,
    Topics.RECOMMENDATIONS_BUDGETS_STATUS: jobs.consume_platform_status,
    Topics.GOALS_UPDATED: jobs.consume_goal_update,
}

TASKS_TOPICS = [topic.value for topic in TASKS]
