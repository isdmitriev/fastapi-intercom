from prometheus_client import Histogram, Counter, Gauge

USER_REPLIED_DURATION = Histogram(name='user_replied_handler_duration', documentation='duration user replied',
                                  buckets=[1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0],labelnames=['pod_name'])
ADMIN_NOTED_DURATION = Histogram(name='admin_noted_handler_duration', documentation='duration admin noted',
                                 buckets=[1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0],labelnames=['pod_name'])
USER_CREATED_DURATION = Histogram(name='user_created_handler_duration', documentation='duration user created',
                                  buckets=[0.0,0.1,0.2,0.5, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0],labelnames=['pod_name'])

SUCCESS_REQUEST_COUNT = Counter(name='success_request_count',labelnames=['pod_name'], documentation='succes request count')
FAILED_REQUEST_COUNT = Counter(name='failed_request_count',labelnames=['pod_name'], documentation='failed request count')
APP_MEMORY_USAGE = Gauge(name='app_memory_usage',labelnames=['pod_name'], documentation='app memory usage in mb')
