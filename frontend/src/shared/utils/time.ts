export function formatRelativeTime(date: Date): string {
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffSeconds = Math.floor(diffMs / 1000)
  const diffMinutes = Math.floor(diffSeconds / 60)
  const diffHours = Math.floor(diffMinutes / 60)
  const diffDays = Math.floor(diffHours / 24)

  if (diffMs < 0) {
    const absDiffMinutes = Math.abs(diffMinutes)
    if (absDiffMinutes <= 60) {
      return '刚刚'
    } else {
      const year = date.getFullYear()
      const month = String(date.getMonth() + 1).padStart(2, '0')
      const day = String(date.getDate()).padStart(2, '0')
      return `${year}-${month}-${day}`
    }
  }

  if (diffMinutes < 1) {
    return '刚刚'
  }

  if (diffHours < 1) {
    return `${diffMinutes}分钟前`
  }

  if (diffDays < 1) {
    return `${diffHours}小时前`
  }

  if (diffDays < 30) {
    return `${diffDays}天前`
  }

  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}
