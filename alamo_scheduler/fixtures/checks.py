from datetime import datetime
from random import randint

SAMPLE_QUERY = {
    "metrics": [
        {
            "tags": {"host": "example.com", "domain": "tech", "context": "test"},
            "name": "kairosdb.datastore.cassandra.key_query_time",
            "group_by": [
                {
                    "name": "tag",
                    "tags": [
                        "query_index"
                    ]
                }
            ],
            "aggregators": [
                {
                    "name": "sum",
                    "align_sampling": True,
                    "sampling": {
                        "value": "1",
                        "unit": "seconds"
                    }
                }
            ]
        }
    ],
    "cache_time": 0,
    "start_relative": {
        "value": "1",
        "unit": "hours"
    }
}

def generate_check_def(check_id, interval=1):
    data = {
            "name": "check_{}".format(check_id),
            "interval": interval,
            "type": "kairosdb",
            "query": SAMPLE_QUERY,
            "debounce": 1,
            "tags": {"tag1": "value1", "tag2": "value2", "tag3": "value3"},
            "threshold_value": 100 + check_id,
            "operator": ">",
            "severity": "warning",
            "integration_key": "some_unique_key_{}".format(check_id),
            "last_run": datetime.timestamp(datetime.now()),
    }
    return data

def load_data_to_memory(nr_of_checks=1000):
    checks = dict( (i, generate_check_def(i, randint(1,10))) for i in range(1, nr_of_checks) )
    return checks
