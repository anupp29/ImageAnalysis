document.addEventListener('DOMContentLoaded', () => {
  // ── Scroll-fade observer ────────────────────────────────────────────────
  const fades = document.querySelectorAll('.scroll-fade');
  const observer = new IntersectionObserver(
    (entries) => entries.forEach(e => { if (e.isIntersecting) e.target.classList.add('visible'); }),
    { threshold: 0.07 }
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

  // ── Code block enhancements: line numbers + copy button ────────────────
  document.querySelectorAll('pre').forEach(pre => {
    const code = pre.querySelector('code');
    if (!code) return;

    // Wrap each line in <span class="line"> so CSS counter works
    const html  = code.innerHTML;
    const lines = html.split('\n');
    // The last element is often an empty string from a trailing newline
    const trimmed = lines[lines.length - 1].trim() === '' ? lines.slice(0, -1) : lines;
    code.innerHTML = trimmed
      .map(ln => `<span class="line">${ln}</span>`)
      .join('\n');

    // aria-label for screen readers
    const lang = pre.getAttribute('data-lang');
    if (lang && !pre.hasAttribute('aria-label')) {
      pre.setAttribute('aria-label', `Code block (${lang})`);
    }

    // Copy button
    const btn = document.createElement('button');
    btn.className   = 'copy-btn';
    btn.textContent = 'copy';
    btn.setAttribute('aria-label', 'Copy code to clipboard');
    pre.appendChild(btn);

    btn.addEventListener('click', () => {
      const text = code.innerText || code.textContent;
      navigator.clipboard.writeText(text).then(() => {
        btn.textContent = 'copied!';
        btn.classList.add('copied');
        setTimeout(() => {
          btn.textContent = 'copy';
          btn.classList.remove('copied');
        }, 1800);
      }).catch(() => {
        btn.textContent = 'error';
        setTimeout(() => { btn.textContent = 'copy'; }, 1800);
      });
    });
  });
});