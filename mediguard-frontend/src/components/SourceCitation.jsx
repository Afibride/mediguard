import React from 'react';
import { BookOpen } from 'lucide-react';

const SourceCitation = ({ sources }) => {
  if (!sources?.length) return null;

  return (
    <div className="mt-2 px-3 py-2 text-xs text-muted-foreground border rounded-md bg-muted/40 flex items-start gap-2">
      <BookOpen className="h-3.5 w-3.5 mt-0.5 text-primary" />
      <span>
        <span className="font-medium text-foreground">Source: </span>
        {sources.join(', ')} - MediGuard curated medical references
      </span>
    </div>
  );
};

export default SourceCitation;

