interface EmptyStateProps {
  hasFilters: boolean;
}

export default function EmptyState({ hasFilters }: Readonly<EmptyStateProps>) {
  return (
    <div className="flex flex-col items-center justify-center py-24 text-center">
      <div className="text-4xl mb-4 opacity-30">&#128269;</div>
      <h3 className="text-xl font-bold mb-2 uppercase">
        {hasFilters ? "No Matching Cases" : "No Cases Yet"}
      </h3>
      <p className="text-sm text-muted-foreground max-w-md mb-8">
        {hasFilters
          ? "Try adjusting your filters to find what you're looking for."
          : "Create your first investigation to get started with forensic analysis."}
      </p>
      {!hasFilters && (
        <button className="px-8 py-3 bg-primary text-primary-foreground font-bold uppercase tracking-widest text-sm hover:brightness-110 transition-all cursor-pointer">
          Create Case
        </button>
      )}
    </div>
  );
}
