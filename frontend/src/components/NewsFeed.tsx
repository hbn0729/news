import type { Article } from '../types'
import { useUpdateArticle } from '../hooks/useArticle'
import NewsCard from './NewsCard'

interface NewsFeedProps {
  articles: Article[]
  hasMore: boolean
  isLoadingMore: boolean
  onLoadMore: () => void
}

export default function NewsFeed({
  articles,
  hasMore,
  isLoadingMore,
  onLoadMore,
}: NewsFeedProps) {
  const updateArticle = useUpdateArticle()

  const handleRead = (id: string) => {
    updateArticle.mutate({ id, update: { is_read: true } })
  }

  const handleStar = (id: string, isStarred: boolean) => {
    updateArticle.mutate({ id, update: { is_starred: !isStarred } })
  }

  return (
    <div className="divide-y bg-white">
      {articles.map((article) => (
        <NewsCard
          key={article.id}
          article={article}
          onRead={() => handleRead(article.id)}
          onStar={() => handleStar(article.id, article.is_starred)}
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
