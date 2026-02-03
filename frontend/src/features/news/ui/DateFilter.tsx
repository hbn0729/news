interface DateFilterProps {
  value: string | null
  onChange: (value: string | null) => void
}

export default function DateFilter({ value, onChange }: DateFilterProps) {
  return (
    <div className="flex items-center gap-2">
      <input
        type="date"
        value={value || ''}
        onChange={(e) => onChange(e.target.value || null)}
        className="px-3 py-1 border rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
        aria-label="按日期筛选"
      />
      {value ? (
        <button
          type="button"
          onClick={() => onChange(null)}
          className="px-2 py-1 rounded-lg text-sm bg-gray-100 text-gray-600 hover:bg-gray-200"
        >
          清空
        </button>
      ) : null}
    </div>
  )
}
