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

  const getPageNumbers = () => {
    const pageNumbers = [];
    const maxPageButtons = 3;
    const halfMaxButtons = Math.floor(maxPageButtons / 2);
    let startPage = Math.max(0, page - halfMaxButtons);
    let endPage = Math.min(totalPages - 1, page + halfMaxButtons);

    if (page - startPage < halfMaxButtons) {
      endPage = Math.min(
        totalPages - 1,
        endPage + (halfMaxButtons - (page - startPage))
      );
    }

    if (endPage - page < halfMaxButtons) {
      startPage = Math.max(0, startPage - (halfMaxButtons - (endPage - page)));
    }

    if (startPage > 0) {
      pageNumbers.push(0);
      if (startPage > 1) {
        pageNumbers.push("...");
      }
    }

    for (let i = startPage; i <= endPage; i++) {
      pageNumbers.push(i);
    }

    if (endPage < totalPages - 1) {
      if (endPage < totalPages - 2) {
        pageNumbers.push("...");
      }
      pageNumbers.push(totalPages - 1);
    }

    return pageNumbers;
  };

  const pages = getPageNumbers();
  const hasNextPage = page < totalPages - 1;

  return (
    <div className="flex justify-center items-center gap-2">
      {/* Back button with arrow icon */}
      <button
        onClick={() => setPage(page - 1)}
        disabled={page === 0}
        className="px-3 py-1 border rounded disabled:opacity-50 flex items-center justify-center cursor-pointer"
      >
        <svg
          className="w-4 h-4 text-gray-700"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M15 19l-7-7 7-7"
          />
        </svg>
      </button>

      {pages.map((p, index) =>
        typeof p === "string" ? (
          <span key={`${p}-${index}`} className="px-3 py-1">
            {p}
          </span>
        ) : (
          <button
            key={p}
            onClick={() => setPage(p)}
            className={`px-3 py-1 border rounded cursor-pointer ${
              p === page ? "bg-gray-200 font-bold" : ""
            }`}
          >
            {p + 1}
          </button>
        )
      )}

      {/* Forward button with arrow icon */}
      <button
        onClick={() => setPage(page + 1)}
        disabled={!hasNextPage}
        className="px-3 py-1 border rounded disabled:opacity-50 flex items-center justify-center cursor-pointer"
      >
        <svg
          className="w-4 h-4 text-gray-700"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
        </svg>
      </button>
    </div>
  );
}