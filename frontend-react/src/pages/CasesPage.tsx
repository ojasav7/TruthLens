import { useState, useMemo } from "react";
import Header from "../components/Header";
import FilterBar from "../components/cases/FilterBar";
import CaseCard from "../components/cases/CaseCard";
import EmptyState from "../components/cases/EmptyState";
import { MOCK_CASES } from "../data/casesData";

const PRIORITY_ORDER = { high: 0, medium: 1, low: 2 };

export default function CasesPage() {
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("all");
  const [priority, setPriority] = useState("all");
  const [sort, setSort] = useState("newest");
  const [page, setPage] = useState(1);
  const perPage = 6;

  const filtered = useMemo(() => {
    let cases = [...MOCK_CASES];

    // Search
    if (search) {
      const q = search.toLowerCase();
      cases = cases.filter(
        (c) =>
          c.title.toLowerCase().includes(q) ||
          c.id.toLowerCase().includes(q) ||
          c.summary.toLowerCase().includes(q)
      );
    }

    // Status
    if (status !== "all") {
      cases = cases.filter((c) => c.status === status);
    }

    // Priority
    if (priority !== "all") {
      cases = cases.filter((c) => c.priority === priority);
    }

    // Sort
    switch (sort) {
      case "oldest":
        cases.reverse();
        break;
      case "updated":
        cases.sort((a, b) => b.updated.localeCompare(a.updated));
        break;
      case "priority":
        cases.sort((a, b) => PRIORITY_ORDER[a.priority] - PRIORITY_ORDER[b.priority]);
        break;
    }

    return cases;
  }, [search, status, priority, sort]);

  const totalPages = Math.ceil(filtered.length / perPage);
  const paged = filtered.slice((page - 1) * perPage, page * perPage);
  const hasFilters = !!(search || status !== "all" || priority !== "all");

  return (
    <div className="min-h-screen bg-background text-foreground">
      <Header backendStatus="live" />
      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Title */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-8">
          <h1 className="text-4xl font-extrabold tracking-tighter uppercase">
            Cases
          </h1>
          <button className="px-6 py-2.5 bg-primary text-primary-foreground font-bold uppercase tracking-widest text-xs hover:brightness-110 transition-all cursor-pointer">
            New Case
          </button>
        </div>

        <div className="h-px bg-border mb-8" />

        {/* Filters */}
        <FilterBar
          search={search}
          status={status}
          priority={priority}
          sort={sort}
          onSearchChange={(v) => { setSearch(v); setPage(1); }}
          onStatusChange={(v) => { setStatus(v); setPage(1); }}
          onPriorityChange={(v) => { setPriority(v); setPage(1); }}
          onSortChange={setSort}
        />

        {/* Cases Grid */}
        {paged.length === 0 ? (
          <EmptyState hasFilters={hasFilters} />
        ) : (
          <>
            <div className="grid md:grid-cols-2 gap-px bg-border border border-border" role="list">
              {paged.map((c) => (
                <CaseCard key={c.id} caseItem={c} />
              ))}
            </div>

            {/* Pagination */}
            <div className="flex items-center justify-between mt-8 text-xs text-muted-foreground font-mono uppercase tracking-widest">
              <span>
                Showing {(page - 1) * perPage + 1}-{Math.min(page * perPage, filtered.length)} of {filtered.length} cases
              </span>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="px-3 py-1.5 border border-border hover:border-primary/30 transition-colors cursor-pointer disabled:opacity-30 disabled:cursor-not-allowed"
                >
                  Prev
                </button>
                {Array.from({ length: totalPages }, (_, i) => i + 1).map((p) => (
                  <button
                    key={p}
                    onClick={() => setPage(p)}
                    className={`w-8 h-8 flex items-center justify-center border transition-colors cursor-pointer ${
                      p === page
                        ? "bg-primary text-primary-foreground border-primary"
                        : "border-border hover:border-primary/30"
                    }`}
                  >
                    {p}
                  </button>
                ))}
                <button
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                  className="px-3 py-1.5 border border-border hover:border-primary/30 transition-colors cursor-pointer disabled:opacity-30 disabled:cursor-not-allowed"
                >
                  Next
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
