import { themes as prismThemes } from 'prism-react-renderer';
import type { Config } from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import customAdmonitionsPlugin from './src/remark/custom-admonitions';

// This runs in Node.js - Don't use client-side code here (browser APIs, JSX...)

// List of all custom admonition types we want to support
const CUSTOM_ADMONITION_TYPES = [
  // standard Docusaurus admonitions
  'note',
  'tip',
  'info',
  'warning',
  'danger',
  // custom admonitions
  'function',
  'class',
];

const config: Config = {
  title: 'PetroVisor Documentation',
  //tagline: 'PetroVisor SDK',
  favicon: 'img/favicon.png',

  // Set the production url of your site here
  url: 'https://datagration.github.io',
  // Set the /<baseUrl>/ pathname under which your site is served
  // For GitHub pages deployment, it is often '/<projectName>/'
  baseUrl: '/petrovisor-python-api/',

  // GitHub pages deployment config.
  organizationName: 'Weatherford International plc', // Usually your GitHub org/user name.
  projectName: 'petrovisor-python-api', // Repo name
  // deploymentBranch: 'gh-pages',
  // trailingSlash: false,

  onBrokenLinks: 'throw',
  onBrokenMarkdownLinks: 'warn',

  // Even if you don't use internationalization, you can use this field to set
  // useful metadata like html lang. For example, if your site is Chinese, you
  // may want to replace "en" with "zh-Hans".
  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  markdown: {
    mermaid: true,
  },
  themes: ['@docusaurus/theme-mermaid'],

  presets: [
    [
      'classic',
      {
        docs: {
          // Custom path
          path: '../docs',
          routeBasePath: 'docs',
          // Use the auto-generated sidebar
          sidebarPath: './sidebars.ts',
          // Please change this to your repo.
          // Remove this to remove the "edit this page" links.
          editUrl:
            'https://github.com/Datagration/petrovisor-python-api/tree/main/website',
          // Add support for custom admonition types
          admonitions: {
            keywords: CUSTOM_ADMONITION_TYPES,
            extendDefaults: true,
          },
          // Add our custom remark plugin with the list of admonition types
          remarkPlugins: [
            [customAdmonitionsPlugin, { keywords: CUSTOM_ADMONITION_TYPES }],
            remarkMath, // Add support for math equations
          ],
          rehypePlugins: [
            rehypeKatex, // Add KaTeX rendering for math equations
          ],
        },
        blog: false, // Disable the blog feature
        theme: {
          customCss: './src/css/custom.css',
        },
      } satisfies Preset.Options,
    ],
  ],

  // Configure plugins for local search
  plugins: [
    [
      require.resolve('@easyops-cn/docusaurus-search-local'),
      /** @type {import("@easyops-cn/docusaurus-search-local").PluginOptions} */
      {
        // Options for the search plugin
        hashed: true,
        language: ['en'],
        indexDocs: true,
        indexPages: true,
        docsRouteBasePath: '/docs',
      },
    ],
  ],

  // Add KaTeX CSS for styling math equations
  stylesheets: [
    {
      href: 'https://cdn.jsdelivr.net/npm/katex@0.13.24/dist/katex.min.css',
      type: 'text/css',
      integrity:
        'sha384-odtC+0UGzzFL/6PNoE8rX/SPcQDXBJ+uRepguP4QkPCm2LBxH3FA3y+fKSiJ+AmM',
      crossorigin: 'anonymous',
    },
  ],

  themeConfig: {
    // Add project's social card
    // image: 'img/petrovisor-social-card.jpg'
    colorMode: {
      defaultMode: 'dark',
      disableSwitch: false,
      respectPrefersColorScheme: true,
    },
    navbar: {
      title: '',
      logo: {
        alt: 'PetroVisor Logo',
        src: 'img/logo-dark.png',
        srcDark: 'img/logo-light.png',
      },
      items: [
        {
          type: 'docSidebar',
          sidebarId: 'docs',
          position: 'left',
          label: 'Documentation',
        },
        {
          to: '/docs/api',
          position: 'left',
          label: 'API Reference',
        },
        {
          href: 'https://github.com/Datagration/petrovisor-python-api',
          label: 'GitHub',
          position: 'right',
        },
      ],
    },
    footer: {
      style: 'dark',
      links: [
        {
          title: 'Docs',
          items: [
            {
              label: 'Getting Started',
              to: '/docs',
            },
            {
              label: 'API Reference',
              to: '/docs/api',
            },
          ],
        },
        {
          title: 'PetroVisor SDK',
          items: [
            {
              label: 'PetroVisor Python SDK',
              href: 'https://pypi.org/project/petrovisor/',
            },
            {
              label: 'PetroVisor R SDK',
              href: 'https://github.com/Datagration/petrovisor-r-api',
            },
            {
              label: 'PetroVisor .NET SDK',
              href: 'https://www.nuget.org/packages/MyrConn.PetroVisor.Web.Client#readme-body-tab',
            },
          ],
        },
        {
          title: 'More',
          items: [
            {
              label: 'PetroVisor Knowledge Base',
              href: 'https://hs.weatherford.com/knowledge',
            },
            {
              label: 'Weatherford',
              href: 'https://www.weatherford.com/en/',
            },
          ],
        },
      ],
      copyright: `Copyright © ${new Date().getFullYear()} Weatherford`,
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
      additionalLanguages: ['python', 'bash', 'yaml'],
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
