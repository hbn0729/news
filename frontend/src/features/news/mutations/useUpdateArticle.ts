import { useMutation, useQueryClient } from '@tanstack/react-query'
import type { ArticleUpdate } from '../../../types'
import { newsApi } from '../api/newsApi'
import { newsKeys } from '../../../shared/queryKeys'

export function useUpdateArticle() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ id, update }: { id: string; update: ArticleUpdate }) => {
      return newsApi.updateArticle(id, update)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: newsKeys.all })
    },
  })
}
