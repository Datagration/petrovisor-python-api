import EnhancedDefaultAdmonitions from './EnhancedDefaultAdmonitions';
import CustomAdmonitions from './CustomAdmonitionComponent';
import DetailsAdmonition from './DetailsAdmonitionComponent';

// Combine enhanced default admonitions with custom admonitions
const AdmonitionTypes = {
  ...EnhancedDefaultAdmonitions,
  ...CustomAdmonitions,
  ...DetailsAdmonition,
};

export default AdmonitionTypes;
