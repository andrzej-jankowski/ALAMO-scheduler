CHECK_TEST_DATA = {
    'id': 982,
    'uuid': 'e2e1ec23-707a-4382-a956-f0cf3276a1b8',
    'name': 'foo bar',
    'environment': 'test',
    'entity_id': '888',
    'entity_name': 'bububu',
    'tags': ['tag1', 'tag2', 'tag3'],
    'timestamp': 1454062612.609237,
    'type': 'graphite',
    'execution_time': '2016-01-29T11:25:56.517142+00:00',
    'integration_key': 'e80e141bb9a2406f9a865dd6077ea6cdaaaa',
    'description': None,
    'scheduled_time': '2016-01-29T11:25:56.430372+00:00',
    'service_id': '999',
    'service_name': 'foo-bar-test',
    'triggers': [{
        'severity': 'CRITICAL',
        'name': 'foo bar: critical',
        'tags': [],
        'threshold': '15',
        'result': {'status': 0, 'message': ''},
        'enabled': True,
        'uuid': 'e2e1ec23-707a-4382-a956-f0cf3276a1b8',
        'url': 'http://example.com/'
               '#/999/entity/888/check/982/?triggerId=2492',
        'id': 2492, 'condition': '<',
        'meta': {'links': {
            "trigger_url": {
                "type": "link",
                "href": "http://example.com/"
                        "#/999/entity/888/check/982/?triggerId=2492"
            }
        }}
    }],
    'fields': {
        'frequency': 60,
        'target': 'stats.tech.foo.bar.test.metrics',
        'debounce': '2',
        '_template_name': 'test checks',
        '_template_version': '1',
        'expected_num_hosts': '0',
        '_checksum': 'e10fc40'
    },
}
