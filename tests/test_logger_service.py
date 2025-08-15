from services.logger_service import LoggerService
import pytest
from models.custom_exceptions import APPException
from services.handlers.processing_result import ProcessingResult


@pytest.fixture
def mocked_logger():
    return LoggerService()


@pytest.fixture
def mocked_app_exception():
    return APPException(
        message="exception",
        service_name="service",
        params={},
        event_type="event",
        ex_class="class",
    )


@pytest.fixture
def processing_result():
    return ProcessingResult(is_success=True, event_type='user_created', execution_time=2.3)


def test_logger_service(mocked_logger, mocked_app_exception, processing_result):
    mocked_logger.log_error(exception=mocked_app_exception)
    mocked_logger.log_info(processing_result=processing_result)
    mocked_logger.log_model('data',extra_name='process_result',model=processing_result)
