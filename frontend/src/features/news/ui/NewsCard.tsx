import type { Article } from '../../../types'
import { formatRelativeTime } from '../../../shared/utils/time'
import { getArticleHref } from '../../../shared/rules/articleLink'
import SourceBadge from './SourceBadge'

interface NewsCardProps {
  article: Article
  onRead: () => void
  onStar: () => void
}

export default function NewsCard({ article, onRead, onStar }: NewsCardProps) {
  const publishedAt = new Date(article.publishedAt)
  const relativeTime = formatRelativeTime(publishedAt)

  return (
    <article
      className={`p-4 hover:bg-gray-50 transition-colors ${
        article.isRead ? 'opacity-60' : ''
      }`}
    >
      <div className="flex items-start gap-3">
        <div className="flex-1 min-w-0">
          <h3 className="font-medium text-lg leading-tight">
            <a
              href={getArticleHref(article)}
              target="_blank"
              rel="noopener noreferrer"
              onClick={onRead}
              className="hover:text-blue-600"
            >
              {article.title}
            </a>
          </h3>

          <div className="flex items-center gap-2 mt-1 text-sm text-gray-500 flex-wrap">
            <SourceBadge source={article.source} />
            <span>{relativeTime}</span>
          </div>

          {article.summary && (
            <p className="mt-2 text-gray-600 text-sm line-clamp-2">
              {article.summary}
            </p>
          )}
        </div>

        <button
          type="button"
          onClick={onStar}
          className={`p-2 rounded-full hover:bg-gray-100 flex-shrink-0 ${
            article.isStarred ? 'text-yellow-500' : 'text-gray-300'
          }`}
          title={article.isStarred ? '取消收藏' : '收藏'}
          aria-label={article.isStarred ? '取消收藏' : '收藏'}
          aria-pressed={article.isStarred}
        >
          <svg
            className="w-5 h-5"
            fill={article.isStarred ? 'currentColor' : 'none'}
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z"
            />
          </svg>
        </button>
      </div>
    </article>
  )
}
