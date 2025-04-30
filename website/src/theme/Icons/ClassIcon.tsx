import React from 'react';

export function ClassIcon(props) {
  return (
    <svg
      viewBox="0 0 24 24"
      stroke="currentColor"
      strokeWidth="2"
      {...props}
    >
      <path fill="none"
        d="M21 16V8a2 2 0 0 0-1-1.7l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.7l7 4a2 2 0 0 0 2 0l7-4a2 2 0 0 0 1-1.7z"
      />
      <polyline fill="none" points="3.3 7.6 12 13 20.7 7.6" />
      <line x1="12" y1="22" x2="12" y2="13" />
    </svg>
  );
}
