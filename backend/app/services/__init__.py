"""领域服务注册表：通用资源路由按模块 key 分派到独立业务服务。"""
from __future__ import annotations

from app.services.base import BaseModuleService
from app.services.review_site import ReviewSiteService
from app.services.seed_keyword import SeedKeywordService
from app.services.review_crawl import ReviewCrawlService
from app.services.page_digest import PageDigestService
from app.services.review_parse import ReviewParseService
from app.services.rating_norm import RatingNormService
from app.services.sentiment_label import SentimentLabelService
from app.services.review_dedup import ReviewDedupService
from app.services.author_profile import AuthorProfileService
from app.services.review_sentiment_store import ReviewSentimentStoreService
from app.services.aspect_extract import AspectExtractService
from app.services.complaint_cluster import ComplaintClusterService
from app.services.trend_stat import TrendStatService
from app.services.crawl_quota import CrawlQuotaService
from app.services.captcha_gate import CaptchaGateService
from app.services.crawl_retry import CrawlRetryService
from app.services.review_export import ReviewExportService
from app.services.opinion_report import OpinionReportService
from app.services.sentiment_review import SentimentReviewService
from app.services.platform_metrics import PlatformMetricsService

SERVICES: dict[str, BaseModuleService] = {
    "review_site": ReviewSiteService(),
    "seed_keyword": SeedKeywordService(),
    "review_crawl": ReviewCrawlService(),
    "page_digest": PageDigestService(),
    "review_parse": ReviewParseService(),
    "rating_norm": RatingNormService(),
    "sentiment_label": SentimentLabelService(),
    "review_dedup": ReviewDedupService(),
    "author_profile": AuthorProfileService(),
    "review_sentiment_store": ReviewSentimentStoreService(),
    "aspect_extract": AspectExtractService(),
    "complaint_cluster": ComplaintClusterService(),
    "trend_stat": TrendStatService(),
    "crawl_quota": CrawlQuotaService(),
    "captcha_gate": CaptchaGateService(),
    "crawl_retry": CrawlRetryService(),
    "review_export": ReviewExportService(),
    "opinion_report": OpinionReportService(),
    "sentiment_review": SentimentReviewService(),
    "platform_metrics": PlatformMetricsService(),
}


def service_for(module: str) -> BaseModuleService | None:
    return SERVICES.get(module)
