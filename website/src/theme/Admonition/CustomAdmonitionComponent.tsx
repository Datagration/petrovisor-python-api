import React, { JSX, ReactNode } from 'react';
import clsx from 'clsx';
import { FunctionIcon, ClassIcon } from '../Icons';

// Map of admonition types to their respective SVG icon components
const ICON_COMPONENTS = {
  function: FunctionIcon,
  class: ClassIcon,
};

export interface CustomAdmonitionProps {
  title?: ReactNode;
  children: ReactNode;
  type: string;
  collapsible?: boolean;
  open?: boolean;
  icon?: ReactNode;
  [key: string]: unknown;
}

/**
 * Common implementation for all custom admonition types
 */
export default function CustomAdmonitionComponent(
  props: CustomAdmonitionProps,
): JSX.Element {
  const { title, children, collapsible, open, icon, type, ...restProps } =
    props;

  // Get the appropriate icon component
  const IconComponent = ICON_COMPONENTS[type];

  // Use provided icon, component icon, or null
  const admonitionIcon = icon || (IconComponent ? <IconComponent /> : null);
  const admonitionTitle = title || type.charAt(0).toUpperCase() + type.slice(1);
  const isCollapsible = !!collapsible;
  const isOpen = !(open == false);

  // Generate admonition class names
  const baseClasses = [
    'admonition',
    `admonition-${type}`,
    'alert',
    'alert--secondary',
  ];

  // Collapsible admonitions
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
