/**
 * DMS 扫码功能模块
 * 依赖: jsQR (vendor/jsqr.min.js)
 *
 * 功能：
 * 1. 调用摄像头扫描二维码/条形码
 * 2. 扫描结果自动填充到目标输入框
 * 3. 支持手动输入模式降级
 */

(function(window) {
  'use strict';

  var QRScanner = {
    _modal: null,
    _video: null,
    _canvas: null,
    _ctx: null,
    _scanning: false,
    _animFrameId: null,
    _targetInput: null,
    _onSuccess: null,
    _stream: null,

    /** 初始化（仅调用一次） */
    init: function() {
      if (this._modal) return;

      var html = '<div class="qr-scanner-modal" id="dmsQRModal">'
        + '<div class="qr-scanner-header">'
        + '<span class="qr-scanner-title">扫码识别</span>'
        + '<button class="qr-scanner-close" id="dmsQRClose"><i data-lucide="x"></i></button>'
        + '</div>'
        + '<div class="qr-scanner-container">'
        + '<video class="qr-scanner-video" id="dmsQRVideo" autoplay playsinline muted></video>'
        + '<canvas class="qr-scanner-canvas" id="dmsQRCanvas"></canvas>'
        + '<div class="qr-scanner-overlay"><div class="qr-scanner-frame"><span></span><div class="qr-scanner-line"></div></div></div>'
        + '</div>'
        + '<div class="qr-scanner-tip">将<b>二维码或条形码</b>对准框内<br>系统将自动识别</div>'
        + '<div class="qr-scanner-result" id="dmsQRResult"></div>'
        + '<button class="qr-scanner-manual-btn" id="dmsQRManualBtn">手动输入编码</button>'
        + '</div>';

      document.body.insertAdjacentHTML('beforeend', html);

      this._modal   = document.getElementById('dmsQRModal');
      this._video   = document.getElementById('dmsQRVideo');
      this._canvas  = document.getElementById('dmsQRCanvas');
      this._ctx     = this._canvas.getContext('2d');
      this._result  = document.getElementById('dmsQRResult');

      var self = this;

      document.getElementById('dmsQRClose').addEventListener('click', function() {
        self.close();
      });

      document.getElementById('dmsQRManualBtn').addEventListener('click', function() {
        var code = prompt('请手动输入设备编码：');
        if (code && code.trim()) {
          self._applyResult(code.trim());
        }
      });

      // 点击 modal 背景关闭
      this._modal.addEventListener('click', function(e) {
        if (e.target === self._modal) self.close();
      });

      // 初始化 Lucide 图标
      if (typeof lucide !== 'undefined') lucide.createIcons();
    },

    /** 打开扫码器 */
    open: function(targetInputEl, onSuccess) {
      this.init();
      this._targetInput = targetInputEl || null;
      this._onSuccess   = onSuccess || null;
      this._result.classList.remove('show');
      this._result.textContent = '';

      var self = this;

      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        alert('您的浏览器不支持摄像头访问，请使用 Chrome/Safari 等现代浏览器。');
        return;
      }

      var constraints = {
        video: {
          facingMode: { ideal: 'environment' },  // 优先后置摄像头
          width: { ideal: 640 },
          height: { ideal: 640 }
        }
      };

      navigator.mediaDevices.getUserMedia(constraints)
        .then(function(stream) {
          self._stream = stream;
          self._video.srcObject = stream;
          self._modal.classList.add('open');
          document.body.style.overflow = 'hidden';
          self._video.addEventListener('loadedmetadata', function() {
            self._video.play();
            self._startScan();
          });
        })
        .catch(function(err) {
          console.error('摄像头访问失败:', err);
          var msg = '无法访问摄像头';
          if (err.name === 'NotAllowedError') {
            msg = '摄像头权限被拒绝，请在浏览器设置中允许访问摄像头';
          } else if (err.name === 'NotFoundError') {
            msg = '未检测到摄像头设备';
          } else if (err.name === 'NotSupportedError') {
            msg = '当前环境不支持摄像头（需要 HTTPS）';
          }
          alert(msg + '\n\n您可以点击"手动输入编码"按钮手动填写。');
          self._modal.classList.add('open');
          document.body.style.overflow = 'hidden';
        });
    },

    /** 开始逐帧扫描 */
    _startScan: function() {
      this._scanning = true;
      var self = this;

      function tick() {
        if (!self._scanning) return;

        if (self._video.readyState === self._video.HAVE_ENOUGH_DATA) {
          var w = self._video.videoWidth;
          var h = self._video.videoHeight;

          self._canvas.width  = w;
          self._canvas.height = h;
          self._ctx.drawImage(self._video, 0, 0, w, h);

          var imageData = self._ctx.getImageData(0, 0, w, h);

          try {
            var code = jsQR(imageData.data, imageData.width, imageData.height, {
              inversionAttempts: 'dontInvert'
            });

            if (code && code.data) {
              self._applyResult(code.data);
              return; // 扫到结果后停止
            }
          } catch(e) {
            // jsQR 解析出错，继续扫
          }
        }

        self._animFrameId = requestAnimationFrame(tick);
      }

      this._animFrameId = requestAnimationFrame(tick);
    },

    /** 应用扫描结果 */
    _applyResult: function(value) {
      // 停止扫描，短暂显示结果
      this._scanning = false;
      if (this._animFrameId) cancelAnimationFrame(this._animFrameId);

      // 显示结果提示
      this._result.textContent = '✓ 识别成功：' + value;
      this._result.classList.add('show');

      // 填充目标输入框
      if (this._targetInput) {
        this._targetInput.value = value;
        this._targetInput.dispatchEvent(new Event('input', { bubbles: true }));
        this._targetInput.dispatchEvent(new Event('change', { bubbles: true }));
        // 聚焦到下一个字段
        var form = this._targetInput.form;
        if (form) {
          var inputs = Array.from(form.querySelectorAll('input, select, textarea'));
          var idx = inputs.indexOf(this._targetInput);
          if (idx >= 0 && idx < inputs.length - 1) {
            inputs[idx + 1].focus();
          }
        }
      }

      // 回调
      if (typeof this._onSuccess === 'function') {
        this._onSuccess(value);
      }

      // 500ms 后自动关闭
      var self = this;
      setTimeout(function() {
        self.close();
      }, 600);
    },

    /** 关闭扫码器 */
    close: function() {
      this._scanning = false;
      if (this._animFrameId) cancelAnimationFrame(this._animFrameId);

      // 停止视频流
      if (this._stream) {
        this._stream.getTracks().forEach(function(track) { track.stop(); });
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
