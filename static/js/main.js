/**
 * DMS 设备管理系统 - 主脚本
 */

(function() {
  'use strict';

  // ==================== 侧边栏 ====================
  const sidebar = document.getElementById('sidebar');
  const mainWrapper = document.getElementById('mainWrapper');
  const sidebarToggle = document.getElementById('sidebarToggle');
  const menuToggle = document.getElementById('menuToggle');

  // 切换侧边栏展开/收起
  function toggleSidebar(forceState) {
    const isCollapsed = forceState !== undefined ? forceState : sidebar.classList.contains('collapsed');

    if (isCollapsed) {
      sidebar.classList.remove('collapsed');
      mainWrapper.classList.remove('expanded');
      localStorage.setItem('sidebar-collapsed', 'false');
    } else {
      sidebar.classList.add('collapsed');
      mainWrapper.classList.add('expanded');
      localStorage.setItem('sidebar-collapsed', 'true');
    }
  }

  // 移动端切换
  function toggleMobileSidebar() {
    sidebar.classList.toggle('mobile-open');
  }

  // 初始化侧边栏状态
  function initSidebar() {
    const savedState = localStorage.getItem('sidebar-collapsed');

    if (savedState === 'true') {
      sidebar.classList.add('collapsed');
      mainWrapper.classList.add('expanded');
    }

    // 监听窗口大小变化
    window.addEventListener('resize', function() {
      if (window.innerWidth <= 768) {
        sidebar.classList.remove('collapsed');
        mainWrapper.classList.remove('expanded');
      } else if (savedState === 'true') {
        sidebar.classList.add('collapsed');
        mainWrapper.classList.add('expanded');
      }
    });
  }

  // 绑定事件
  if (sidebarToggle) {
    sidebarToggle.addEventListener('click', function() {
      if (window.innerWidth <= 768) {
        toggleMobileSidebar();
      } else {
        toggleSidebar();
      }
    });
  }

  if (menuToggle) {
    menuToggle.addEventListener('click', toggleMobileSidebar);
  }

  // 点击遮罩层关闭移动端侧边栏
  document.addEventListener('click', function(e) {
    if (window.innerWidth <= 768 &&
        sidebar.classList.contains('mobile-open') &&
        !sidebar.contains(e.target) &&
        !menuToggle.contains(e.target)) {
      sidebar.classList.remove('mobile-open');
    }
  });

  initSidebar();

  // ==================== 用户下拉菜单 ====================
  const userDropdown = document.getElementById('userDropdown');

  if (userDropdown) {
    const userBtn = userDropdown.querySelector('.user-btn');

    userBtn.addEventListener('click', function(e) {
      e.stopPropagation();
      userDropdown.classList.toggle('open');
    });

    document.addEventListener('click', function(e) {
      if (!userDropdown.contains(e.target)) {
        userDropdown.classList.remove('open');
      }
    });
  }

  // ==================== 全局搜索 ====================
  const globalSearch = document.querySelector('.global-search');
  const searchInput = globalSearch ? globalSearch.querySelector('.search-input') : null;

  // 键盘快捷键 ⌘K / Ctrl+K
  document.addEventListener('keydown', function(e) {
    if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
      e.preventDefault();
      if (searchInput) {
        searchInput.focus();
        globalSearch.classList.add('focused');
      }
    }

    if (e.key === 'Escape' && globalSearch) {
      globalSearch.classList.remove('focused');
      if (searchInput) {
        searchInput.blur();
      }
    }
  });

  // ==================== 自动关闭闪现消息 ====================
  const alerts = document.querySelectorAll('.alert');

  alerts.forEach(function(alert) {
    setTimeout(function() {
      const bsAlert = new bootstrap.Alert(alert);
      bsAlert.close();
    }, 5000);
  });

  // ==================== 确认删除 ====================
  document.querySelectorAll('[data-confirm]').forEach(function(el) {
    el.addEventListener('click', function(e) {
      const message = el.getAttribute('data-confirm') || '确定要执行此操作吗？';
      if (!confirm(message)) {
        e.preventDefault();
      }
    });
  });

  // ==================== 表单提交状态 ====================
  document.querySelectorAll('form[data-loading]').forEach(function(form) {
    form.addEventListener('submit', function() {
      const submitBtn = form.querySelector('[type="submit"]');
      if (submitBtn && !submitBtn.disabled) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="loading-spinner"></span> 处理中...';
      }
    });
  });

  // ==================== 工具提示初始化 ====================
  const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');

  if (typeof bootstrap !== 'undefined') {
    tooltipTriggerList.forEach(function(tooltipTriggerEl) {
      new bootstrap.Tooltip(tooltipTriggerEl);
    });
  }

  // ==================== Lucide 图标动画 ====================
  // 为导航项添加微交互
  document.querySelectorAll('.nav-item').forEach(function(item) {
    item.addEventListener('mouseenter', function() {
      const icon = item.querySelector('i, svg');
      if (icon && icon.tagName === 'I') {
        icon.style.transform = 'scale(1.1)';
      }
    });

    item.addEventListener('mouseleave', function() {
      const icon = item.querySelector('i, svg');
      if (icon && icon.tagName === 'I') {
        icon.style.transform = 'scale(1)';
      }
    });
  });

  // ==================== 统计卡片动画 ====================
  const statCards = document.querySelectorAll('.stat-card');

  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver(function(entries) {
      entries.forEach(function(entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('fade-in');
          observer.unobserve(entry.target);
        }
      });
    }, {
      threshold: 0.1
    });

    statCards.forEach(function(card) {
      observer.observe(card);
    });
  }

  // ==================== 导出公共方法 ====================
  window.DMS = {
    toggleSidebar: toggleSidebar,
    toggleMobileSidebar: toggleMobileSidebar
  };

})();

// ==================== 移动端底部导航交互 ====================
(function() {
  'use strict';

  // "更多"展开/收起
  var moreBtn = document.getElementById('mobileMoreBtn');
  var moreMenu = document.getElementById('mobileMoreMenu');
  var moreOverlay = document.getElementById('mobileMoreOverlay');

  function openMoreMenu() {
    if (moreMenu) moreMenu.classList.add('open');
    if (moreOverlay) moreOverlay.classList.add('open');
    document.body.style.overflow = 'hidden';
  }

  function closeMoreMenu() {
    if (moreMenu) moreMenu.classList.remove('open');
    if (moreOverlay) moreOverlay.classList.remove('open');
    document.body.style.overflow = '';
  }

  if (moreBtn) {
    moreBtn.addEventListener('click', function() {
      if (moreMenu && moreMenu.classList.contains('open')) {
        closeMoreMenu();
      } else {
        openMoreMenu();
      }
    });
  }

  if (moreOverlay) {
    moreOverlay.addEventListener('click', closeMoreMenu);
  }

  // 移动端搜索覆盖层
  var searchBtn = document.getElementById('mobileSearchBtn');
  var searchOverlay = document.getElementById('mobileSearchOverlay');
  var searchCancel = document.getElementById('mobileSearchCancel');
  var searchInput = document.getElementById('mobileSearchInput');
  var searchBg = document.getElementById('mobileSearchBg');

  function openMobileSearch() {
    if (searchOverlay) {
      searchOverlay.classList.add('open');
      document.body.style.overflow = 'hidden';
      setTimeout(function() {
        if (searchInput) searchInput.focus();
      }, 100);
    }
  }

  function closeMobileSearch() {
    if (searchOverlay) {
      searchOverlay.classList.remove('open');
      document.body.style.overflow = '';
    }
  }

  if (searchBtn) searchBtn.addEventListener('click', openMobileSearch);
  if (searchCancel) searchCancel.addEventListener('click', closeMobileSearch);
  if (searchBg) searchBg.addEventListener('click', closeMobileSearch);

  // 移动端铃铛角标同步
  var mobileBellBadge = document.getElementById('mobileBellBadge');
  if (mobileBellBadge) {
    var count = 0;
    fetch('/api/dashboard/due-maintenance?days=7')
      .then(function(r) { return r.json(); })
      .then(function(d) {
        count += (d.summary.overdue_count || 0) + (d.summary.due_today_count || 0);
        updateMobileBell();
      }).catch(function() {});
    fetch('/api/dashboard/calibration-overdue-count')
      .then(function(r) { return r.json(); })
      .then(function(d) {
        count += (d.overdue_count || 0);
        updateMobileBell();
      }).catch(function() {});

    function updateMobileBell() {
      if (count > 0) {
        mobileBellBadge.textContent = count > 99 ? '99+' : count;
        mobileBellBadge.style.display = '';
      } else {
        mobileBellBadge.style.display = 'none';
      }
    }
  }
})();
