interface SourceBadgeProps {
  source: string
}

const SOURCE_CONFIG: Record<string, { name: string; color: string }> = {
  // AkShare 数据源
  eastmoney: { name: '东方财富', color: 'bg-red-100 text-red-700' },
  cls: { name: '财联社', color: 'bg-purple-100 text-purple-700' },
  cctv: { name: '央视财经', color: 'bg-red-100 text-red-800' },
  hot_rank: { name: '热门股票', color: 'bg-orange-100 text-orange-700' },

  // 实时快讯
  jin10: { name: '金十数据', color: 'bg-yellow-100 text-yellow-800' },
  wallstreet: { name: '华尔街见闻', color: 'bg-blue-100 text-blue-700' },
  gelonghui: { name: '格隆汇', color: 'bg-indigo-100 text-indigo-700' },

  // 国际
  gnews: { name: 'Google', color: 'bg-green-100 text-green-700' },
}

export default function SourceBadge({ source }: SourceBadgeProps) {
  const config = SOURCE_CONFIG[source] || {
    name: source,
    color: 'bg-gray-100 text-gray-700',
  }

  return (
    <span className={`px-2 py-0.5 rounded text-xs font-medium ${config.color}`}>
      {config.name}
    </span>
  )
}
