<template>
  <div class="app-shell">
    <aside class="app-side">
      <h1 class="app-title">商品评论采集与口碑洞察平台</h1>
      <nav class="nav-list">
        <RouterLink v-for="item in navItems" :key="item.path" :to="item.path" class="nav-item">
          {{ item.label }}
        </RouterLink>
      </nav>
    </aside>
    <main class="app-main">
      <header class="app-head">
        <span class="head-desc">抓取多站点商品评论，解析归一评分与情感，去重建档后形成口碑趋势与报告的数据采集与口碑分析平台</span>
        <span class="head-user">当前值班：数据工程组</span>
      </header>
      <RouterView />
    </main>
  </div>
</template>

<script setup lang="ts">
const navItems = [{ label: "运营概览", path: "/" }, { label: "评论站点目录", path: "/review_site" }, { label: "关键词种子池", path: "/seed_keyword" }, { label: "评论抓取任务", path: "/review_crawl" }, { label: "页面快文摘取", path: "/page_digest" }, { label: "评论解析器", path: "/review_parse" }, { label: "评分归一", path: "/rating_norm" }, { label: "情感标注", path: "/sentiment_label" }, { label: "评论去重", path: "/review_dedup" }, { label: "作者画像", path: "/author_profile" }, { label: "口碑情感库", path: "/review_sentiment_store" }, { label: "方面词抽取", path: "/aspect_extract" }, { label: "投诉聚类", path: "/complaint_cluster" }, { label: "趋势统计", path: "/trend_stat" }, { label: "抓取配额", path: "/crawl_quota" }, { label: "验证码闸口", path: "/captcha_gate" }, { label: "失败重试队列", path: "/crawl_retry" }, { label: "口碑导出中心", path: "/review_export" }, { label: "口碑报告", path: "/opinion_report" }, { label: "标注复核台", path: "/sentiment_review" }, { label: "采集度量总览", path: "/platform_metrics" }]
</script>
