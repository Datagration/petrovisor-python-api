import React, { ReactElement, ReactNode } from 'react';
import Details from '@theme/Details';

export interface DetailsAdmonitionProps {
  title?: ReactElement | string;
  children: ReactNode;
  open?: boolean;
  className?: string;
  [key: string]: unknown;
}

/**
 * Custom Details admonition implementation that uses the standard Docusaurus Details component
 */
function DetailsAdmonitionComponent(props: DetailsAdmonitionProps): ReactNode {
  const { title, children, open, className, ...restProps } = props;

  const isOpen = open !== false;
  const summary = title !== undefined && title !== null ? title : 'Details';

  return (
    <Details
      summary={summary}
      open={isOpen}
      className={className}
      {...restProps}>
      {children}
    </Details>
  );
}

// Export directly as an object with the 'details' key
export default {
  details: DetailsAdmonitionComponent,
};
