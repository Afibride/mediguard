import React from 'react';
import { BookOpen } from 'lucide-react';

const SourceCitation = ({ sources }) => {
  if (!sources?.length) return null;

  return (
    <div className="mt-2 max-w-full min-w-0 px-3 py-2 text-xs text-muted-foreground border rounded-md bg-muted/40 flex items-start gap-2 overflow-hidden">
      <BookOpen className="h-3.5 w-3.5 mt-0.5 text-primary shrink-0" />
      <span className="min-w-0 break-words [overflow-wrap:anywhere]">
        <span className="font-medium text-foreground">Source: </span>
        {sources.join(', ')} - MediGuard curated medical references
      </span>
    </div>
  );
};

export default SourceCitation;

