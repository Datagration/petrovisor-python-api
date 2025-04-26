import React, { JSX, ReactNode } from 'react';
import DefaultAdmonition from '@theme-original/Admonition';
import { Props } from '@theme/Admonition';

interface AdmonitionProps extends Props {
  type: string;
  title?: ReactNode;
  icon?: ReactNode;
  collapsible?: boolean | string;
  open?: boolean | string;
  children: ReactNode;
  [key: string]: unknown;
}

/**
 * Admonition component wrapper to handle custom admonition types
 */
export default function AdmonitionWrapper(props: AdmonitionProps): JSX.Element {
  // Pass through all props to the default admonition component
  return <DefaultAdmonition {...props} />;
}
