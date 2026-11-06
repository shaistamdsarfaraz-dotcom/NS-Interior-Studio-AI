function handleLogin(){
  const email=document.getElementById('login-email').value.trim();
  const pass=document.getElementById('login-pass').value.trim();
  if(!email||!pass){toast('Please fill in both fields.');return false}
  fetch('/login',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},
    body:new URLSearchParams({email:email,password:pass})})
  .then(r=>r.json())
  .then(d=>{
    if(d.success){toast('Login successful!',true);setTimeout(()=>location.href='/studio',700)}
    else toast(d.message)
  })
  .catch(e=>{console.error(e);toast('Something went wrong. Please try again.')});
  return false;
}
function openResetModal(){document.getElementById('reset-modal').style.display='flex'}
function closeResetModal(){document.getElementById('reset-modal').style.display='none'}
function handleResetPassword(){
  const email=document.getElementById('reset-email').value.trim();
  const newPass=document.getElementById('reset-pass').value.trim();
  if(!email||!newPass){toast('Please fill in all fields.');return false}
  fetch('/reset-password',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},
    body:new URLSearchParams({email:email,new_password:newPass})})
  .then(r=>r.json())
  .then(d=>{toast(d.message,d.success);if(d.success)closeResetModal()})
  .catch(e=>{console.error(e);toast('Could not reset password. Please try again.')});
  return false;
}