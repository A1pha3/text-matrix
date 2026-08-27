(() => {
  'use strict';

  const articleEnd = document.querySelector('[data-article-end]');
  if (!articleEnd) return;

  const track = (eventName, parameters = {}) => {
    if (typeof window.gtag !== 'function') return;
    window.gtag('event', eventName, {
      source_page: window.location.pathname,
      source_section: 'article_end',
      ...parameters,
    });
  };

  const referrerPath = () => {
    if (!document.referrer) return '';
    try {
      return new URL(document.referrer).pathname;
    } catch {
      return '';
    }
  };

  const initAnalytics = () => {
    if ('IntersectionObserver' in window) {
      const exposureObserver = new IntersectionObserver((entries) => {
        if (!entries.some((entry) => entry.isIntersecting)) return;
        track('article_end_view', {
          content_type: articleEnd.dataset.contentType || 'post',
          topic: articleEnd.querySelector('[data-topic]')?.dataset.topic || '',
        });
        exposureObserver.disconnect();
      }, { threshold: 0.1 });
      exposureObserver.observe(articleEnd);
    }

    document.addEventListener('click', (event) => {
      const link = event.target.closest('a[data-event]');
      if (!link) return;
      track(link.dataset.event, {
        target_kind: link.dataset.targetKind || '',
        target_url: link.dataset.target || link.getAttribute('href') || '',
        position: link.dataset.position || '',
        topic: link.dataset.topic || '',
      });
    }, false);

    const content = document.getElementById('content');
    if (!content) return;

    let visibleStarted = document.visibilityState === 'visible' ? performance.now() : null;
    let visibleDuration = 0;
    let readingProgress = 0;
    let engaged = false;
    let framePending = false;

    const updateProgress = () => {
      framePending = false;
      const rect = content.getBoundingClientRect();
      const viewed = Math.max(0, Math.min(content.scrollHeight, window.innerHeight - rect.top));
      readingProgress = content.scrollHeight > 0 ? viewed / content.scrollHeight : 0;
    };

    const requestProgressUpdate = () => {
      if (framePending) return;
      framePending = true;
      window.requestAnimationFrame(updateProgress);
    };

    const currentVisibleDuration = () => visibleDuration + (
      visibleStarted === null ? 0 : performance.now() - visibleStarted
    );

    const engagementTimer = window.setInterval(() => {
      if (engaged || currentVisibleDuration() < 10000 || readingProgress < 0.25) return;
      engaged = true;
      window.clearInterval(engagementTimer);
      track('article_read_engaged', {
        referrer_path: referrerPath(),
      });
    }, 1000);

    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'visible') {
        visibleStarted = performance.now();
      } else if (visibleStarted !== null) {
        visibleDuration += performance.now() - visibleStarted;
        visibleStarted = null;
      }
    }, false);
    window.addEventListener('scroll', requestProgressUpdate, { passive: true });
    window.addEventListener('resize', requestProgressUpdate, { passive: true });
    requestProgressUpdate();
  };

  const initShare = () => {
    const button = articleEnd.querySelector('[data-share]');
    const status = articleEnd.querySelector('.post-share-status');
    if (!button || !status) return;

    let statusTimer = 0;
    const announce = (message) => {
      window.clearTimeout(statusTimer);
      status.textContent = message;
      statusTimer = window.setTimeout(() => {
        status.textContent = '';
      }, 4000);
    };

    const copyURL = async (url) => {
      if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(url);
        return;
      }
      const input = document.createElement('textarea');
      input.value = url;
      input.setAttribute('readonly', '');
      input.style.position = 'fixed';
      input.style.opacity = '0';
      document.body.appendChild(input);
      input.select();
      const copied = document.execCommand('copy');
      input.remove();
      if (!copied) throw new Error('copy failed');
    };

    button.hidden = false;
    button.addEventListener('click', async () => {
      const title = button.dataset.shareTitle || document.title;
      const url = button.dataset.shareUrl || window.location.href;
      try {
        if (typeof navigator.share === 'function') {
          await navigator.share({ title, url });
          announce('已打开系统分享');
          track('article_share', { method: 'system', state: 'success' });
          return;
        }
        await copyURL(url);
        announce('链接已复制');
        track('article_share', { method: 'clipboard', state: 'success' });
      } catch (error) {
        if (error?.name === 'AbortError') {
          announce('已取消分享');
          track('article_share', { method: 'system', state: 'cancelled' });
          return;
        }
        announce('无法自动复制，请从地址栏复制链接');
        track('article_share', { method: 'clipboard', state: 'failed' });
      }
    }, false);
  };

  const initDiscussion = () => {
    const section = document.getElementById('comments');
    const heading = document.getElementById('discussion-title');
    const root = document.querySelector('[data-giscus-root]');
    if (!section || !heading || !root) return;

    const status = section.querySelector('.giscus-status');
    const fallback = section.querySelector('[data-giscus-fallback]');
    const retryButton = section.querySelector('[data-giscus-retry]');
    let state = 'idle';
    let attempt = 0;
    let timeoutID = 0;
    let iframeObserver = null;
    let messageHandler = null;
    let loadStartedAt = 0;

    const setStatus = (message) => {
      if (!status) return;
      status.textContent = message;
      status.hidden = !message;
    };

    const clearWatchers = () => {
      window.clearTimeout(timeoutID);
      timeoutID = 0;
      iframeObserver?.disconnect();
      iframeObserver = null;
      if (messageHandler) window.removeEventListener('message', messageHandler);
      messageHandler = null;
    };

    const removeWidget = () => {
      root.querySelectorAll('script[data-giscus-loader], .giscus').forEach((node) => node.remove());
    };

    const emitCommentState = (nextState) => {
      track('article_comment_state', {
        state: nextState,
        duration_ms: loadStartedAt ? Math.round(performance.now() - loadStartedAt) : 0,
        attempt,
      });
    };

    const markReady = () => {
      if (state !== 'loading') return;
      state = 'ready';
      clearWatchers();
      root.setAttribute('aria-busy', 'false');
      setStatus('');
      if (fallback) fallback.hidden = true;
      emitCommentState('ready');
    };

    const markFailed = () => {
      if (state !== 'loading') return;
      state = 'failed';
      clearWatchers();
      removeWidget();
      root.setAttribute('aria-busy', 'false');
      setStatus('');
      if (fallback) fallback.hidden = false;
      emitCommentState('failed');
    };

    const watchIframe = (iframe) => {
      if (iframe.dataset.articleEndObserved === 'true') return;
      iframe.dataset.articleEndObserved = 'true';
      iframe.addEventListener('load', markReady, { once: true });
      iframe.addEventListener('error', markFailed, { once: true });
    };

    const startGiscus = () => {
      if (state === 'loading' || state === 'ready') return;
      clearWatchers();
      removeWidget();
      attempt += 1;
      state = 'loading';
      loadStartedAt = performance.now();
      root.setAttribute('aria-busy', 'true');
      if (fallback) fallback.hidden = true;
      setStatus('正在加载讨论…');

      messageHandler = (event) => {
        if (event.origin !== 'https://giscus.app' || !event.data?.giscus) return;
        markReady();
      };
      window.addEventListener('message', messageHandler, false);

      iframeObserver = new MutationObserver(() => {
        root.querySelectorAll('iframe.giscus-frame').forEach(watchIframe);
      });
      iframeObserver.observe(root, { childList: true, subtree: true });

      const script = document.createElement('script');
      script.src = 'https://giscus.app/client.js';
      script.dataset.giscusLoader = 'true';
      script.setAttribute('data-repo', root.dataset.repo);
      script.setAttribute('data-repo-id', root.dataset.repoId);
      script.setAttribute('data-category', root.dataset.category);
      script.setAttribute('data-category-id', root.dataset.categoryId);
      script.setAttribute('data-lang', root.dataset.lang);
      script.setAttribute('data-mapping', root.dataset.mapping);
      script.setAttribute('data-reactions-enabled', root.dataset.reactionsEnabled);
      script.setAttribute('data-emit-metadata', root.dataset.emitMetadata);
      script.setAttribute('data-input-position', root.dataset.inputPosition);
      script.setAttribute('data-loading', root.dataset.loading);
      script.setAttribute('data-theme', document.body.getAttribute('theme') === 'dark'
        ? root.dataset.darkTheme
        : root.dataset.lightTheme);
      script.crossOrigin = 'anonymous';
      script.async = true;
      script.addEventListener('error', markFailed, { once: true });
      root.appendChild(script);

      timeoutID = window.setTimeout(markFailed, 12000);
    };

    const focusDiscussionHeading = () => {
      window.requestAnimationFrame(() => heading.focus({ preventScroll: true }));
    };

    // 悬浮评论按钮由 baseof 静态渲染为 #discussion-title，但主题 theme.js 会在
    // DOMContentLoaded 时把它的 href 改写为 #comments；两个片段都指向评论区，
    // 这里按两种取值同时匹配，避免与主题脚本做时序竞态。
    document.addEventListener('click', (event) => {
      const link = event.target.closest('a[href="#discussion-title"], a[href="#comments"]');
      if (!link) return;
      if (!link.dataset.event) {
        track('article_discussion_click', {
          target_kind: link.id === 'view-comments' ? 'fixed' : 'anchor',
          target_url: '#discussion-title',
        });
      }
      startGiscus();
      focusDiscussionHeading();
    }, false);

    retryButton?.addEventListener('click', startGiscus, false);

    const themeObserver = new MutationObserver(() => {
      const iframe = root.querySelector('iframe.giscus-frame');
      if (!iframe?.contentWindow) return;
      iframe.contentWindow.postMessage({
        giscus: {
          setConfig: {
            theme: document.body.getAttribute('theme') === 'dark'
              ? root.dataset.darkTheme
              : root.dataset.lightTheme,
          },
        },
      }, 'https://giscus.app');
    });
    themeObserver.observe(document.body, { attributes: true, attributeFilter: ['theme'] });

    if ('IntersectionObserver' in window) {
      const loadObserver = new IntersectionObserver((entries) => {
        if (!entries.some((entry) => entry.isIntersecting)) return;
        loadObserver.disconnect();
        startGiscus();
      }, { rootMargin: '800px 0px' });
      loadObserver.observe(section);
    } else {
      startGiscus();
    }

    if (window.location.hash === '#discussion-title' || window.location.hash === '#comments') {
      startGiscus();
      focusDiscussionHeading();
    }
  };

  initAnalytics();
  initShare();
  initDiscussion();
})();
