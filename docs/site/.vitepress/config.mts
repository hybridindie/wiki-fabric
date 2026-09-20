import { defineConfig } from 'vitepress'
import { withMermaid } from 'vitepress-plugin-mermaid'

const BASE = '/wiki-fabric/'

export default withMermaid(defineConfig({
  lang: 'en-US',
  title: 'Wiki Fabric',
  description:
    'Git-native, testable knowledge governance for AI coding agents — scoped by precedence, traceable to evidence, enforced by CI.',
  base: BASE,
  outDir: 'dist',
  ignoreDeadLinks: false,
  vite: {
    optimizeDeps: {
      include: ['debug'],
    },
  },
  head: [
    ['link', { rel: 'icon', type: 'image/svg+xml', href: BASE + 'logo.svg' }],
  ],
  mermaid: {
    // plugin auto-switches to theme 'dark' when VitePress dark mode is active
    // (Mermaid.vue reads documentElement's `dark` class and re-renders)
    securityLevel: 'loose',
    startOnLoad: false,
  },
  mermaidPlugin: {
    class: 'mermaid-blocks',
  },
  themeConfig: {
    siteTitle: 'Wiki Fabric',
    nav: [
      { text: 'Why', link: '/why' },
      { text: 'Getting Started', link: '/getting-started' },
      { text: 'Workflows', link: '/core-workflows' },
      { text: 'Config', link: '/configuration' },
      { text: 'Reference', link: '/cli' },
      {
        text: 'GitHub',
        link: 'https://github.com/hybridindie/wiki-fabric'
      }
    ],
    sidebar: [
      {
        text: 'Start Here',
        items: [
          { text: 'Why not just a wiki or RAG?', link: '/why' },
          { text: 'Getting Started', link: '/getting-started' },
          { text: 'Core Workflows', link: '/core-workflows' },
          { text: 'Task Context (wf context)', link: '/context' }
        ]
      },
      {
        text: 'Using the Fabric',
        items: [
          { text: 'Configuration', link: '/configuration' },
          { text: 'Optional Integrations', link: '/integrations' },
          { text: 'Team Sync', link: '/sync' }
        ]
      },
      {
        text: 'Reference',
        items: [
          { text: 'CLI & Scripts', link: '/cli' },
          { text: 'Model Policy & Evals', link: '/evals' },
          { text: 'OKF v0.2 Conformance', link: '/okf' },
          { text: 'Governance', link: '/governance' },
          { text: 'Machine-Readable Contract', link: '/machine-contract' },
          { text: 'Troubleshooting', link: '/troubleshooting' }
        ]
      }
    ],
    search: {
      provider: 'local',
      options: {
        translations: {
          button: { buttonText: 'Search docs' }
        }
      }
    },
    socialLinks: [
      { icon: 'github', link: 'https://github.com/hybridindie/wiki-fabric' }
    ],
    editLink: {
      pattern:
        'https://github.com/hybridindie/wiki-fabric/edit/main/docs/site/:path',
      text: 'Edit this page on GitHub'
    },
    footer: {
      message: 'Alpha — expect breaking changes.',
      copyright: 'MIT Licensed. Copyright © 2026 hybridindie'
    }
  },
}))