(function(){
  document.documentElement.classList.remove('no-js');
  var hdr=document.querySelector('.site-header');
  var onScroll=function(){hdr&&hdr.classList.toggle('scrolled',window.scrollY>10)};
  window.addEventListener('scroll',onScroll,{passive:true});onScroll();

  var tg=document.querySelector('.nav-toggle'),nav=document.querySelector('.nav');
  if(tg&&nav){tg.addEventListener('click',function(){var o=nav.classList.toggle('open');tg.setAttribute('aria-expanded',o)});}

  // flash dapat ditutup & hilang otomatis
  document.querySelectorAll('.flash').forEach(function(f){
    var b=f.querySelector('button');b&&b.addEventListener('click',function(){f.remove()});
    setTimeout(function(){f.style.transition='.4s';f.style.opacity='0';setTimeout(function(){f.remove()},400)},7000);
  });

  // animasi muncul saat scroll
  var els=document.querySelectorAll('.reveal');
  if('IntersectionObserver' in window){
    var io=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){e.target.classList.add('in');io.unobserve(e.target)}})},{threshold:.12});
    els.forEach(function(el,i){el.style.transitionDelay=(i%3)*80+'ms';io.observe(el)});
  }else{els.forEach(function(el){el.classList.add('in')})}

  // modal preview sertifikat
  var modal=document.getElementById('cert-modal');
  if(modal){
    var q=function(s){return modal.querySelector(s)};
    var open=function(d){
      var img=q('.modal-img img'),ph=q('.modal-img .ph');
      if(d.img){img.src=d.img;img.alt=d.nama;img.style.display='';ph.style.display='none'}
      else{img.style.display='none';ph.style.display='grid'}
      q('[data-f=nama]').textContent=d.nama;q('[data-f=org]').textContent=d.org;
      q('[data-f=tgl]').textContent=d.tgl;q('[data-f=desc]').textContent=d.desc;
      modal.classList.add('open');document.body.style.overflow='hidden';q('.modal-close').focus();
    };
    var close=function(){modal.classList.remove('open');document.body.style.overflow=''};
    document.querySelectorAll('[data-cert]').forEach(function(c){
      c.addEventListener('click',function(){open(c.dataset)});
    });
    modal.addEventListener('click',function(e){if(e.target===modal||e.target.closest('.modal-close'))close()});
    document.addEventListener('keydown',function(e){if(e.key==='Escape')close()});
  }

  // lightbox galeri pengalaman
  var lb=document.getElementById('lightbox');
  if(lb){
    var li=document.getElementById('lightbox-img');
    document.querySelectorAll('[data-lightbox]').forEach(function(b){
      b.addEventListener('click',function(){li.src=b.dataset.lightbox;lb.classList.add('open');document.body.style.overflow='hidden'});
    });
    var cl=function(){lb.classList.remove('open');document.body.style.overflow=''};
    lb.addEventListener('click',function(e){if(e.target!==li)cl()});
    document.addEventListener('keydown',function(e){if(e.key==='Escape')cl()});
  }

  // konfirmasi hapus
  document.querySelectorAll('form[data-confirm]').forEach(function(f){
    f.addEventListener('submit',function(e){if(!confirm(f.dataset.confirm))e.preventDefault()});
  });

  // pratinjau gambar upload (admin)
  document.querySelectorAll('input[type=file][data-preview]').forEach(function(inp){
    inp.addEventListener('change',function(){
      var t=document.getElementById(inp.dataset.preview);if(!t||!inp.files[0])return;
      var f=inp.files[0];
      if(f.size>2*1024*1024){alert('Ukuran gambar maksimal 2 MB.');inp.value='';return}
      t.src=URL.createObjectURL(f);t.style.display='block';
    });
  });
})();
