import type { NewsFilters } from '../types'

function normalizeNewsFilters(filters: NewsFilters = {}) {
  return {
    source: filters.source ?? '',
    category: filters.category ?? '',
    search: filters.search ?? '',
    publishedDate: filters.publishedDate ?? '',
    starredOnly: filters.starredOnly ?? false,
  }
}

export const newsKeys = {
  all: ['news'] as const,
  lists: () => [...newsKeys.all, 'list'] as const,
  list: (filters: NewsFilters = {}) => [...newsKeys.lists(), normalizeNewsFilters(filters)] as const,
}

export const metaKeys = {
  all: ['meta'] as const,
  sources: () => [...metaKeys.all, 'sources'] as const,
  categories: () => [...metaKeys.all, 'categories'] as const,
  stats: () => [...metaKeys.all, 'stats'] as const,
}
