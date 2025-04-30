// File: app/(main)/customers/components/Pagination.tsx
'use client'

interface CustomerPaginationProps {
  page: number
  setPage: (page: number) => void
  totalItems: number
  itemsPerPage: number
}

export default function CustomerPagination({
  page,
  setPage,
  totalItems,
  itemsPerPage
}: CustomerPaginationProps) {
  const totalPages = Math.ceil(totalItems / itemsPerPage)

  if (totalPages <= 1) return null

  const pages = Array.from({ length: totalPages }, (_, i) => i)
  const hasNextPage = page < totalPages - 1

  return (
    <div className="flex justify-center items-center mt-4 gap-2">
      <button
        onClick={() => setPage(page - 1)}
        disabled={page === 0}
        className="px-3 py-1 border rounded disabled:opacity-50"
      >
        Prev
      </button>

      {pages.map((p) => (
        <button
          key={p}
          onClick={() => setPage(p)}
          className={`px-3 py-1 border rounded ${p === page ? 'bg-gray-200 font-bold' : ''}`}
        >
          {p + 1}
        </button>
      ))}

      <button
        onClick={() => setPage(page + 1)}
        disabled={!hasNextPage}
        className="px-3 py-1 border rounded disabled:opacity-50"
      >
        Next
      </button>
    </div>
  )
}