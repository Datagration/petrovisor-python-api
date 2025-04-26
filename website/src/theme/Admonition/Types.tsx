import React from 'react';
import EnhancedDefaultAdmonitions from './EnhancedDefaultAdmonitions';
import CustomAdmonitionComponent from './CustomAdmonitionComponent';
import type { CustomAdmonitionProps } from './CustomAdmonitionComponent';

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
