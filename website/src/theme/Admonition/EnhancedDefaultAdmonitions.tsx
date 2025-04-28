import React, { ReactElement, ReactNode } from 'react';
import clsx from 'clsx';
import DefaultAdmonitionTypes from '@theme-original/Admonition/Types';

/**
 * Props for enhanced admonition components
 */
interface EnhancedAdmonitionProps {
  children: ReactNode;
  className?: string;
  icon?: ReactNode;
  title?: ReactElement | string;
  collapsible?: boolean;
  open?: boolean;
  [key: string]: unknown;
}

// Define the admonition component type
type AdmonitionComponentType = React.ComponentType<{
  children: ReactNode;
  className?: string;
  icon?: ReactNode;
  title?: ReactElement | string;
  [key: string]: unknown;
}>;

/**
 * Creates an enhanced version of a standard admonition component with collapsible support
 * This approach keeps the exact structure of the original admonition
 * but adds collapsible functionality when requested
 */
const enhanceAdmonition = (
  type: string,
  OriginalAdmonition: AdmonitionComponentType,
) => {
  return (props: EnhancedAdmonitionProps) => {
    // Extract collapsible related props
    const { collapsible, open, className, ...restProps } = props;

    // Check if component should be collapsible
    const isCollapsible = !!collapsible;

    // If not collapsible, render the original component
    if (!isCollapsible) {
      return <OriginalAdmonition {...props} />;
    }

    // For collapsible admonitions, modify with details/summary
    const isOpen = !(open == false);

    // Simple approach: Render the original component inside details/summary
    return (
      <OriginalAdmonition
        {...restProps}
        className={clsx(className, 'admonition-collapsible')}>
        <details open={isOpen} className="admonition-details">
          <summary className="admonition-summary">
            <div className="admonition-summary-content">
              {/* Let the original OriginalAdmonition handle the title and icon */}
              <div className="admonition-heading-wrapper">
                <OriginalAdmonition
                  {...restProps}
                  className="admonition-heading-content"
                  children={null}
                />
              </div>
              <div className="admonition-arrow"></div>
            </div>
          </summary>
          <div className="admonition-content">{props.children}</div>
        </details>
      </OriginalAdmonition>
    );
  };
};

// Create enhanced versions of all default admonition types
const EnhancedAdmonitions: Record<string, AdmonitionComponentType> = {};
Object.entries(DefaultAdmonitionTypes).forEach(([key, component]) => {
  EnhancedAdmonitions[key] = enhanceAdmonition(
    key,
    component as AdmonitionComponentType,
  );
});

export default EnhancedAdmonitions;
