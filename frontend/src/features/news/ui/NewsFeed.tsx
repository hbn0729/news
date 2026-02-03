import type { Article } from '../../../types'
import NewsCard from './NewsCard'

interface NewsFeedProps {
  articles: Article[]
  hasMore: boolean
  isLoadingMore: boolean
  onLoadMore: () => void
  onRead: (id: string) => void
  onStar: (id: string, isStarred: boolean) => void
}

export default function NewsFeed({
  articles,
  hasMore,
  isLoadingMore,
  onLoadMore,
  onRead,
  onStar,
}: NewsFeedProps) {
  return (
    <div className="divide-y bg-white">
      {articles.map((article) => (
        <NewsCard
          key={article.id}
          article={article}
          onRead={() => onRead(article.id)}
          onStar={() => onStar(article.id, article.isStarred)}
        />
      ))}

      {hasMore && (
        <div className="p-4 text-center">
          <button
            onClick={onLoadMore}
            disabled={isLoadingMore}
            className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50"
          >
            {isLoadingMore ? '加载中...' : '加载更多'}
          </button>
        </div>
      )}
    </div>
  )
}
