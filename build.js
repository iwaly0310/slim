// 宏謙健康減重指南 — 靜態網站產生器
// 用法：node build.js  → 輸出到 docs/（GitHub Pages 讀這個資料夾）
const fs = require('fs');
const path = require('path');
const { marked } = require('marked');

const ROOT = __dirname;
const OUT = path.join(ROOT, 'docs');
const site = JSON.parse(fs.readFileSync(path.join(ROOT, 'content', 'site.json'), 'utf8'));

marked.setOptions({ gfm: true, breaks: false });

// ---------- helpers ----------
const rimraf = p => fs.rmSync(p, { recursive: true, force: true });
const mkdirp = p => fs.mkdirSync(p, { recursive: true });
const write = (rel, html) => { const f = path.join(OUT, rel); mkdirp(path.dirname(f)); fs.writeFileSync(f, html, 'utf8'); };
const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const copyDir = (src, dst) => { mkdirp(dst); for (const f of fs.readdirSync(src)) { const s = path.join(src, f), d = path.join(dst, f); fs.statSync(s).isDirectory() ? copyDir(s, d) : fs.copyFileSync(s, d); } };

function parseFrontmatter(raw) {
  const m = raw.match(/^---\r?\n([\s\S]*?)\r?\n---\r?\n?([\s\S]*)$/);
  if (!m) return { meta: {}, body: raw };
  const meta = {};
  for (const line of m[1].split(/\r?\n/)) {
    const i = line.indexOf(':'); if (i < 0) continue;
    const k = line.slice(0, i).trim(); let v = line.slice(i + 1).trim();
    if (/^\[.*\]$/.test(v)) v = v.slice(1, -1).split(',').map(s => s.trim()).filter(Boolean);
    meta[k] = v;
  }
  return { meta, body: m[2] };
}

const readTime = text => Math.max(1, Math.round(text.replace(/\s/g, '').length / 400));

// ---------- load content ----------
const CATS = site.categories; // [{id, name, desc}]
const PHASES = site.phases;   // [{id, name, tagline, desc}]

const articles = fs.readdirSync(path.join(ROOT, 'content', 'articles'))
  .filter(f => f.endsWith('.md'))
  .map(f => {
    const raw = fs.readFileSync(path.join(ROOT, 'content', 'articles', f), 'utf8');
    const { meta, body } = parseFrontmatter(raw);
    const slug = f.replace(/\.md$/, '');
    return { slug, ...meta, order: Number(meta.order || 99), phases: meta.phases || [], body, html: marked.parse(body), minutes: readTime(body) };
  })
  .sort((a, b) => a.order - b.order || (b.date || '').localeCompare(a.date || ''));

const faqRaw = fs.readFileSync(path.join(ROOT, 'content', 'faq.md'), 'utf8');
const faqs = faqRaw.split(/^## /m).slice(1).map(block => {
  const [q, ...rest] = block.split(/\r?\n/);
  return { q: q.trim(), a: marked.parse(rest.join('\n').trim()) };
});

const catById = Object.fromEntries(CATS.map(c => [c.id, c]));
const phaseById = Object.fromEntries(PHASES.map(p => [p.id, p]));

// ---------- layout ----------
function layout({ title, description, canonical, body, ogImage, narrow, jsonld }) {
  const fullTitle = title ? `${title}｜${site.name}` : `${site.name}｜${site.tagline}`;
  const url = site.url + (canonical || '/');
  const og = site.url + (ogImage || '/assets/img/og.png');
  return `<!DOCTYPE html>
<html lang="zh-Hant-TW">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${esc(fullTitle)}</title>
<meta name="description" content="${esc(description || site.description)}">
<link rel="canonical" href="${url}">
<meta property="og:type" content="${canonical && canonical !== '/' ? 'article' : 'website'}">
<meta property="og:title" content="${esc(fullTitle)}">
<meta property="og:description" content="${esc(description || site.description)}">
<meta property="og:url" content="${url}">
<meta property="og:image" content="${og}">
<meta property="og:site_name" content="${esc(site.name)}">
<meta property="og:locale" content="zh_TW">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/assets/img/logo-72.png">
<link rel="apple-touch-icon" href="/assets/img/logo.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;500;700;900&display=swap">
<script defer src="https://cloud.umami.is/script.js" data-website-id="7cadf1bf-b05b-4c80-a86a-5e7b7192b3e0"></script>
<link rel="stylesheet" href="/assets/style.css">
${jsonld ? `<script type="application/ld+json">${JSON.stringify(jsonld)}</script>` : ''}
</head>
<body>
<a class="skip" href="#main">跳到主要內容</a>
<header class="top">
  <div class="wrap top-in">
    <a class="brand" href="/"><img src="/assets/img/logo-72.png" alt="" width="40" height="40"><span><b>宏謙</b>健康減重指南</span></a>
    <nav class="nav" aria-label="主選單">
      <a href="/start/">開始前</a>
      <a href="/during/">療程中</a>
      <a href="/maintain/">維持期</a>
      <a href="/articles/">全部文章</a>
      <a href="/faq/">常見問題</a>
      <a class="ext" href="${site.clinic.website}">診所官網</a>
    </nav>
  </div>
</header>
<main id="main" class="${narrow ? 'wrap narrow' : 'wrap'}">
${body}
</main>
<footer class="foot">
  <div class="wrap foot-in">
    <div>
      <div class="foot-brand"><img src="/assets/img/logo-72.png" alt="" width="36" height="36"><b>${esc(site.clinic.name)}</b></div>
      <p>${esc(site.clinic.address)}<br>電話 ${esc(site.clinic.phone)}　LINE ${esc(site.clinic.lineId)}</p>
      <p class="hours">${esc(site.clinic.hours)}</p>
      <p class="links"><a href="${site.clinic.website}">診所官網</a> · <a href="${site.clinic.fb}">Facebook</a> · <a href="${site.clinic.line}">LINE 官方帳號</a></p>
    </div>
    <div class="cta-box">
      <p><b>想開始，或療程中有疑問？</b><br>用 LINE 告訴我們，個管師會協助安排門診與追蹤。</p>
      <a class="btn" href="${site.clinic.line}">用 LINE 聯絡宏謙</a>
    </div>
  </div>
  <div class="wrap disclaimer">${esc(site.disclaimer)}<br>© ${new Date().getFullYear()} ${esc(site.clinic.name)}</div>
</footer>
</body>
</html>`;
}

// ---------- components ----------
const card = a => `<a class="card" href="/articles/${a.slug}/">
  <span class="pill">${esc(catById[a.category]?.name || a.category)}</span>
  <h3>${esc(a.title)}</h3>
  <p>${esc(a.summary || '')}</p>
  <span class="meta">閱讀約 ${a.minutes} 分鐘</span>
</a>`;

const cardGrid = list => `<div class="grid">${list.map(card).join('\n')}</div>`;

const phaseCards = () => `<div class="phases">${PHASES.map(p => `<a class="phase" href="/${p.id}/">
  <span class="eyebrow">${esc(p.tagline)}</span>
  <h3>${esc(p.name)}</h3>
  <p>${esc(p.desc)}</p>
  <span class="more">看這個階段的內容 →</span>
</a>`).join('')}</div>`;

const faqList = (list, open) => `<div class="faq">${list.map((f, i) => `<details${open && i === 0 ? ' open' : ''}>
  <summary>${esc(f.q)}</summary>
  <div class="faq-a">${f.a}</div>
</details>`).join('\n')}</div>`;

const ctaBand = () => `<section class="band">
  <div>
    <h2>減重不是一個人的事</h2>
    <p>在宏謙，醫師、營養師與個管師分工照顧：醫師評估與調整治療，營養師為您做飲食規劃，個管師定期、主動關心您的狀況。我們有經驗豐富的團隊，幫您達成理想中的體重與健康。</p>
  </div>
  <div class="band-actions"><a class="btn light" href="${site.clinic.line}">用 LINE 預約評估</a><a class="btn outline" href="${site.clinic.website}">查看門診時間</a></div>
</section>`;

// ---------- pages ----------
rimraf(OUT); mkdirp(OUT);
copyDir(path.join(ROOT, 'assets'), path.join(OUT, 'assets'));
fs.writeFileSync(path.join(OUT, 'CNAME'), site.domain + '\n');
fs.writeFileSync(path.join(OUT, '.nojekyll'), '');
fs.writeFileSync(path.join(OUT, 'robots.txt'), `User-agent: *\nAllow: /\nSitemap: ${site.url}/sitemap.xml\n`);

const urls = ['/'];

// 首頁
{
  const byCat = CATS.map(c => ({ c, list: articles.filter(a => a.category === c.id) })).filter(x => x.list.length);
  const body = `
<section class="hero">
  <div class="hero-text">
    <span class="eyebrow">宏謙聯合診所 ・ 減重與代謝照護</span>
    <h1>把體重減下來，<br>也把健康留在身上。</h1>
    <p class="lede">這裡整理了宏謙減重門診在診間反覆說明的內容：療程前要知道的事、每一餐怎麼吃到足夠的蛋白質、不舒服時怎麼照顧自己、以及成果怎麼長期維持。由醫療團隊撰寫與審閱，隨門診經驗持續更新。</p>
    <div class="hero-actions"><a class="btn" href="/start/">我正準備開始</a><a class="btn ghost" href="/during/">我在療程中</a></div>
    <p class="hero-note">想先認識我們？醫師簡介、門診時間、交通方式都在 <a href="${site.clinic.website}">診所官網</a>。</p>
  </div>
  <figure class="hero-img"><img src="/assets/img/doctor-explain.jpg" alt="宏謙聯合診所院長在診間向患者說明報告" width="1000" height="750"><figcaption>報告不是印出來就交給您帶回家。每一份，都由醫師當面說明。</figcaption></figure>
</section>

<section>
  <div class="h2"><h2>今天，你想先了解什麼？</h2><small>依照您所在的階段</small></div>
  ${phaseCards()}
</section>

<section class="journey">
  <div class="h2"><h2>從減重，到把成果留下來</h2><small>宏謙的三階段照護</small></div>
  <ol class="steps">
    <li><b>適應期</b><span>用藥最初一到兩個月。重點是把噁心、便祕、注射部位反應這些常見不適處理好，讓治療穩定開始。</span></li>
    <li><b>穩定期</b><span>體重開始明顯下降。重點是蛋白質吃到份數、補足營養，保住肌肉、減少掉髮，同時開始安排運動。</span></li>
    <li><b>維持期</b><span>2 到 3 個月之後。重點是把阻力運動變成習慣，讓體重、血糖、血脂、血壓在停藥或減量後仍然穩定。</span></li>
  </ol>
</section>

${byCat.map(({ c, list }) => `<section id="${c.id}">
  <div class="h2"><h2>${esc(c.name)}</h2><small>${esc(c.desc)}</small></div>
  ${cardGrid(list)}
</section>`).join('\n')}

<section id="faq">
  <div class="h2"><h2>門診常見問題</h2><small><a href="/faq/">看全部 ${faqs.length} 題 →</a></small></div>
  ${faqList(faqs.slice(0, 5), false)}
</section>

${ctaBand()}

<section class="about">
  <div class="h2"><h2>關於宏謙聯合診所</h2></div>
  <div class="about-in">
    <p>${esc(site.clinic.about)}</p>
    <ul class="awards">${site.clinic.awards.map(a => `<li>${esc(a)}</li>`).join('')}</ul>
  </div>
</section>`;
  write('index.html', layout({ body, jsonld: { '@context': 'https://schema.org', '@type': 'MedicalClinic', name: site.clinic.name, url: site.clinic.website, telephone: site.clinic.phone, address: site.clinic.address } }));
}

// 階段頁
for (const p of PHASES) {
  const list = articles.filter(a => a.phases.includes(p.id));
  const body = `
<nav class="crumbs"><a href="/">首頁</a> › ${esc(p.name)}</nav>
<header class="page-head"><span class="eyebrow">${esc(p.tagline)}</span><h1>${esc(p.name)}</h1><p class="lede">${esc(p.intro)}</p></header>
${p.points ? `<ul class="points">${p.points.map(x => `<li>${esc(x)}</li>`).join('')}</ul>` : ''}
<div class="h2"><h2>這個階段建議先讀</h2></div>
${cardGrid(list)}
${ctaBand()}`;
  write(`${p.id}/index.html`, layout({ title: p.name, description: p.intro, canonical: `/${p.id}/`, body }));
  urls.push(`/${p.id}/`);
}

// 文章列表
{
  const body = `
<nav class="crumbs"><a href="/">首頁</a> › 全部文章</nav>
<header class="page-head"><h1>全部文章</h1><p class="lede">共 ${articles.length} 篇，依主題分類。每篇都由宏謙醫療團隊撰寫與審閱，並註明更新日期。</p></header>
${CATS.map(c => { const list = articles.filter(a => a.category === c.id); return list.length ? `<section><div class="h2"><h2>${esc(c.name)}</h2><small>${esc(c.desc)}</small></div>${cardGrid(list)}</section>` : ''; }).join('\n')}`;
  write('articles/index.html', layout({ title: '全部文章', description: '宏謙健康減重指南全部衛教文章', canonical: '/articles/', body }));
  urls.push('/articles/');
}

// 文章頁
for (const a of articles) {
  const related = articles.filter(x => x.slug !== a.slug && (x.category === a.category || x.phases.some(p => a.phases.includes(p)))).slice(0, 3);
  const body = `
<nav class="crumbs"><a href="/">首頁</a> › <a href="/articles/">全部文章</a> › ${esc(catById[a.category]?.name || '')}</nav>
<article class="post">
  <header class="post-head">
    <span class="pill">${esc(catById[a.category]?.name || a.category)}</span>
    <h1>${esc(a.title)}</h1>
    <p class="lede">${esc(a.summary || '')}</p>
    <p class="byline">${esc(site.author)}　·　更新於 ${esc(a.date || '')}　·　閱讀約 ${a.minutes} 分鐘</p>
  </header>
  <div class="prose">${a.html}</div>
  <div class="post-note">${esc(site.disclaimer)}</div>
</article>
${related.length ? `<section><div class="h2"><h2>延伸閱讀</h2></div>${cardGrid(related)}</section>` : ''}
${ctaBand()}`;
  const jsonld = { '@context': 'https://schema.org', '@type': 'MedicalWebPage', headline: a.title, description: a.summary, dateModified: a.date, inLanguage: 'zh-Hant', author: { '@type': 'Organization', name: site.clinic.name }, publisher: { '@type': 'Organization', name: site.clinic.name } };
  write(`articles/${a.slug}/index.html`, layout({ title: a.title, description: a.summary, canonical: `/articles/${a.slug}/`, body, narrow: true, jsonld }));
  urls.push(`/articles/${a.slug}/`);
}

// FAQ
{
  const body = `
<nav class="crumbs"><a href="/">首頁</a> › 常見問題</nav>
<header class="page-head"><h1>門診常見問題</h1><p class="lede">這些是宏謙減重門診最常被問到的問題。答案是一般性的衛教說明，您的狀況請以醫師當面評估為準。</p></header>
${faqList(faqs, true)}
${ctaBand()}`;
  const jsonld = { '@context': 'https://schema.org', '@type': 'FAQPage', mainEntity: faqs.map(f => ({ '@type': 'Question', name: f.q, acceptedAnswer: { '@type': 'Answer', text: f.a.replace(/<[^>]+>/g, '') } })) };
  write('faq/index.html', layout({ title: '常見問題', description: '宏謙減重門診常見問題', canonical: '/faq/', body, narrow: true, jsonld }));
  urls.push('/faq/');
}

// 404
write('404.html', layout({ title: '找不到這一頁', body: `<header class="page-head"><h1>找不到這一頁</h1><p class="lede">網址可能打錯了，或這篇文章已經移動。</p><p><a class="btn" href="/">回到首頁</a></p></header>` }));

// sitemap
fs.writeFileSync(path.join(OUT, 'sitemap.xml'), `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${urls.map(u => `  <url><loc>${site.url}${u}</loc></url>`).join('\n')}\n</urlset>\n`);

console.log(`built ${articles.length} articles, ${faqs.length} FAQs, ${urls.length} urls → docs/`);
