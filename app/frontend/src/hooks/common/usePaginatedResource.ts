import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { usePagination } from "@/hooks/common/usePagination";

export function usePaginatedResource<T>(
  fetcher: () => Promise<T[]>,
  filterFn: (item: T, query: string) => boolean,
  itemsPerPage = 10,
) {
  const fetcherRef = useRef(fetcher);
  fetcherRef.current = fetcher;
  const filterRef = useRef(filterFn);
  filterRef.current = filterFn;

  const [items, setItems] = useState<T[]>([]);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      setItems(await fetcherRef.current());
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh().catch(() => setLoading(false));
  }, [refresh]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return items;
    return items.filter((item) => filterRef.current(item, q));
  }, [items, query]);

  const { currentPage, setCurrentPage, totalPages, paginatedItems } =
    usePagination(filtered, itemsPerPage, query);

  return {
    items: filtered,
    paginatedItems,
    currentPage,
    setCurrentPage,
    totalPages,
    loading,
    query,
    setQuery,
    refresh,
  };
}
