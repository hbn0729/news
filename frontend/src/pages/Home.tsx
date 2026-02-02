/**
 * Home Page - 首页
 *
 * 职责：
 * - UI 渲染
 * - 事件处理委托给 hooks
 *
 * 设计原则：
 * - 展示组件：只负责渲染
 * - 状态逻辑由 useHomeState 管理
 */

import NewsFeed from '../components/NewsFeed'
import CategoryFilter from '../components/CategoryFilter'
import SourceFilter from '../components/SourceFilter'
import { useHomeState } from '../hooks/useHomeState'

export default function Home() {
  const {
    source,
    setSource,
    category,
    setCategory,
    searchInput,
    setSearchInput,
    starredOnly,
    toggleStarredOnly,
    articles,
    total,
    isLoading,
    isError,
    error,
    isRefetching,
    hasNextPage,
    isFetchingNextPage,
    fetchNextPage,
    handleRefresh,
  } = useHomeState()

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
              >
                <span className={isRefetching ? 'inline-block animate-spin' : ''}>
                  🔄
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
            <input
              type="text"
              placeholder="搜索新闻..."
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              aria-label="搜索新闻"
            />
          </div>

          {/* Filters */}
          <div className="mt-3 flex flex-wrap gap-2 items-center">
            <SourceFilter value={source} onChange={setSource} />
            <CategoryFilter value={category} onChange={setCategory} />
            <button
              onClick={toggleStarredOnly}
              className={`px-3 py-1 rounded-full text-sm transition-colors ${
                starredOnly
                  ? 'bg-yellow-100 text-yellow-800'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
              aria-pressed={starredOnly}
            >
              ⭐ 收藏
            </button>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-4xl mx-auto">
        {isLoading ? (
          <div className="p-8 text-center text-gray-500">加载中...</div>
        ) : isError ? (
          <div className="p-8 text-center text-red-500">
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
            hasMore={hasNextPage}
            isLoadingMore={isFetchingNextPage}
            onLoadMore={() => fetchNextPage()}
          />
        )}
      </main>
    </div>
  )
}
