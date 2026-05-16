import React from 'react';
import { Stethoscope } from 'lucide-react';

const DisclaimerBanner = ({ variant = 'default', className = '' }) => {
  const styles = {
    default: 'bg-blue-50 border-blue-200 text-blue-900 dark:bg-blue-950/30 dark:border-blue-800 dark:text-blue-200',
    warning: 'bg-amber-50 border-amber-300 text-amber-950 dark:bg-amber-950/30 dark:border-amber-800 dark:text-amber-200',
    danger: 'bg-red-50 border-red-300 text-red-950 dark:bg-red-950/30 dark:border-red-800 dark:text-red-200',
  };

  return (
    <div className={`border rounded-lg p-3 text-sm flex items-start gap-2 ${styles[variant]} ${className}`}>
      <Stethoscope className="h-4 w-4 mt-0.5 shrink-0" />
      <p>
        <strong>Medical Disclaimer:</strong> MediGuard provides health information for educational purposes only.
        It is not a diagnostic tool. Always consult a qualified healthcare professional.
      </p>
    </div>
  );
};

export default DisclaimerBanner;
