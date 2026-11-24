<template>
  <section class="page">
    <header class="page-head">
      <div>
        <h2>运营概览</h2>
        <p class="page-desc">汇总各业务模块的关键指标，先看总量再看异常。</p>
      </div>
    </header>
    <div class="stat-row">
      <article v-for="card in cards" :key="card.label" class="stat-card">
        <span class="stat-label">{{ card.label }}</span>
        <strong class="stat-value">{{ card.value }}</strong>
      </article>
    </div>
    <table class="data-table">
      <thead>
        <tr><th>业务模块</th><th>今日新增</th><th>待处理</th><th>异常量</th></tr>
      </thead>
      <tbody>
        <tr v-for="row in moduleRows" :key="row.name">
          <td>{{ row.name }}</td>
          <td>{{ row.created }}</td>
          <td>{{ row.pending }}</td>
          <td>{{ row.abnormal }}</td>
        </tr>
      </tbody>
    </table>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import { fetchJson } from '@/api/client'

type Overview = {
  cards: { label: string; value: number }[]
  modules: { name: string; created: number; pending: number; abnormal: number }[]
}

const cards = ref<Overview['cards']>([])
const moduleRows = ref<Overview['modules']>([])

onMounted(async () => {
  try {
    const payload = await fetchJson<Overview>('/api/overview')
    cards.value = payload.cards
    moduleRows.value = payload.modules
  } catch {
    cards.value = [{"label": "业务模块", "value": 0}, {"label": "今日新增", "value": 0}]
    moduleRows.value = [{"name": "评论站点目录", "created": 0, "pending": 0, "abnormal": 0}, {"name": "关键词种子池", "created": 0, "pending": 0, "abnormal": 0}, {"name": "评论抓取任务", "created": 0, "pending": 0, "abnormal": 0}, {"name": "页面快文摘取", "created": 0, "pending": 0, "abnormal": 0}, {"name": "评论解析器", "created": 0, "pending": 0, "abnormal": 0}, {"name": "评分归一", "created": 0, "pending": 0, "abnormal": 0}, {"name": "情感标注", "created": 0, "pending": 0, "abnormal": 0}, {"name": "评论去重", "created": 0, "pending": 0, "abnormal": 0}, {"name": "作者画像", "created": 0, "pending": 0, "abnormal": 0}, {"name": "口碑情感库", "created": 0, "pending": 0, "abnormal": 0}, {"name": "方面词抽取", "created": 0, "pending": 0, "abnormal": 0}, {"name": "投诉聚类", "created": 0, "pending": 0, "abnormal": 0}, {"name": "趋势统计", "created": 0, "pending": 0, "abnormal": 0}, {"name": "抓取配额", "created": 0, "pending": 0, "abnormal": 0}, {"name": "验证码闸口", "created": 0, "pending": 0, "abnormal": 0}, {"name": "失败重试队列", "created": 0, "pending": 0, "abnormal": 0}, {"name": "口碑导出中心", "created": 0, "pending": 0, "abnormal": 0}, {"name": "口碑报告", "created": 0, "pending": 0, "abnormal": 0}, {"name": "标注复核台", "created": 0, "pending": 0, "abnormal": 0}, {"name": "采集度量总览", "created": 0, "pending": 0, "abnormal": 0}]
  }
})
</script>
