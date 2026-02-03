const DEFAULT_SOURCE_BADGE_CLASS = 'bg-gray-100 text-gray-700'

const SOURCE_REGISTRY: Record<string, { name: string; badgeClass: string }> = {
  eastmoney: { name: '东方财富', badgeClass: 'bg-red-100 text-red-700' },
  cls: { name: '财联社', badgeClass: 'bg-purple-100 text-purple-700' },
  cctv: { name: '央视财经', badgeClass: 'bg-red-100 text-red-800' },
  hot_rank: { name: '热门股票', badgeClass: 'bg-orange-100 text-orange-700' },
  jin10: { name: '金十数据', badgeClass: 'bg-yellow-100 text-yellow-800' },
  wallstreet: { name: '华尔街见闻', badgeClass: 'bg-blue-100 text-blue-700' },
  gelonghui: { name: '格隆汇', badgeClass: 'bg-indigo-100 text-indigo-700' },
  gnews: { name: 'Google', badgeClass: 'bg-green-100 text-green-700' },
  itjuzi: { name: 'IT桔子', badgeClass: 'bg-emerald-100 text-emerald-700' },
}

export function getSourceDisplayName(source: string) {
  return SOURCE_REGISTRY[source]?.name ?? source
}

export function getSourceBadgeClass(source: string) {
  return SOURCE_REGISTRY[source]?.badgeClass ?? DEFAULT_SOURCE_BADGE_CLASS
}
