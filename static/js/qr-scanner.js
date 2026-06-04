/**
 * DMS 扫码功能模块 v2
 * 依赖: jsQR (vendor/jsqr.min.js)
 *
 * 降级策略（自动选择）：
 *   HTTPS + getUserMedia 可用  → 实时摄像头扫描（最佳体验）
 *   HTTP / 权限被拒绝         → 拍照/相册选图解码（HTTP 也能用）
 *   两者都失败                → 手动输入
 */

(function(window) {
  'use strict';

  // ======================================================
  // 工具函数
  // ======================================================

  /** 从 ImageData 中解码二维码/条形码，返回字符串或 null */
  function decodeImageData(imageData) {
    if (typeof jsQR === 'undefined') return null;
    try {
      var result = jsQR(imageData.data, imageData.width, imageData.height, {
        inversionAttempts: 'attemptBoth'
      });
      return result && result.data ? result.data : null;
    } catch (e) {
      return null;
    }
  }

  /** 从 HTMLImageElement 解码，自动缩放到合理尺寸，返回 Promise<string|null> */
  function decodeImage(imgEl) {
    return new Promise(function(resolve) {
      var MAX_SIDE = 1600;
      var w = imgEl.naturalWidth  || imgEl.width  || 800;
      var h = imgEl.naturalHeight || imgEl.height || 800;

      // 等比缩放
      var scale = 1;
      if (w > MAX_SIDE || h > MAX_SIDE) {
        scale = MAX_SIDE / Math.max(w, h);
      }
      var dw = Math.round(w * scale);
      var dh = Math.round(h * scale);

      var canvas = document.createElement('canvas');
      canvas.width  = dw;
      canvas.height = dh;
      var ctx = canvas.getContext('2d');
      ctx.drawImage(imgEl, 0, 0, dw, dh);

      // 尝试全图解码
      var imageData = ctx.getImageData(0, 0, dw, dh);
      var result = decodeImageData(imageData);

      if (result) { resolve(result); return; }

      // 如果全图没识别到，尝试将图片增强对比度后再扫一次
      // （某些低对比度图片 jsQR 不容易识别）
      try {
        var d = imageData.data;
        for (var i = 0; i < d.length; i += 4) {
          // 转灰度 → 二值化（阈值 128）
          var gray = 0.299 * d[i] + 0.587 * d[i+1] + 0.114 * d[i+2];
          var bin  = gray > 128 ? 255 : 0;
          d[i] = d[i+1] = d[i+2] = bin;
        }
        ctx.putImageData(imageData, 0, 0);
        var imageData2 = ctx.getImageData(0, 0, dw, dh);
        result = decodeImageData(imageData2);
      } catch(e) { /* ignore */ }

      resolve(result);
    });
  }

  /** 检测是否支持摄像头（HTTPS 环境或 localhost） */
  function isCameraSupported() {
    return !!(
      navigator.mediaDevices &&
      navigator.mediaDevices.getUserMedia &&
      (location.protocol === 'https:' || location.hostname === 'localhost' || location.hostname === '127.0.0.1')
    );
  }

  // ======================================================
  // 扫码器主体
  // ======================================================

  var QRScanner = {
    _modal:       null,
    _video:       null,
    _canvas:      null,
    _ctx:         null,
    _scanning:    false,
    _animFrameId: null,
    _targetInput: null,
    _onSuccess:   null,
    _stream:      null,
    _resultEl:    null,
    _fileInput:   null,

    // --------------------------------------------------
    // 初始化 DOM（仅执行一次）
    // --------------------------------------------------
    init: function() {
      if (this._modal) return;

      var html = [
        '<div class="qr-scanner-modal" id="dmsQRModal">',
          '<div class="qr-scanner-inner">',
            /* 标题栏 */
            '<div class="qr-scanner-header">',
              '<span class="qr-scanner-title">扫描二维码 / 条形码</span>',
              '<button class="qr-scanner-close" id="dmsQRClose" type="button" aria-label="关闭">',
                '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>',
              '</button>',
            '</div>',

            /* 摄像头区域（仅 HTTPS 显示） */
            '<div class="qr-scanner-camera-area" id="dmsQRCameraArea" style="display:none;">',
              '<video class="qr-scanner-video" id="dmsQRVideo" autoplay playsinline muted></video>',
              '<canvas class="qr-scanner-canvas" id="dmsQRCanvas"></canvas>',
              '<div class="qr-scanner-overlay">',
                '<div class="qr-scanner-frame"><div class="qr-scanner-line"></div></div>',
              '</div>',
              '<div class="qr-scanner-tip">将二维码或条形码对准扫描框</div>',
            '</div>',

            /* 拍照上传区域（HTTP 降级 / 始终显示 "从相册选取" 选项） */
            '<div class="qr-scanner-upload-area" id="dmsQRUploadArea">',
              '<div class="qr-upload-icon">',
                '<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3z"/><circle cx="12" cy="13" r="3"/></svg>',
              '</div>',
              '<p class="qr-upload-hint" id="dmsQRUploadHint">拍照或从相册选取二维码图片</p>',
              '<p class="qr-upload-sub" id="dmsQRUploadSub">自动解析图片中的二维码/条形码</p>',
              /* 隐藏的文件输入，accept 设置 image/* 让手机弹出拍照+相册选择菜单；不加 capture 属性让用户可以选相册 */
              '<input type="file" id="dmsQRFileInput" accept="image/*" style="display:none;">',
              '<button class="qr-upload-btn" id="dmsQRUploadBtn" type="button">',
                '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3z"/><circle cx="12" cy="13" r="3"/></svg>',
                '拍照 / 选择图片',
              '</button>',
            '</div>',

            /* 解码结果 */
            '<div class="qr-scanner-result" id="dmsQRResult"></div>',

            /* 底部操作 */
            '<div class="qr-scanner-actions">',
              '<button class="qr-btn-secondary" id="dmsQRManualBtn" type="button">手动输入编码</button>',
            '</div>',
          '</div>',
        '</div>'
      ].join('');

      document.body.insertAdjacentHTML('beforeend', html);

      this._modal     = document.getElementById('dmsQRModal');
      this._video     = document.getElementById('dmsQRVideo');
      this._canvas    = document.getElementById('dmsQRCanvas');
      this._ctx       = this._canvas.getContext('2d');
      this._resultEl  = document.getElementById('dmsQRResult');
      this._fileInput = document.getElementById('dmsQRFileInput');

      var self = this;

      // 关闭按钮
      document.getElementById('dmsQRClose').addEventListener('click', function() {
        self.close();
      });
      // 遮罩关闭
      this._modal.addEventListener('click', function(e) {
        if (e.target === self._modal) self.close();
      });

      // 手动输入
      document.getElementById('dmsQRManualBtn').addEventListener('click', function() {
        var code = prompt('请手动输入设备编码：');
        if (code && code.trim()) self._applyResult(code.trim());
      });

      // 拍照/选图按钮
      document.getElementById('dmsQRUploadBtn').addEventListener('click', function() {
        self._fileInput.click();
      });

      // 文件选择后解码
      this._fileInput.addEventListener('change', function(e) {
        var file = e.target.files && e.target.files[0];
        if (!file) return;

        self._showStatus('正在解析图片...', 'loading');

        // 将文件转成 createObjectURL，让 img.onload 拿到原始尺寸
        var objectURL = URL.createObjectURL(file);
        var img = new Image();
        img.onload = function() {
          decodeImage(img).then(function(value) {
            URL.revokeObjectURL(objectURL);
            if (value) {
              self._applyResult(value);
            } else {
              self._showStatus('未检测到二维码，请换一张更清晰的图片或手动输入', 'error');
            }
          });
        };
        img.onerror = function() {
          URL.revokeObjectURL(objectURL);
          self._showStatus('图片加载失败，请重试', 'error');
        };
        img.src = objectURL;

        // 清空，允许重复选同一张图
        self._fileInput.value = '';
      });
    },

    // --------------------------------------------------
    // 打开扫码器
    // --------------------------------------------------
    open: function(targetInputEl, onSuccess) {
      this.init();
      this._targetInput = targetInputEl || null;
      this._onSuccess   = onSuccess || null;
      this._resultEl.className = 'qr-scanner-result';
      this._resultEl.textContent = '';

      var self = this;

      // 先显示弹窗
      this._modal.classList.add('open');
      document.body.style.overflow = 'hidden';

      if (isCameraSupported()) {
        // HTTPS：优先尝试实时摄像头
        document.getElementById('dmsQRCameraArea').style.display = '';
        document.getElementById('dmsQRUploadArea').style.display = '';
        document.getElementById('dmsQRUploadHint').textContent   = '或从相册选取图片';
        document.getElementById('dmsQRUploadSub').style.display  = 'none';

        var constraints = {
          video: {
            facingMode: { ideal: 'environment' },
            width:  { ideal: 1280 },
            height: { ideal: 720 }
          }
        };

        navigator.mediaDevices.getUserMedia(constraints)
          .then(function(stream) {
            self._stream = stream;
            self._video.srcObject = stream;
            self._video.addEventListener('loadedmetadata', function onMeta() {
              self._video.removeEventListener('loadedmetadata', onMeta);
              self._video.play();
              self._startScan();
            });
          })
          .catch(function(err) {
            console.warn('[DMSScanner] 摄像头获取失败，降级到拍照模式:', err.name);
            document.getElementById('dmsQRCameraArea').style.display = 'none';
            self._showStatus('摄像头不可用，请点击"拍照/选择图片"按钮扫码', 'warn');
          });
      } else {
        // HTTP：直接显示上传区域
        document.getElementById('dmsQRCameraArea').style.display = 'none';
        document.getElementById('dmsQRUploadArea').style.display = '';
        document.getElementById('dmsQRUploadHint').textContent   = '拍照或从相册选取二维码图片';
        document.getElementById('dmsQRUploadSub').style.display  = '';
      }
    },

    // --------------------------------------------------
    // 实时摄像头扫描（HTTPS 模式）
    // --------------------------------------------------
    _startScan: function() {
      this._scanning = true;
      var self = this;

      function tick() {
        if (!self._scanning) return;

        if (self._video.readyState === self._video.HAVE_ENOUGH_DATA) {
          var w = self._video.videoWidth;
          var h = self._video.videoHeight;

          if (w > 0 && h > 0) {
            self._canvas.width  = w;
            self._canvas.height = h;
            self._ctx.drawImage(self._video, 0, 0, w, h);

            var imageData = self._ctx.getImageData(0, 0, w, h);
            var value = decodeImageData(imageData);

            if (value) {
              self._applyResult(value);
              return;
            }
          }
        }

        self._animFrameId = requestAnimationFrame(tick);
      }

      this._animFrameId = requestAnimationFrame(tick);
    },

    // --------------------------------------------------
    // 应用识别结果
    // --------------------------------------------------
    _applyResult: function(value) {
      this._scanning = false;
      if (this._animFrameId) cancelAnimationFrame(this._animFrameId);

      this._showStatus('✓ 识别成功：' + value, 'success');

      if (this._targetInput) {
        this._targetInput.value = value;
        this._targetInput.dispatchEvent(new Event('input',  { bubbles: true }));
        this._targetInput.dispatchEvent(new Event('change', { bubbles: true }));

        // 自动聚焦到下一个表单字段
        var form = this._targetInput.form;
        if (form) {
          var inputs = Array.from(form.querySelectorAll('input:not([type=hidden]), select, textarea'));
          var idx = inputs.indexOf(this._targetInput);
          if (idx >= 0 && idx < inputs.length - 1) {
            setTimeout(function() { inputs[idx + 1].focus(); }, 100);
          }
        }
      }

      if (typeof this._onSuccess === 'function') {
        this._onSuccess(value);
      }

      // 600ms 后自动关闭
      var self = this;
      setTimeout(function() { self.close(); }, 700);
    },

    // --------------------------------------------------
    // 显示状态信息
    // --------------------------------------------------
    _showStatus: function(msg, type) {
      if (!this._resultEl) return;
      this._resultEl.textContent = msg;
      this._resultEl.className = 'qr-scanner-result show qr-result-' + (type || 'info');
    },

    // --------------------------------------------------
    // 关闭扫码器
    // --------------------------------------------------
    close: function() {
      this._scanning = false;
      if (this._animFrameId) cancelAnimationFrame(this._animFrameId);

      if (this._stream) {
        this._stream.getTracks().forEach(function(t) { t.stop(); });
        this._stream = null;
      }

      if (this._video) {
        this._video.srcObject = null;
      }

      if (this._modal) {
        this._modal.classList.remove('open');
      }

      document.body.style.overflow = '';
    }
  };

  // 暴露到全局
  window.DMSScanner = QRScanner;

})(window);
