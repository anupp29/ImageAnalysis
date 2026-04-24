document.addEventListener('DOMContentLoaded', () => {
  // ── Scroll-fade observer ────────────────────────────────────────────────
  const fades = document.querySelectorAll('.scroll-fade');
  const observer = new IntersectionObserver(
    (entries) => entries.forEach(e => { if (e.isIntersecting) e.target.classList.add('visible'); }),
    { threshold: 0.05 }
  );
  fades.forEach(el => observer.observe(el));

  // ── Active nav link on scroll ───────────────────────────────────────────
  const links    = document.querySelectorAll('.nav-links a[href^="#"]');
  const sections = [...links].map(l => document.querySelector(l.getAttribute('href'))).filter(Boolean);
  const onScroll = () => {
    const y = window.scrollY + 120;
    let cur = sections[0];
    sections.forEach(s => { if (s.offsetTop <= y) cur = s; });
    links.forEach(l => {
      l.classList.toggle('active', l.getAttribute('href') === '#' + cur?.id);
    });
  };
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  // ── Mobile hamburger ────────────────────────────────────────────────────
  const hamburger = document.querySelector('.nav-hamburger');
  const navLinks  = document.querySelector('.nav-links');
  if (hamburger && navLinks) {
    hamburger.addEventListener('click', () => {
      const open = hamburger.classList.toggle('open');
      navLinks.classList.toggle('open', open);
      hamburger.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
    navLinks.querySelectorAll('a').forEach(a => {
      a.addEventListener('click', () => {
        hamburger.classList.remove('open');
        navLinks.classList.remove('open');
        hamburger.setAttribute('aria-expanded', 'false');
      });
    });
  }

  // ── Code block enhancements: LaTeX listing header + line numbers + copy ─
  const LANG_LABELS = {
    python: 'Python',
    tree:   'File Tree',
    bash:   'Shell',
    js:     'JavaScript',
    json:   'JSON',
    text:   'Plain Text',
  };

  let listingCount = 0;

  document.querySelectorAll('pre').forEach(pre => {
    const code = pre.querySelector('code');
    if (!code) return;

    // Wrap each line in <span class="line"> for CSS counter
    const html    = code.innerHTML;
    const lines   = html.split('\n');
    const trimmed = lines[lines.length - 1].trim() === '' ? lines.slice(0, -1) : lines;
    code.innerHTML = trimmed.map(ln => `<span class="line">${ln}</span>`).join('\n');

    const lang      = (pre.getAttribute('data-lang') || '').toLowerCase();
    const caption   = pre.getAttribute('data-caption') || '';
    const langLabel = LANG_LABELS[lang] || (lang ? lang.toUpperCase() : 'Code');
    const isTree    = lang === 'tree';

    if (!isTree) listingCount++;

    // Build listing header
    const header = document.createElement('div');
    header.className = 'listing-header';

    const labelDiv = document.createElement('div');
    labelDiv.className = 'listing-label';

    if (!isTree) {
      const numSpan = document.createElement('span');
      numSpan.className = 'listing-num';
      numSpan.textContent = `Listing ${String(listingCount).padStart(2, '0')}`;
      labelDiv.appendChild(numSpan);

      const dot = document.createElement('span');
      dot.className = 'listing-dot';
      labelDiv.appendChild(dot);
    }

    if (caption) {
      const desc = document.createElement('span');
      desc.className = 'listing-desc';
      desc.textContent = caption;
      labelDiv.appendChild(desc);
    }

    const langBadge = document.createElement('span');
    langBadge.className = 'listing-lang';
    langBadge.textContent = langLabel;

    // Copy button
    const btn = document.createElement('button');
    btn.className   = 'copy-btn';
    btn.textContent = 'copy';
    btn.setAttribute('aria-label', 'Copy code to clipboard');

    btn.addEventListener('click', () => {
      const text = code.innerText || code.textContent;
      navigator.clipboard.writeText(text).then(() => {
        btn.textContent = 'copied ✓';
        btn.classList.add('copied');
        setTimeout(() => { btn.textContent = 'copy'; btn.classList.remove('copied'); }, 1800);
      }).catch(() => {
        btn.textContent = 'error';
        setTimeout(() => { btn.textContent = 'copy'; }, 1800);
      });
    });

    header.appendChild(labelDiv);
    header.appendChild(langBadge);
    header.appendChild(btn);

    // Wrap pre in .listing-wrap and prepend header
    const wrap = document.createElement('div');
    wrap.className = 'listing-wrap';
    if (!pre.hasAttribute('aria-label')) {
      pre.setAttribute('aria-label', `${langLabel} code block`);
    }
    pre.parentNode.insertBefore(wrap, pre);
    wrap.appendChild(header);
    wrap.appendChild(pre);
  });

  // ── Circuit diagram blocks — inject header bar ──────────────────────────
  document.querySelectorAll('.algorithm-box .circuit-diagram').forEach(cd => {
    const box = cd.closest('.algorithm-box');
    if (!box) return;
    const title = box.querySelector('h4')?.textContent || 'Quantum Circuit';

    const header = document.createElement('div');
    header.className = 'circuit-diagram-header';
    header.innerHTML =
      `<span class="cdh-icon">⬡</span><span class="cdh-title">Conceptual Circuit — ${title}</span>`;

    const wrap = document.createElement('div');
    wrap.className = 'circuit-diagram-wrap';
    cd.parentNode.insertBefore(wrap, cd);
    wrap.appendChild(header);
    wrap.appendChild(cd);
  });
});
