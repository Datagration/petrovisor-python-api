import { visit } from 'unist-util-visit';
import type { Plugin } from 'unified';
import type { Root } from 'mdast';
import type { Node } from 'unist';

// Define interfaces for directive nodes
interface DirectiveNode {
  type: 'containerDirective' | 'leafDirective' | 'textDirective';
  name: string;
  attributes?: Record<string, string>;
  children?: Node[];
  data?: {
    hName?: string;
    hProperties?: Record<string, unknown>;
  };
  label?: string;
}

interface PluginOptions {
  keywords?: string[];
}

/**
 * Remark plugin to handle custom admonition directives with attributes
 * This plugin processes:
 * - Container directives: :::admonition[Title] {attr1="value1" attr2="value2"}
 * - Leaf directives: ::admonition[Title] {attr1="value1" attr2="value2"}
 * - Text directives: :admonition[Title] {attr1="value1" attr2="value2"}
 * 
 * It also supports shorthand boolean attributes:
 * - :::admonition[Title] {collapsible}  // equivalent to collapsible=true
 */
const customAdmonitionsPlugin: Plugin<[PluginOptions?], Root> = (
  options = {},
) => {
  // Default options
  const pluginOptions: PluginOptions = {
    keywords: ['custom_admonition'],
    ...options,
  };

  const transformer = (tree: Root): void => {
    visit(tree, (node: Node) => {
      // Check if node is a directive node
      if (
        'type' in node &&
        (node.type === 'containerDirective' ||
          node.type === 'leafDirective' ||
          node.type === 'textDirective')
      ) {
        const directiveNode = node as DirectiveNode;

        // Check if this directive is one of our custom admonitions
        if (!pluginOptions.keywords?.includes(directiveNode.name)) {
          return;
        }

        // Make sure we have data and attributes
        const data = directiveNode.data || (directiveNode.data = {});
        const attributes = directiveNode.attributes || {};

        // Process attributes to handle shorthand boolean syntax
        const processedAttributes: Record<string, unknown> = {};
        
        // Process each attribute
        for (const [key, value] of Object.entries(attributes)) {
          if (value === '' || value === undefined) {
            // If an attribute has no value, consider it a boolean attribute with value true
            processedAttributes[key] = true;
          } else {
            // Normal case: keep the original value
            processedAttributes[key] = value;
          }
          
          // Special handling for boolean text values
          if (value === 'true' || value === 'false') {
            processedAttributes[key] = value === 'true';
          }
        }

        // Set up the hProperties which will be passed to the React component
        data.hName =
          directiveNode.type === 'textDirective' ? 'span' : 'admonition';

        // For text directives, we use a span with special classes
        if (directiveNode.type === 'textDirective') {
          data.hProperties = {
            className: [
              'admonition-inline',
              `admonition-inline-${directiveNode.name}`,
            ],
            ...processedAttributes, // Use processed attributes instead
          };

          // If there's a title in the label, add it as a data attribute
          if (directiveNode.label) {
            data.hProperties['data-title'] = directiveNode.label;
          }
        } else {
          // For container and leaf directives, use the admonition component
          data.hProperties = {
            type: directiveNode.name,
            ...processedAttributes, // Use processed attributes instead
          };

          // If there's a title in the label (from [Title])
          if (directiveNode.label) {
            data.hProperties.title = directiveNode.label;
          }
        }
      }
    });
  };

  return transformer;
};

export default customAdmonitionsPlugin;
