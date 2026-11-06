function handleRegister(){
  const name=document.getElementById('reg-name').value.trim();
  const email=document.getElementById('reg-email').value.trim();
  const pass=document.getElementById('reg-pass').value.trim();
  if(!name||!email||!pass){toast('Please fill in all fields.');return false}
  fetch('/register',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},
    body:new URLSearchParams({username:name,email:email,password:pass})})
  .then(r=>r.json())
  .then(d=>{
    if(d.success){toast('Registration successful! Please login.',true);setTimeout(()=>location.href='/login',900)}
    else toast(d.message)
  })
  .catch(e=>{console.error(e);toast('Something went wrong. Please try again.')});
  return false;
}