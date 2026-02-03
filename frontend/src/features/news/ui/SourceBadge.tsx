import { getSourceBadgeClass, getSourceDisplayName } from '../../../shared/config/sources'

interface SourceBadgeProps {
  source: string
}

export default function SourceBadge({ source }: SourceBadgeProps) {
  const badgeClass = getSourceBadgeClass(source)
  const name = getSourceDisplayName(source)

  return (
    <span className={`px-2 py-0.5 rounded text-xs font-medium ${badgeClass}`}>
      {name}
    </span>
  )
}
