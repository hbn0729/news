import { useCategories } from '../hooks/useNews'

interface CategoryFilterProps {
  value: string | null
  onChange: (value: string | null) => void
}

export default function CategoryFilter({ value, onChange }: CategoryFilterProps) {
  const { data: categories = [], isLoading, isError } = useCategories()

  return (
    <select
      value={value || ''}
      onChange={(e) => onChange(e.target.value || null)}
      className="px-3 py-1 border rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
      aria-label="按分类筛选"
      disabled={isLoading}
    >
      <option value="">
        {isLoading ? '加载中...' : isError ? '加载失败' : '全部分类'}
      </option>
      {categories.map((c) => (
        <option key={c.category} value={c.category}>
          {c.category} ({c.count})
        </option>
      ))}
    </select>
  )
}
