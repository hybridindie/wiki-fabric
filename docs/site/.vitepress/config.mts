import { defineConfig } from 'vitepress'

const BASE = '/wiki-fabric/'

export default defineConfig({
  lang: 'en-US',
  title: 'Wiki Fabric',
  description:
    'Git-native, testable knowledge governance for AI coding agents — scoped by precedence, traceable to evidence, enforced by CI.',
  base: BASE,
  outDir: 'dist',
  ignoreDeadLinks: false,
  head: [
    ['link', { rel: 'icon', type: 'image/svg+xml', href: BASE + 'logo.svg' }],
  ],
  themeConfig: {
    siteTitle: 'Wiki Fabric',
    nav: [
      { text: 'Guide', link: '/why' },
      { text: 'Workflows', link: '/core-workflows' },
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
          { text: 'Architecture', link: '/architecture' },
          { text: 'Core Workflows', link: '/core-workflows' }
        ]
      },
      {
        text: 'Using the Fabric',
        items: [
          { text: 'Task Context (wf context)', link: '/context' },
          { text: 'Team Sync', link: '/sync' },
          { text: 'Optional Integrations', link: '/integrations' }
        ]
      },
      {
        text: 'Reference',
        items: [
          { text: 'CLI & Scripts', link: '/cli' },
          { text: 'Model Policy & Evals', link: '/evals' },
          { text: 'OKF v0.2 Conformance', link: '/okf' },
          { text: 'Machine-Readable Contract', link: '/machine-contract' },
          { text: 'Governance', link: '/governance' }
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
  markdown: {
    // mermaid support is provided by vitepress-plugin-group-icons-less setups;
    // we render mermaid blocks as code fences (GitHub renders them natively).
    config: (md) => {
      // keep default; mermaid fences display as highlighted code in VitePress
    }
  }
})