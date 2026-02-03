import { getSourceDisplayName } from '../../../shared/config/sources'
import type { SourceInfo } from '../../../types'

interface SourceFilterProps {
  value: string | null
  onChange: (value: string | null) => void
  options: SourceInfo[]
  isLoading?: boolean
  isError?: boolean
}

export default function SourceFilter({
  value,
  onChange,
  options,
  isLoading,
  isError,
}: SourceFilterProps) {
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
      {options.map((s) => (
        <option key={s.source} value={s.source}>
          {getSourceDisplayName(s.source)} ({s.count})
        </option>
      ))}
    </select>
  )
}
