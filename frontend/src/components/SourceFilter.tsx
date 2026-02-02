import { useSources } from '../hooks/useNews'

interface SourceFilterProps {
  value: string | null
  onChange: (value: string | null) => void
}

const SOURCE_NAMES: Record<string, string> = {
  eastmoney: '东方财富',
  cls: '财联社',
  jin10: '金十数据',
  wallstreet: '华尔街见闻',
}

export default function SourceFilter({ value, onChange }: SourceFilterProps) {
  const { data: sources = [], isLoading, isError } = useSources()

  return (
    <select
      value={value || ''}
      onChange={(e) => onChange(e.target.value || null)}
      className="px-3 py-1 border rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
      aria-label="按来源筛选"
      disabled={isLoading}
    >
      <option value="">
        {isLoading ? '加载中...' : isError ? '加载失败' : '全部来源'}
      </option>
      {sources.map((s) => (
        <option key={s.source} value={s.source}>
          {SOURCE_NAMES[s.source] || s.source} ({s.count})
        </option>
      ))}
    </select>
  )
}
