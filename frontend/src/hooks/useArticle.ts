/**
 * useArticle Hook - 文章操作
 *
 * 职责：
 * - 更新文章状态
 * - 乐观更新
 */

import { useMutation, useQueryClient } from '@tanstack/react-query'
import { newsApi } from '../api/client'
import type { ArticleUpdate } from '../types'

export function useUpdateArticle() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ id, update }: { id: string; update: ArticleUpdate }) => {
      return newsApi.updateArticle(id, update)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['news'] })
    },
  })
}
