/**
 * 统一的时间格式化工具函数
 * 将所有相对时间统一格式为：
 * - x分钟前 (< 1小时)
 * - x小时前 (< 24小时)
 * - x天前 (< 30天)
 * - YYYY-MM-DD (>= 30天)
 */

export function formatRelativeTime(date: Date): string {
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffSeconds = Math.floor(diffMs / 1000)
  const diffMinutes = Math.floor(diffSeconds / 60)
  const diffHours = Math.floor(diffMinutes / 60)
  const diffDays = Math.floor(diffHours / 24)

  // 处理未来时间：如果发布时间在未来，当作刚刚发布（可能是数据源时间错误）
  // 但如果未来时间超过1小时，显示具体日期以提示异常
  if (diffMs < 0) {
    const absDiffMinutes = Math.abs(diffMinutes)
    if (absDiffMinutes <= 60) {
      // 未来1小时内：当作刚刚（可能是时区或时间同步问题）
      return '刚刚'
    } else {
      // 未来超过1小时：显示具体日期，提示数据异常
      const year = date.getFullYear()
      const month = String(date.getMonth() + 1).padStart(2, '0')
      const day = String(date.getDate()).padStart(2, '0')
      return `${year}-${month}-${day}`
    }
  }

  // 小于1分钟：刚刚
  if (diffMinutes < 1) {
    return '刚刚'
  }

  // 小于1小时：x分钟前
  if (diffHours < 1) {
    return `${diffMinutes}分钟前`
  }

  // 小于24小时：x小时前
  if (diffDays < 1) {
    return `${diffHours}小时前`
  }

  // 小于30天：x天前
  if (diffDays < 30) {
    return `${diffDays}天前`
  }

  // 大于等于30天：显示具体日期 YYYY-MM-DD
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}


