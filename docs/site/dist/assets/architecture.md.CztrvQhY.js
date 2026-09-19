import{_ as a,o as i,c as t,a2 as n}from"./chunks/framework.CcJ8wlZS.js";const k=JSON.parse('{"title":"Architecture — pipeline diagram and module map","description":"The wiki-fabric pipeline and module structure","frontmatter":{"type":"index","title":"Architecture — pipeline diagram and module map","description":"The wiki-fabric pipeline and module structure","created":"2026-09-19T00:00:00.000Z","updated":"2026-09-19T00:00:00.000Z"},"headers":[],"relativePath":"architecture.md","filePath":"architecture.md"}'),e={name:"architecture.md"};function p(l,s,r,E,h,o){return i(),t("div",null,[...s[0]||(s[0]=[n(`<h1 id="architecture" tabindex="-1">Architecture <a class="header-anchor" href="#architecture" aria-label="Permalink to &quot;Architecture&quot;">​</a></h1><div class="language-mermaid vp-adaptive-theme"><button title="Copy Code" class="copy"></button><span class="lang">mermaid</span><pre class="shiki shiki-themes github-light github-dark vp-code" tabindex="0"><code><span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">graph TB</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">    subgraph &quot;Source Repos&quot;</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">        R1[&quot;project-a&quot;]</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">        R2[&quot;project-b&quot;]</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">        R3[&quot;project-c&quot;]</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">    end</span></span>
<span class="line"></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">    subgraph &quot;Fabric&quot;</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">        RAW[&quot;evidence/raw/&lt;br/&gt;(immutable captures)&quot;]</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">        CLAIMS[&quot;evidence/claims/&lt;br/&gt;(verified claims)&quot;]</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">        CONCEPTS[&quot;concepts/&lt;br/&gt;(synthesized concepts)&quot;]</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">        PATTERNS[&quot;patterns/&lt;br/&gt;(cross-project patterns)&quot;]</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">        SKILLS[&quot;skills/&lt;br/&gt;(promoted skills)&quot;]</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">        EVENTS[&quot;projects/*/experience-events/&quot;]</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">        ENTITIES[&quot;global/entities/&lt;br/&gt;(AST-indexed symbols)&quot;]</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">        GRAPHS[&quot;global/graphs/&lt;br/&gt;(graphify call graph)&quot;]</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">        REGISTRY[&quot;registry/&lt;br/&gt;(catalog.json, promotion queue, log)&quot;]</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">    end</span></span>
<span class="line"></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">    R1 &amp; R2 &amp; R3 --&gt;|capture| RAW</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">    RAW --&gt;|&quot;ingest.py → extract_backends (LLM)&quot;| CLAIMS</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">    CLAIMS --&gt;|&quot;synthesize.py (LLM)&quot;| CONCEPTS</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">    CLAIMS --&gt;|&quot;mine-promotions.py&quot;| PATTERNS</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">    PATTERNS --&gt;|&quot;promote.py&quot;| SKILLS</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">    R1 &amp; R2 &amp; R3 --&gt;|&quot;build-entity-index.py (AST)&quot;| ENTITIES</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">    R1 --&gt;|&quot;graphify-bridge.py (AST, 0 tokens)&quot;| GRAPHS</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">    EVENTS --&gt;|&quot;mine-promotions.py&quot;| PATTERNS</span></span></code></pre></div><hr>`,3)])])}const u=a(e,[["render",p]]);export{k as __pageData,u as default};
