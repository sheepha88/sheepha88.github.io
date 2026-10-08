// 내비 활성 표시 + 이미지 확대 + 인쇄 시 케이스 상세 펼침. 없어도 콘텐츠는 모두 읽힌다.
(function () {
  var links = {};
  document.querySelectorAll('.topnav ul a').forEach(function (a) {
    links[a.getAttribute('href').slice(1)] = a;
  });
  var ids = Object.keys(links);
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (!e.isIntersecting) return;
        ids.forEach(function (id) { links[id].classList.toggle('active', id === e.target.id); });
      });
    }, { rootMargin: '-30% 0px -60% 0px' });
    ids.forEach(function (id) {
      var el = document.getElementById(id);
      if (el) io.observe(el);
    });
  }

  var dlg = document.getElementById('lightbox');
  if (dlg && dlg.showModal) {
    var big = dlg.querySelector('img');
    var cnt = dlg.querySelector('.lb-count');
    var bPrev = dlg.querySelector('.lb-prev');
    var bNext = dlg.querySelector('.lb-next');
    var group = [], cur = 0;
    function show(i) {
      cur = Math.min(Math.max(i, 0), group.length - 1);
      var a = group[cur], img = a.querySelector('img');
      big.src = a.getAttribute('href');
      big.alt = img ? img.alt : '';
      cnt.textContent = (cur + 1) + ' / ' + group.length;
      bPrev.disabled = cur === 0;
      bNext.disabled = cur === group.length - 1;
      dlg.classList.toggle('single', group.length < 2);
    }
    document.querySelectorAll('a.zoom').forEach(function (a) {
      a.addEventListener('click', function (ev) {
        ev.preventDefault();
        var scope = a.closest('[data-viewer], .product-images, .deliverables') || document;
        group = Array.prototype.slice.call(scope.querySelectorAll('a.zoom'));
        show(group.indexOf(a));
        dlg.showModal();
      });
    });
    bPrev.addEventListener('click', function () { show(cur - 1); });
    bNext.addEventListener('click', function () { show(cur + 1); });
    dlg.addEventListener('keydown', function (ev) {
      if (ev.key === 'ArrowRight') { ev.preventDefault(); show(cur + 1); }
      if (ev.key === 'ArrowLeft') { ev.preventDefault(); show(cur - 1); }
    });
    dlg.addEventListener('click', function (ev) { if (ev.target === dlg) dlg.close(); });
    dlg.addEventListener('close', function () {
      // 확대 창에서 본 슬라이드 위치로 뷰어를 맞춘다
      var a = group[cur], track = a && a.closest('.slides');
      if (track) track.scrollTo({ left: track.clientWidth * cur, behavior: 'auto' });
    });
  }

  // 슬라이드 뷰어: 이전/다음 버튼 + 방향키 (JS가 없어도 가로 스크롤로 열람 가능)
  document.querySelectorAll('[data-viewer]').forEach(function (v) {
    var track = v.querySelector('.slides');
    var slides = track.querySelectorAll('.slide');
    var n = slides.length;
    var nav = document.createElement('div');
    nav.className = 'viewer-nav';
    nav.innerHTML = '<button type="button" data-d="-1">이전</button><span class="count" aria-live="polite"></span><button type="button" data-d="1">다음</button>';
    v.appendChild(nav);
    v.classList.add('js');
    var prev = nav.querySelector('[data-d="-1"]');
    var next = nav.querySelector('[data-d="1"]');
    var count = nav.querySelector('.count');
    function current() { return Math.round(track.scrollLeft / track.clientWidth); }
    function update() {
      var i = Math.min(Math.max(current(), 0), n - 1);
      count.textContent = (i + 1) + ' / ' + n;
      prev.disabled = i === 0;
      next.disabled = i === n - 1;
    }
    function go(d) {
      var i = Math.min(Math.max(current() + d, 0), n - 1);
      track.scrollTo({ left: i * track.clientWidth, behavior: 'smooth' });
    }
    nav.addEventListener('click', function (ev) {
      var b = ev.target.closest('button');
      if (b) go(parseInt(b.getAttribute('data-d'), 10));
    });
    track.addEventListener('keydown', function (ev) {
      if (ev.key === 'ArrowRight') { ev.preventDefault(); go(1); }
      if (ev.key === 'ArrowLeft') { ev.preventDefault(); go(-1); }
    });
    track.addEventListener('scroll', function () { window.requestAnimationFrame(update); }, { passive: true });
    window.addEventListener('resize', update);
    update();
  });

  var opened = [];
  window.addEventListener('beforeprint', function () {
    opened = [];
    document.querySelectorAll('details').forEach(function (d) {
      if (!d.open) { d.open = true; opened.push(d); }
    });
  });
  window.addEventListener('afterprint', function () {
    opened.forEach(function (d) { d.open = false; });
  });
})();
