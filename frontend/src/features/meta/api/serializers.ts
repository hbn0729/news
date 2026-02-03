import type { Stats, StatsDTO } from '../../../types'

export function mapStatsDtoToStats(dto: StatsDTO): Stats {
  return {
    totalArticles: dto.total_articles,
    unread: dto.unread,
    starred: dto.starred,
    filtered: dto.filtered,
  }
}
