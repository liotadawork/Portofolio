(function(){
  var sb=document.querySelector('.sidebar'),bg=document.querySelector('.burger');
  if(bg&&sb){bg.addEventListener('click',function(){sb.classList.toggle('open')});
    document.addEventListener('click',function(e){if(sb.classList.contains('open')&&!sb.contains(e.target)&&!bg.contains(e.target))sb.classList.remove('open')});}
  document.querySelectorAll('.flash button').forEach(function(b){b.addEventListener('click',function(){b.parentElement.remove()})});
  document.querySelectorAll('form[data-confirm]').forEach(function(f){
    f.addEventListener('submit',function(e){if(!confirm(f.dataset.confirm))e.preventDefault()});
  });
  document.querySelectorAll('input[type=file][data-preview]').forEach(function(inp){
    inp.addEventListener('change',function(){
      var t=document.getElementById(inp.dataset.preview);if(!t||!inp.files[0])return;
      var f=inp.files[0];
      if(f.size>2*1024*1024){alert('Ukuran gambar maksimal 2 MB.');inp.value='';return}
      t.src=URL.createObjectURL(f);t.style.display='block';
    });
  });
})();
