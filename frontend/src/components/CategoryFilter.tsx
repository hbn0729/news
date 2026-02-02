import { useCategories } from '../hooks/useNews'

interface CategoryFilterProps {
  value: string | null
  onChange: (value: string | null) => void
}

// Category grouping configuration
const DOMESTIC_CATEGORIES = ['科技', '股市', '财经', '快讯', '创投']
const INTERNATIONAL_CATEGORIES = ['美股', '国际']

export default function CategoryFilter({ value, onChange }: CategoryFilterProps) {
  const { data: categories = [], isLoading, isError } = useCategories()

  // Group categories
  const domesticCategories = categories.filter((c) =>
    DOMESTIC_CATEGORIES.includes(c.category)
  )
  const internationalCategories = categories.filter((c) =>
    INTERNATIONAL_CATEGORIES.includes(c.category)
  )
  const otherCategories = categories.filter(
    (c) =>
      !DOMESTIC_CATEGORIES.includes(c.category) &&
      !INTERNATIONAL_CATEGORIES.includes(c.category)
  )

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

      {domesticCategories.length > 0 && (
        <optgroup label="国内">
          {domesticCategories.map((c) => (
            <option key={c.category} value={c.category}>
              {c.category} ({c.count})
            </option>
          ))}
        </optgroup>
      )}

      {internationalCategories.length > 0 && (
        <optgroup label="国际">
          {internationalCategories.map((c) => (
            <option key={c.category} value={c.category}>
              {c.category} ({c.count})
            </option>
          ))}
        </optgroup>
      )}

      {otherCategories.length > 0 && (
        <optgroup label="其他">
          {otherCategories.map((c) => (
            <option key={c.category} value={c.category}>
              {c.category} ({c.count})
            </option>
          ))}
        </optgroup>
      )}
    </select>
  )
}
