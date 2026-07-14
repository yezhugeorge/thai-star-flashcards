/**
 * 活人泰语点读卡 · 追星专版 - 应用逻辑
 * 激活码验证 / SPA路由 / 句子卡片 / 对话组件 / 搜索 / 收藏 / 音频播放
 */
(function () {
  'use strict';

  var DATA = window.APP_DATA || {};
  var CATEGORIES = DATA.CATEGORIES || [];
  var SUBCATS = DATA.SUBCATS || {};
  var SENTENCES = DATA.SENTENCES || [];
  var DIALOGUES = DATA.DIALOGUES || [];

  /* ===== Toast ===== */
  var toastEl = null, toastTimer = null;
  function showToast(msg) {
    if (!toastEl) {
      toastEl = document.createElement('div');
      toastEl.style.cssText = 'position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);background:rgba(0,0,0,.78);color:#fff;padding:12px 24px;border-radius:12px;font-size:14px;z-index:99999;pointer-events:none;opacity:0;transition:opacity .3s;white-space:nowrap;max-width:90vw;text-align:center';
      document.body.appendChild(toastEl);
    }
    toastEl.textContent = msg;
    toastEl.style.opacity = '1';
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { toastEl.style.opacity = '0'; }, 2000);
  }

  /* ===== 激活码 ===== */
  async function sha256(message) {
    var buf = new TextEncoder().encode(message);
    var hash = await crypto.subtle.digest('SHA-256', buf);
    return Array.from(new Uint8Array(hash)).map(function (b) {
      return b.toString(16).padStart(2, '0');
    }).join('');
  }

  function isActivated() {
    return localStorage.getItem('thai_star_activated') === 'true';
  }

  async function submitActivation() {
    var input = document.getElementById('activation-input');
    var hint = document.getElementById('activation-hint');
    var btn = document.querySelector('.activation-box__btn');
    var raw = input.value.trim().toUpperCase();

    if (!raw) { hint.textContent = '请输入激活码'; hint.classList.add('error'); return; }

    var clean = raw.replace(/[^A-Z0-9]/g, '');
    if (clean.length < 16) {
      hint.textContent = '激活码长度不对，请检查格式';
      hint.classList.add('error');
      return;
    }
    var code = 'THAI-' + clean.slice(4, 8) + '-' + clean.slice(8, 12) + '-' + clean.slice(12, 16);

    btn.textContent = '验证中...';
    btn.disabled = true;
    hint.textContent = '';
    hint.classList.remove('error');

    try {
      var hash = await sha256(code);
      var hashes = window.ACTIVATION_HASHES || [];
      if (hashes.indexOf(hash) !== -1) {
        localStorage.setItem('thai_star_activated', 'true');
        localStorage.setItem('thai_star_code', code);
        document.getElementById('activation-overlay').style.display = 'none';
        document.getElementById('app').style.display = 'block';
        initApp();
        showToast('激活成功！🎉');
      } else {
        hint.textContent = '激活码无效，请检查后重新输入';
        hint.classList.add('error');
        input.value = '';
        input.focus();
      }
    } catch (e) {
      hint.textContent = '验证失败，请确保使用 HTTPS 访问';
      hint.classList.add('error');
    }
    btn.textContent = '激 活';
    btn.disabled = false;
  }

  function initActivationInput() {
    var input = document.getElementById('activation-input');
    if (!input) return;
    input.addEventListener('keydown', function (e) {
      if (e.key === 'Enter') { e.preventDefault(); submitActivation(); }
    });
    input.addEventListener('input', function () {
      var v = this.value.toUpperCase().replace(/[^A-Z0-9]/g, '');
      var f = '';
      if (v.length > 0) f += v.substring(0, 4);
      if (v.length > 4) f += '-' + v.substring(4, 8);
      if (v.length > 8) f += '-' + v.substring(8, 12);
      if (v.length > 12) f += '-' + v.substring(12, 16);
      this.value = f;
    });
  }

  /* ===== 状态 ===== */
  var state = {
    route: 'home',
    cat: null,
    sub: null,
    searchQ: '',
    favs: loadFavs(),
    playingId: null,
    gender: localStorage.getItem('thai_star_gender') || 'female',
    speed: parseFloat(localStorage.getItem('thai_star_speed') || '1'),
    dlgId: null,
    dlgQueue: [],
    dlgIdx: 0,
  };

  /* ===== 收藏 ===== */
  function loadFavs() {
    try { return JSON.parse(localStorage.getItem('thai_star_favs') || '[]'); }
    catch (e) { return []; }
  }
  function saveFavs() {
    localStorage.setItem('thai_star_favs', JSON.stringify(state.favs));
    var badge = document.getElementById('fav-badge');
    if (state.favs.length > 0) { badge.textContent = state.favs.length; badge.style.display = 'flex'; }
    else { badge.style.display = 'none'; }
  }
  function toggleFav(id) {
    var i = state.favs.indexOf(id);
    if (i > -1) { state.favs.splice(i, 1); showToast('已取消收藏'); }
    else { state.favs.push(id); showToast('⭐ 已收藏'); }
    saveFavs();
    document.querySelectorAll('[data-fav="' + id + '"]').forEach(function (btn) {
      btn.classList.toggle('active', state.favs.indexOf(id) > -1);
      btn.textContent = state.favs.indexOf(id) > -1 ? '⭐' : '☆';
    });
  }
  function isFav(id) { return state.favs.indexOf(id) > -1; }

  /* ===== 音频 ===== */
  var currentAudio = null;
  var thaiVoice = null;

  function loadVoices() {
    if (!('speechSynthesis' in window)) return;
    var voices = speechSynthesis.getVoices();
    thaiVoice = voices.find(function (v) { return v.lang === 'th-TH'; }) ||
      voices.find(function (v) { return v.lang && v.lang.startsWith('th'); });
  }
  if ('speechSynthesis' in window) {
    loadVoices();
    speechSynthesis.onvoiceschanged = loadVoices;
  }

  function audioPath(id) {
    var dir = state.gender === 'male' ? 'audio/male/' : 'audio/';
    return dir + id + '.mp3';
  }

  function playAudio(id) {
    if (state.playingId === id) { stopAudio(); return; }
    stopAudio();
    var a = new Audio();
    a.src = audioPath(id);
    a.playbackRate = state.speed;
    a.onplay = function () { state.playingId = id; updatePlayBtns(id, true); };
    a.onended = function () { state.playingId = null; updatePlayBtns(id, false); };
    a.onerror = function () { state.playingId = null; updatePlayBtns(id, false); playTTS(id); };
    currentAudio = a;
    a.play().catch(function () { playTTS(id); });
  }

  function playTTS(id) {
    if (!('speechSynthesis' in window)) { showToast('当前浏览器不支持语音'); return; }
    // 句子
    var s = SENTENCES.find(function (x) { return x.id === id; });
    var text = s ? s.thai : null;
    // 对话轮次
    if (!text) {
      var parts = id.split('-');
      var lastPart = parts[parts.length - 1];
      var dlgId = id.substring(0, id.length - lastPart.length - 1);
      var dlg = DIALOGUES.find(function (d) { return d.id === dlgId; });
      if (dlg && dlg.turns[parseInt(lastPart)]) text = dlg.turns[parseInt(lastPart)].t;
    }
    if (!text) return;
    if (!thaiVoice) loadVoices();
    var u = new SpeechSynthesisUtterance(text);
    u.lang = 'th-TH';
    u.rate = 0.8;
    if (thaiVoice) u.voice = thaiVoice;
    u.onstart = function () { state.playingId = id; updatePlayBtns(id, true); };
    u.onend = function () { state.playingId = null; updatePlayBtns(id, false); };
    u.onerror = function () { state.playingId = null; updatePlayBtns(id, false); };
    speechSynthesis.speak(u);
  }

  function stopAudio() {
    if ('speechSynthesis' in window) speechSynthesis.cancel();
    if (currentAudio) { currentAudio.pause(); currentAudio = null; }
    if (state.playingId) { updatePlayBtns(state.playingId, false); state.playingId = null; }
  }

  function updatePlayBtns(id, playing) {
    document.querySelectorAll('[data-play="' + id + '"]').forEach(function (btn) {
      btn.classList.toggle('playing', playing);
      btn.textContent = playing ? '⏸' : '▶';
    });
  }

  /* ===== 对话播放 ===== */
  function playTurn(dlgId, idx) {
    var audioId = dlgId + '-' + idx;
    if (state.playingId === audioId) { stopAudio(); return; }
    stopAudio();
    playAudio(audioId);
  }

  function playDialogueAll(dlgId) {
    var dlg = DIALOGUES.find(function (d) { return d.id === dlgId; });
    if (!dlg) return;
    stopDialoguePlay();
    stopAudio();
    state.dlgId = dlgId;
    state.dlgQueue = dlg.turns.map(function (_, i) { return i; });
    state.dlgIdx = 0;
    document.getElementById('dialogue-player').style.display = 'flex';
    playNextTurn();
  }

  function playNextTurn() {
    if (state.dlgIdx >= state.dlgQueue.length) { stopDialoguePlay(); return; }
    var idx = state.dlgQueue[state.dlgIdx];
    var dlg = DIALOGUES.find(function (d) { return d.id === state.dlgId; });
    if (!dlg || !dlg.turns[idx]) { stopDialoguePlay(); return; }
    var turn = dlg.turns[idx];
    var audioId = state.dlgId + '-' + idx;

    document.getElementById('dialogue-player-text').textContent = turn.s + ': ' + turn.c;

    var a = new Audio();
    a.src = audioPath(audioId);
    a.playbackRate = state.speed;
    a.onended = function () { state.dlgIdx++; playNextTurn(); };
    a.onerror = function () {
      // TTS fallback for dialogue
      if ('speechSynthesis' in window) {
        if (!thaiVoice) loadVoices();
        var u = new SpeechSynthesisUtterance(turn.t);
        u.lang = 'th-TH';
        u.rate = 0.8;
        if (thaiVoice) u.voice = thaiVoice;
        u.onend = function () { state.dlgIdx++; playNextTurn(); };
        u.onerror = function () { state.dlgIdx++; playNextTurn(); };
        speechSynthesis.speak(u);
      } else {
        state.dlgIdx++; playNextTurn();
      }
    };
    currentAudio = a;
    a.play().catch(function () {
      if ('speechSynthesis' in window) {
        var u = new SpeechSynthesisUtterance(turn.t);
        u.lang = 'th-TH'; u.rate = 0.8;
        if (thaiVoice) u.voice = thaiVoice;
        u.onend = function () { state.dlgIdx++; playNextTurn(); };
        u.onerror = function () { state.dlgIdx++; playNextTurn(); };
        speechSynthesis.speak(u);
      } else { state.dlgIdx++; playNextTurn(); }
    });
  }

  function stopDialoguePlay() {
    if (currentAudio) { currentAudio.pause(); currentAudio = null; }
    if ('speechSynthesis' in window) speechSynthesis.cancel();
    state.dlgId = null;
    state.dlgQueue = [];
    state.dlgIdx = 0;
    var p = document.getElementById('dialogue-player');
    if (p) p.style.display = 'none';
  }

  /* ===== 性别 / 速度 ===== */
  function setVoiceGender(g) {
    stopAudio();
    stopDialoguePlay();
    state.gender = g;
    localStorage.setItem('thai_star_gender', g);
    showToast(g === 'male' ? '👨 已切换男声' : '👩 已切换女声');
    document.querySelectorAll('.gender-bar__btn').forEach(function (btn) {
      btn.classList.toggle('active', btn.dataset.gender === g);
    });
    document.querySelectorAll('.speed-tab[data-gender]').forEach(function (btn) {
      btn.classList.toggle('active', btn.dataset.gender === g);
    });
  }

  function setPlaybackSpeed(s) {
    state.speed = s;
    localStorage.setItem('thai_star_speed', s.toString());
    if (currentAudio) currentAudio.playbackRate = s;
    document.querySelectorAll('.speed-tab[data-speed]').forEach(function (btn) {
      btn.classList.toggle('active', parseFloat(btn.dataset.speed) === s);
    });
    showToast('🎵 ' + (s === 0.5 ? '0.5x 慢速' : s === 0.75 ? '0.75x' : '1x 正常'));
  }

  /* ===== 大字卡 ===== */
  function showLargeCard(id) {
    var s = SENTENCES.find(function (x) { return x.id === id; });
    if (!s) return;
    var playing = state.playingId === id;
    var overlay = document.getElementById('largecard-overlay');
    var body = document.getElementById('largecard-content');
    body.innerHTML =
      '<button class="largecard__close" onclick="closeLargeCard()">✕</button>' +
      '<div class="largecard__thai">' + s.thai + '</div>' +
      '<div class="largecard__cn">' + s.cn + '</div>' +
      '<button class="largecard__play ' + (playing ? 'playing' : '') + '" onclick="playAudio(\'' + id + '\')">' + (playing ? '⏸' : '▶') + '</button>';
    overlay.style.display = 'flex';
    document.body.style.overflow = 'hidden';
  }
  function closeLargeCard() {
    document.getElementById('largecard-overlay').style.display = 'none';
    document.body.style.overflow = '';
  }
  function closeLargeCardOnOverlay(e) {
    if (e.target === document.getElementById('largecard-overlay')) closeLargeCard();
  }

  /* ===== 设置 ===== */
  function openSettings() {
    document.getElementById('settings-modal').style.display = 'flex';
  }
  function closeSettings(e) {
    if (e && e.target && e.target.id !== 'settings-modal') return;
    document.getElementById('settings-modal').style.display = 'none';
  }

  /* ===== 搜索 ===== */
  var searchTimer = null;
  function openSearch() {
    stopAudio();
    state.route = 'search';
    state.searchQ = '';
    document.getElementById('search-bar').style.display = 'flex';
    document.getElementById('back-btn').style.display = 'block';
    document.getElementById('page-title').textContent = '🔍 搜索';
    var input = document.getElementById('search-input');
    input.value = '';

    var suggestions = ['你好', '加油', '可爱', '演唱会', '签售', 'CP', '接机', '安利', '安可', '打榜', '甜', '帅'];
    var content = document.getElementById('content');
    content.innerHTML =
      '<div class="section-header">🔥 热门搜索</div>' +
      '<div class="sub-tabs" style="flex-wrap:wrap">' +
      suggestions.map(function (s) {
        return '<span class="sub-tab" onclick="quickSearch(\'' + s + '\')">' + s + '</span>';
      }).join('') +
      '</div>' +
      '<div class="search-results" id="search-results"></div>';

    // Bind input
    var newInput = input.cloneNode(true);
    input.parentNode.replaceChild(newInput, input);
    newInput.addEventListener('input', function () {
      clearTimeout(searchTimer);
      var val = this.value;
      searchTimer = setTimeout(function () { performSearch(val); }, 200);
    });
    newInput.addEventListener('keydown', function (e) {
      if (e.key === 'Enter') this.blur();
    });
    setTimeout(function () { newInput.focus(); }, 100);
  }

  function closeSearch() {
    document.getElementById('search-bar').style.display = 'none';
    goHome();
  }

  function quickSearch(term) {
    var input = document.getElementById('search-input');
    if (input) input.value = term;
    performSearch(term);
  }

  function performSearch(query) {
    var q = query.trim().toLowerCase();
    var container = document.getElementById('search-results');
    if (!container) return;
    if (!q) { container.innerHTML = ''; return; }

    var sResults = SENTENCES.filter(function (s) {
      return s.cn.toLowerCase().indexOf(q) > -1 || s.thai.toLowerCase().indexOf(q) > -1;
    });
    var dResults = DIALOGUES.filter(function (d) {
      if (d.title.toLowerCase().indexOf(q) > -1) return true;
      if (d.scene.toLowerCase().indexOf(q) > -1) return true;
      return d.turns.some(function (t) {
        return t.c.toLowerCase().indexOf(q) > -1 || t.t.toLowerCase().indexOf(q) > -1;
      });
    });

    var html = '';
    if (sResults.length > 0) {
      html += '<div class="section-header">📝 句子 (' + sResults.length + ')</div>';
      html += sResults.map(function (s) {
        var cat = CATEGORIES.find(function (c) { return c.id === s.cat; });
        return '<div class="search-result-item">' +
          '<div class="search-result-item__thai">' + s.thai + '</div>' +
          '<div class="search-result-item__cn">' + s.cn + '</div>' +
          '<div class="search-result-item__cat">' + (cat ? cat.icon + ' ' + cat.name : '') + '</div>' +
          '<div style="margin-top:8px;display:flex;gap:8px;align-items:center">' +
          '<button class="sentence-card__play" style="width:36px;height:36px;font-size:16px" data-play="' + s.id + '" onclick="playAudio(\'' + s.id + '\')">▶</button>' +
          '<button class="sentence-card__expand" onclick="showLargeCard(\'' + s.id + '\')">🔍</button>' +
          '<button class="sentence-card__fav ' + (isFav(s.id) ? 'active' : '') + '" data-fav="' + s.id + '" onclick="toggleFav(\'' + s.id + '\')">' + (isFav(s.id) ? '⭐' : '☆') + '</button>' +
          '</div></div>';
      }).join('');
    }
    if (dResults.length > 0) {
      html += '<div class="section-header">💬 对话 (' + dResults.length + ')</div>';
      html += dResults.map(function (d) {
        var cat = CATEGORIES.find(function (c) { return c.id === d.cat; });
        return '<div class="search-result-item" onclick="goToCategory(\'' + d.cat + '\')" style="cursor:pointer">' +
          '<div class="search-result-item__thai">💬 ' + d.title + '</div>' +
          '<div class="search-result-item__cn">' + d.scene + '</div>' +
          '<div class="search-result-item__cat">' + (cat ? cat.icon + ' ' + cat.name : '') + '</div>' +
          '</div>';
      }).join('');
    }
    if (sResults.length === 0 && dResults.length === 0) {
      html = '<div class="fav-empty"><div class="fav-empty__icon">🔍</div><p>没有找到相关内容</p><p style="font-size:13px;margin-top:4px">试试搜索"你好""加油""CP"等</p></div>';
    }
    container.innerHTML = html;
  }

  /* ===== 收藏页 ===== */
  function openFavorites() {
    stopAudio();
    state.route = 'favorites';
    document.getElementById('search-bar').style.display = 'none';
    document.getElementById('back-btn').style.display = 'block';
    document.getElementById('page-title').textContent = '⭐ 收藏';

    var content = document.getElementById('content');
    var favSentences = state.favs
      .map(function (id) { return SENTENCES.find(function (s) { return s.id === id; }); })
      .filter(Boolean);

    if (favSentences.length === 0) {
      content.innerHTML = '<div class="fav-empty"><div class="fav-empty__icon">⭐</div><p>还没有收藏</p><p style="font-size:13px;margin-top:4px">点击句子卡片上的星星即可收藏</p></div>';
      return;
    }
    content.innerHTML = '<div class="section-header">已收藏 ' + favSentences.length + ' 句</div>' +
      favSentences.map(renderSentenceCard).join('');
  }

  /* ===== 路由 ===== */
  function goHome() {
    stopAudio();
    stopDialoguePlay();
    state.route = 'home';
    state.sub = null;
    document.getElementById('search-bar').style.display = 'none';
    document.getElementById('back-btn').style.display = 'none';
    document.getElementById('page-title').textContent = '活人泰语 · 追星专版';
    renderHome();
    window.scrollTo(0, 0);
  }

  function goBack() {
    if (state.route === 'category') {
      // If in subcategory, go back to all; else go home
      if (state.sub) { state.sub = null; renderCategoryPage(state.cat); }
      else { goHome(); }
    } else {
      goHome();
    }
  }

  function goToCategory(catId) {
    stopAudio();
    stopDialoguePlay();
    state.route = 'category';
    state.cat = catId;
    state.sub = null;
    var cat = CATEGORIES.find(function (c) { return c.id === catId; });
    document.getElementById('search-bar').style.display = 'none';
    document.getElementById('back-btn').style.display = 'block';
    document.getElementById('page-title').textContent = cat ? cat.icon + ' ' + cat.name : '';
    renderCategoryPage(catId);
    window.scrollTo(0, 0);
  }

  function selectSub(catId, subId) {
    state.sub = subId;
    renderCategoryPage(catId);
    window.scrollTo(0, 0);
  }

  /* ===== 首页 ===== */
  function renderHome() {
    var content = document.getElementById('content');
    var html =
      '<div class="home-header">' +
      '<div class="home-header__title">🇹🇭 泰国追星泰语</div>' +
      '<div class="home-header__desc">点一下就能听 · BL/GL/追星/演唱会/社交/线下</div>' +
      '</div><div class="cat-grid">';

    CATEGORIES.forEach(function (cat) {
      var sc = SENTENCES.filter(function (s) { return s.cat === cat.id; }).length;
      var dc = DIALOGUES.filter(function (d) { return d.cat === cat.id; }).length;
      html +=
        '<div class="cat-card" onclick="goToCategory(\'' + cat.id + '\')">' +
        '<div class="cat-card__icon">' + cat.icon + '</div>' +
        '<div class="cat-card__name">' + cat.name + '</div>' +
        '<div class="cat-card__desc">' + cat.desc + '</div>' +
        '<div class="cat-card__count">📝 ' + sc + '句 · 💬 ' + dc + '对话</div>' +
        '</div>';
    });
    html += '</div>';
    content.innerHTML = html;
  }

  /* ===== 分类页 ===== */
  function renderCategoryPage(catId) {
    var subcats = SUBCATS[catId] || [];
    var content = document.getElementById('content');

    // Sub tabs
    var html = '<div class="sub-tabs">';
    html += '<span class="sub-tab ' + (!state.sub ? 'active' : '') + '" onclick="selectSub(\'' + catId + '\',null)">全部</span>';
    subcats.forEach(function (sub) {
      html += '<span class="sub-tab ' + (state.sub === sub.id ? 'active' : '') + '" onclick="selectSub(\'' + catId + '\',\'' + sub.id + '\')">' + sub.name + '</span>';
    });
    html += '</div>';

    // Sentences
    var sentences = SENTENCES.filter(function (s) { return s.cat === catId; });
    if (state.sub) sentences = sentences.filter(function (s) { return s.sub === state.sub; });

    if (sentences.length > 0) {
      html += '<div class="section-header">📝 实用句子 (' + sentences.length + ')</div>';
      html += sentences.map(renderSentenceCard).join('');
    }

    // Dialogues (only show when "全部" is selected)
    var dialogues = DIALOGUES.filter(function (d) { return d.cat === catId; });
    if (dialogues.length > 0 && !state.sub) {
      html += '<div class="section-header">💬 对话场景 (' + dialogues.length + ')</div>';
      html += dialogues.map(renderDialogueCard).join('');
    }

    if (sentences.length === 0 && (state.sub && dialogues.length === 0)) {
      html += '<div class="fav-empty"><div class="fav-empty__icon">📝</div><p>该分类暂无内容</p></div>';
    }

    content.innerHTML = html;
  }

  /* ===== 句子卡片 ===== */
  function renderSentenceCard(s) {
    var playing = state.playingId === s.id ? 'playing' : '';
    var favActive = isFav(s.id) ? 'active' : '';
    var favIcon = isFav(s.id) ? '⭐' : '☆';
    return '<div class="sentence-card">' +
      '<div class="sentence-card__thai">' + s.thai + '</div>' +
      '<div class="sentence-card__cn">' + s.cn + '</div>' +
      '<div class="sentence-card__actions">' +
      '<button class="sentence-card__play ' + playing + '" data-play="' + s.id + '" onclick="playAudio(\'' + s.id + '\')">' + (playing ? '⏸' : '▶') + '</button>' +
      '<button class="sentence-card__fav ' + favActive + '" data-fav="' + s.id + '" onclick="toggleFav(\'' + s.id + '\')">' + favIcon + '</button>' +
      '<button class="sentence-card__expand" onclick="showLargeCard(\'' + s.id + '\')">🔍</button>' +
      '</div></div>';
  }

  /* ===== 对话卡片 ===== */
  function renderDialogueCard(d) {
    var turnsHtml = d.turns.map(function (turn, i) {
      var audioId = d.id + '-' + i;
      var playing = state.playingId === audioId ? 'playing' : '';
      return '<div class="dialogue-turn">' +
        '<div class="dialogue-turn__speaker">' + turn.s + '</div>' +
        '<div class="dialogue-turn__content">' +
        '<div class="dialogue-turn__thai">' + turn.t + '</div>' +
        '<div class="dialogue-turn__cn">' + turn.c + '</div>' +
        '</div>' +
        '<button class="dialogue-turn__play ' + playing + '" data-play="' + audioId + '" onclick="playTurn(\'' + d.id + '\',' + i + ')">' + (playing ? '⏸' : '▶') + '</button>' +
        '</div>';
    }).join('');

    return '<div class="dialogue-card">' +
      '<div class="dialogue-card__header" onclick="toggleDialogue(this)">' +
      '<div class="dialogue-card__icon">💬</div>' +
      '<div class="dialogue-card__info">' +
      '<div class="dialogue-card__title">' + d.title + '</div>' +
      '<div class="dialogue-card__scene">' + d.scene + '</div>' +
      '</div>' +
      '<div class="dialogue-card__arrow">▼</div>' +
      '</div>' +
      '<div class="dialogue-card__body">' +
      '<button class="dialogue-card__play-all" onclick="playDialogueAll(\'' + d.id + '\')">▶ 连续播放全部</button>' +
      turnsHtml +
      '</div></div>';
  }

  function toggleDialogue(headerEl) {
    var body = headerEl.nextElementSibling;
    var arrow = headerEl.querySelector('.dialogue-card__arrow');
    body.classList.toggle('open');
    arrow.classList.toggle('open');
  }

  /* ===== 全局暴露 ===== */
  window.submitActivation = submitActivation;
  window.goBack = goBack;
  window.openSearch = openSearch;
  window.closeSearch = closeSearch;
  window.openFavorites = openFavorites;
  window.openSettings = openSettings;
  window.closeSettings = closeSettings;
  window.setVoiceGender = setVoiceGender;
  window.setPlaybackSpeed = setPlaybackSpeed;
  window.closeLargeCardOnOverlay = closeLargeCardOnOverlay;
  window.stopDialoguePlay = stopDialoguePlay;
  window.playAudio = playAudio;
  window.toggleFav = toggleFav;
  window.showLargeCard = showLargeCard;
  window.closeLargeCard = closeLargeCard;
  window.goToCategory = goToCategory;
  window.selectSub = selectSub;
  window.quickSearch = quickSearch;
  window.playTurn = playTurn;
  window.playDialogueAll = playDialogueAll;
  window.toggleDialogue = toggleDialogue;

  /* ===== 初始化 ===== */
  function initApp() {
    renderHome();
    saveFavs(); // 更新badge
    // 恢复性别/速度按钮状态
    document.querySelectorAll('.gender-bar__btn').forEach(function (btn) {
      btn.classList.toggle('active', btn.dataset.gender === state.gender);
    });
    document.querySelectorAll('.speed-tab[data-speed]').forEach(function (btn) {
      btn.classList.toggle('active', parseFloat(btn.dataset.speed) === state.speed);
    });
    document.querySelectorAll('.speed-tab[data-gender]').forEach(function (btn) {
      btn.classList.toggle('active', btn.dataset.gender === state.gender);
    });
  }

  function init() {
    if (isActivated()) {
      document.getElementById('activation-overlay').style.display = 'none';
      document.getElementById('app').style.display = 'block';
      initApp();
    } else {
      initActivationInput();
      var input = document.getElementById('activation-input');
      if (input) input.focus();
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();
