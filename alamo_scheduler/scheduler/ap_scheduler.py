"""
Demonstrates how to use the Tornado compatible scheduler
to schedule a job that executes on 3 second intervals.
"""

from datetime import datetime
import asyncio
import os

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from alamo_scheduler.fixtures.checks import load_data_to_memory, SAMPLE_QUERY


def tick(check, test):
    if 'check_{}'.format(test) == check['name']:
        print('{} Tick! Interval is: {}. The time is: {}'.
              format(check['name'], check['interval'], datetime.now()))


def update_check(scheduler, checks):
    # TODO Check if update flag is set in cache,
    # Update check definitions if needed
    # 1. check cache update flag
    # 2. udpate checks if needed
    # 3. update or create new job
    # OR
    # scheduler.shutdown()
    # run_scheduler(checks)
    check_id = 2900
    new_job = {
        "name": "new_check_{}".format(check_id),
        "interval": 1,
        "type": "kairosdb",
        "query": SAMPLE_QUERY,
        "debounce": 10,
        "tags": {"tag1": "value1", "tag2": "value2", "tag3": "value3"},
        "threshold_value": 300 + check_id,
        "operator": ">",
        "severity": "warning",
        "integration_key": "some_unique_key_{}".format(check_id),
        "last_run": datetime.timestamp(datetime.now()),
    }
    job = scheduler.get_job('2900')
    print(job)
    scheduler.modify_job('2900', kwargs={"check": new_job, "test": 2900})
    # scheduler.print_jobs()
    print("Updating")


def run_scheduler(checks):
    scheduler = AsyncIOScheduler()
    scheduler.add_job(update_check, 'interval', seconds=10,
                      kwargs={"scheduler": scheduler, "checks": checks})
    for k, v in checks.items():
        scheduler.add_job(tick, 'interval', seconds=v['interval'],
                          max_instances=10,
                          id=str(k),
                          kwargs={"check": v, "test": 2900})
    scheduler.start()
    print('Press Ctrl+{0} to exit'.format('Break' if os.name == 'nt' else 'C'))

    # Execution will block here until Ctrl+C is pressed.
    try:
        asyncio.get_event_loop().run_forever()
    except (KeyboardInterrupt, SystemExit):
        pass

if __name__ == '__main__':
    checks = load_data_to_memory(3000)
    run_scheduler(checks)
