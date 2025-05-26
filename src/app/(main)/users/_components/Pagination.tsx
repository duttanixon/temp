"use client";

interface UserPaginationProps {
  page: number;
  setPage: (page: number) => void;
  totalItems: number;
  itemsPerPage: number;
}

export default function UserPagination({
  page,
  setPage,
  totalItems,
  itemsPerPage,
}: UserPaginationProps) {
  const totalPages = Math.ceil(totalItems / itemsPerPage);

  if (totalPages <= 1) return null;

  const pages = Array.from({ length: totalPages }, (_, i) => i);
  const hasNextPage = page < totalPages - 1;

  return (
    <div className="flex justify-center items-center gap-2">
      {/* Back button with arrow icon */}
      <button
        onClick={() => setPage(page - 1)}
        disabled={page === 0}
        className="px-3 py-1 border rounded disabled:opacity-50 flex items-center justify-center cursor-pointer">
        <svg
          className="w-4 h-4 text-gray-700"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          viewBox="0 0 24 24">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M15 19l-7-7 7-7"
          />
        </svg>
      </button>

      {pages.map((p) => (
        <button
          key={p}
          onClick={() => setPage(p)}
          className={`px-3 py-1 border rounded cursor-pointer ${p === page ? "bg-gray-200 font-bold" : ""}`}>
          {p + 1}
        </button>
      ))}

      {/* Forward button with arrow icon */}
      <button
        onClick={() => setPage(page + 1)}
        disabled={!hasNextPage}
        className="px-3 py-1 border rounded disabled:opacity-50 flex items-center justify-center cursor-pointer">
        <svg
          className="w-4 h-4 text-gray-700"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
        </svg>
      </button>
    </div>
  );
}
