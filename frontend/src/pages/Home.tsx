import { useState, useMemo } from 'react'
import { useNews } from '../hooks/useNews'
import NewsFeed from '../components/NewsFeed'
import CategoryFilter from '../components/CategoryFilter'
import SourceFilter from '../components/SourceFilter'
import { useDebounce } from '../hooks/useDebounce'
import { useQueryClient } from '@tanstack/react-query'

export default function Home() {
  const [source, setSource] = useState<string | null>(null)
  const [category, setCategory] = useState<string | null>(null)
  const [searchInput, setSearchInput] = useState('')
  const [starredOnly, setStarredOnly] = useState(false)

  const queryClient = useQueryClient()

  // Debounce search input to avoid excessive API calls
  const debouncedSearch = useDebounce(searchInput, 300)

  const { data, isLoading, isError, error, fetchNextPage, hasNextPage, isFetchingNextPage, refetch, isRefetching } = useNews({
    source,
    category,
    search: debouncedSearch || undefined,
    starredOnly,
  })

  // 手动刷新函数
  const handleRefresh = () => {
    refetch()
    // 同时刷新统计数据、来源和分类
    queryClient.invalidateQueries({ queryKey: ['stats'] })
    queryClient.invalidateQueries({ queryKey: ['sources'] })
    queryClient.invalidateQueries({ queryKey: ['categories'] })
  }

  const articles = useMemo(
    () => data?.pages.flatMap((page) => page.items) ?? [],
    [data]
  )
  const total = data?.pages[0]?.total ?? 0

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-xl font-bold text-gray-900">财经资讯聚合</h1>
            <div className="flex items-center gap-3">
              <button
                onClick={handleRefresh}
                disabled={isRefetching}
                className={`px-3 py-1.5 text-sm font-medium rounded-lg transition-all ${
                  isRefetching
                    ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                    : 'bg-blue-500 text-white hover:bg-blue-600 active:scale-95'
                }`}
                aria-label="刷新新闻"
                title="刷新最新新闻"
              >
                <span className={isRefetching ? 'inline-block animate-spin' : ''}>
                  {isRefetching ? '🔄' : '🔄'}
                </span>
                {' '}
                {isRefetching ? '刷新中...' : '刷新'}
              </button>
              <span className="text-sm text-gray-500" aria-live="polite">
                {total} 条新闻
              </span>
            </div>
          </div>

          {/* Search */}
          <div className="mt-3">
            <label htmlFor="search" className="sr-only">搜索新闻</label>
            <input
              id="search"
              type="text"
              placeholder="搜索新闻..."
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              aria-label="搜索新闻"
            />
          </div>

          {/* Filters */}
          <div className="mt-3 flex flex-wrap gap-2 items-center" role="group" aria-label="筛选选项">
            <SourceFilter value={source} onChange={setSource} />
            <CategoryFilter value={category} onChange={setCategory} />
            <button
              onClick={() => setStarredOnly(!starredOnly)}
              className={`px-3 py-1 rounded-full text-sm transition-colors ${
                starredOnly
                  ? 'bg-yellow-100 text-yellow-800'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
              aria-pressed={starredOnly}
            >
              <span aria-hidden="true">⭐</span> 收藏
            </button>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-4xl mx-auto" role="main">
        {isLoading ? (
          <div className="p-8 text-center text-gray-500" aria-busy="true">
            加载中...
          </div>
        ) : isError ? (
          <div className="p-8 text-center text-red-500" role="alert">
            加载失败: {error instanceof Error ? error.message : '未知错误'}
            <button
              onClick={() => window.location.reload()}
              className="ml-2 underline hover:no-underline"
            >
              重试
            </button>
          </div>
        ) : articles.length === 0 ? (
          <div className="p-8 text-center text-gray-500">暂无新闻</div>
        ) : (
          <NewsFeed
            articles={articles}
            hasMore={hasNextPage ?? false}
            isLoadingMore={isFetchingNextPage}
            onLoadMore={() => fetchNextPage()}
          />
        )}
      </main>
    </div>
  )
}
