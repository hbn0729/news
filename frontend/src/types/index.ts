/**
 * 类型定义 - 集中管理所有类型
 *
 * 设计原则：
 * - 单一来源：所有类型在此定义
 * - 与后端 schema 保持一致
 */

// ============================================
// 文章相关类型
// ============================================

export interface Article {
  id: string
  title: string
  content: string | null
  summary: string | null
  url: string
  source: string
  sourceCategory: string | null
  publishedAt: string
  collectedAt: string
  isRead: boolean
  isStarred: boolean
  isFiltered: boolean
}

export interface ArticleUpdate {
  isRead?: boolean
  isStarred?: boolean
}

export interface ArticleDTO {
  id: string
  title: string
  content: string | null
  summary: string | null
  url: string
  source: string
  source_category: string | null
  published_at: string
  collected_at: string
  is_read: boolean
  is_starred: boolean
  is_filtered: boolean
}

export interface ArticleUpdateDTO {
  is_read?: boolean
  is_starred?: boolean
}

// ============================================
// 分页相关类型
// ============================================

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  perPage: number
  pages: number
}

export type PaginatedNews = PaginatedResponse<Article>

export interface PaginatedResponseDTO<T> {
  items: T[]
  total: number
  page: number
  per_page: number
  pages: number
}

export type PaginatedNewsDTO = PaginatedResponseDTO<ArticleDTO>

// ============================================
// 筛选相关类型
// ============================================

export interface NewsFilters {
  source?: string | null
  category?: string | null
  search?: string
  publishedDate?: string | null
  starredOnly?: boolean
}

// ============================================
// 元数据类型
// ============================================

export interface SourceInfo {
  source: string
  count: number
}

export interface CategoryInfo {
  category: string
  count: number
}

export interface Stats {
  totalArticles: number
  unread: number
  starred: number
  filtered: number
}

export interface StatsDTO {
  total_articles: number
  unread: number
  starred: number
  filtered: number
}
