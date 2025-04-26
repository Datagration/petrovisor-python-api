import React, { JSX, ReactNode } from 'react';
import clsx from 'clsx';
import EnhancedDefaultAdmonitions from './EnhancedDefaultAdmonitions';

// Default icons for custom admonition types
const DEFAULT_ICONS = {
  function: '🔧', // Wrench icon for functions
  class: '📦', // Package icon for classes
};

interface CustomAdmonitionProps {
  title?: ReactNode;
  children: ReactNode;
  type: string;
  collapsible?: boolean | string;
  open?: boolean | string;
  icon?: ReactNode;
  [key: string]: unknown;
}

/**
 * Common implementation for all custom admonition types
 */
function CustomAdmonitionComponent(props: CustomAdmonitionProps): JSX.Element {
  const { title, children, collapsible, open, icon, type, ...restProps } =
    props;

  // Use default icon, title if none provided
  const admonitionIcon = icon || DEFAULT_ICONS[type] || null;
  const admonitionTitle = title || type.charAt(0).toUpperCase() + type.slice(1);
  const isCollapsible = collapsible === 'true' || collapsible === true;
  const isOpen = !(open === 'false' || open === false);

  // Generate admonition class names
  const baseClasses = [
    'admonition',
    `admonition-${type}`,
    'alert',
    'alert--secondary',
  ];

  // Collapsible admonitions, using the same structure as the EnhancedDefaultAdmonitions
  if (isCollapsible) {
    return (
      <div
        className={clsx(baseClasses, 'admonition-collapsible')}
        {...restProps}>
        <details open={isOpen} className="admonition-details">
          <summary className="admonition-summary">
            <div className="admonition-summary-content">
              <div className="admonition-heading">
                {admonitionIcon && (
                  <span className="admonition-icon">{admonitionIcon}</span>
                )}
                <h5>{admonitionTitle}</h5>
              </div>
              <div className="admonition-arrow"></div>
            </div>
          </summary>
          <div className="admonition-content">{children}</div>
        </details>
      </div>
    );
  }

  // Regular version
  return (
    <div className={baseClasses.join(' ')} {...restProps}>
      <div className="admonition-heading">
        {admonitionIcon && (
          <span className="admonition-icon">{admonitionIcon}</span>
        )}
        <h5>{admonitionTitle}</h5>
      </div>
      <div className="admonition-content">{children}</div>
    </div>
  );
}

// Define admonition types from the config
const admonitionTypes = ['function', 'class'];

// Create a map of all custom admonitions
const CustomAdmonitions: Record<
  string,
  React.ComponentType<CustomAdmonitionProps>
> = {};

// Register all custom admonitions
admonitionTypes.forEach((type) => {
  CustomAdmonitions[type] = (props: CustomAdmonitionProps) => (
    <CustomAdmonitionComponent {...props} type={type} />
  );
});

// Combine enhanced default admonitions with our custom admonitions
const AdmonitionTypes = {
  ...EnhancedDefaultAdmonitions,
  ...CustomAdmonitions,
};

export default AdmonitionTypes;
