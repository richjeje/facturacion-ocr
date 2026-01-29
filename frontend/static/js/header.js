// Simple header behavior: hide on scroll down, show on scroll up
(function(){
  var header = document.getElementById('site-header');
  if (!header) return;
  var lastY = window.scrollY;
  var ticking = false;
  window.addEventListener('scroll', function(){
    var y = window.scrollY;
    if (!ticking) {
      window.requestAnimationFrame(function(){
        if (y > lastY && y > 80) {
          header.style.transform = 'translateY(-100%)';
        } else {
          header.style.transform = 'translateY(0)';
        }
        lastY = y;
        ticking = false;
      });
      ticking = true;
    }
  });

  // Basic notification menu placeholder (toggle on click)
  var btn = document.getElementById('notif-btn');
  var menu = document.getElementById('notif-menu');
  if (btn && !menu) {
    btn.addEventListener('click', function(){
      // create simple dropdown if not exists
      var m = document.getElementById('notif-menu');
      if (!m) {
        m = document.createElement('div');
        m.id = 'notif-menu';
        m.style.position = 'absolute';
        m.style.top = '64px';
        m.style.right = '16px';
        m.style.width = '260px';
        m.style.background = '#fff';
        m.style.border = '1px solid var(--border-dim)';
        m.style.boxShadow = '0 4px 12px rgba(0,0,0,.1)';
        m.style.borderRadius = '6px';
        m.style.padding = '8px';
        m.innerHTML = '<div class="text-muted" style="font-size:12px; padding:4px 6px;">Sin notificaciones</div>';
        document.body.appendChild(m);
      }
      var shown = m.style.display === 'block';
      m.style.display = shown ? 'none' : 'block';
    });
  }

  // Mobile menu toggle (drawer)
  var mobileBtn = document.getElementById('mobile-menu-btn');
  var mobileMenu = document.getElementById('mobile-menu');
  if (mobileBtn && mobileMenu) {
    // Build simple menu content if empty
    mobileBtn.addEventListener('click', function(){
      const visible = mobileMenu.style.transform === 'translateX(0%)' || mobileMenu.style.display === 'block';
      if (visible) {
        mobileMenu.style.transform = 'translateX(-110%)';
        mobileMenu.style.display = 'none';
      } else {
        // populate once
        if (!mobileMenu.dataset.populated) {
          mobileMenu.innerHTML = `
            <div style="padding: 12px; border-bottom:1px solid var(--border-dim); font-weight:600;">Negocio</div>
            <a class="nav-link" href="/negocio/emitir-factura" style="display:block; padding:8px 12px;">Emitir Factura (Negocio)</a>
            <a class="nav-link" href="/negocio/facturar-gastos" style="display:block; padding:8px 12px;">Facturar Gastos</a>
            <a class="nav-link" href="/negocio/mis-facturas" style="display:block; padding:8px 12px;">Mis Facturas (Negocio)</a>
            <a class="nav-link" href="/negocio/mis-clientes" style="display:block; padding:8px 12px;">Mis Clientes</a>
            <div style="height:8px;"></div>
            <div style="padding: 12px; font-weight:600; border-bottom:1px solid var(--border-dim);">Clientes</div>
            <a class="nav-link" href="/clientes/mis-facturas" style="display:block; padding:8px 12px;">Mis Facturas (Clientes)</a>
            <div style="height:8px;"></div>
            <a class="nav-link" href="/logout" style="display:block; padding:8px 12px;">Cerrar Sesión</a>
          `;
          mobileMenu.dataset.populated = '1';
        }
        mobileMenu.style.display = 'block';
        mobileMenu.style.transform = 'translateX(0%)';
      }
    });
  }
})();
