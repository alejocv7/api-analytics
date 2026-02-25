from app.schemas.metric import PerformanceStatsMixin


def test_performance_stats_mixin_rounding():
    class TestStats(PerformanceStatsMixin):
        pass

    stats = TestStats(
        request_count=10,
        avg_response_time_ms=123.4567,
        error_count=1,
        slowest_request_ms=500.8888,
        fastest_request_ms=10.1111,
    )

    assert stats.avg_response_time_ms == 123.46
    assert stats.slowest_request_ms == 500.89
    assert stats.fastest_request_ms == 10.11
    assert stats.error_rate == 10.0


def test_performance_stats_mixin_zero_requests():
    class TestStats(PerformanceStatsMixin):
        pass

    stats = TestStats(request_count=0, error_count=0)
    assert stats.error_rate == 0.0


def test_performance_stats_mixin_all_errors():
    class TestStats(PerformanceStatsMixin):
        pass

    stats = TestStats(request_count=5, error_count=5)
    assert stats.error_rate == 100.0
