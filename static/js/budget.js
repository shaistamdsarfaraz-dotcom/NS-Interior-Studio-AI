/* Budget Planner: your original logic, unchanged in behaviour.
   Only differences: Walnut colours, and room/style are read from the new tile selectors. */
const BP_COLORS = { purple:'#AD8964', pink:'#89947A', yellow:'#D1B06A', teal:'#6B5A4B', orange:'#B98B7D', blue:'#9A9086' };
 
function formatRupees(value){
    const amount = Number(value) || 0;
    return '₹' + Math.max(0, amount).toLocaleString('en-IN');
}
function numericText(value){ return Number(String(value ?? '').replace(/[₹,\s]/g,'')) || 0; }
function getChoice(name, fallback){ return document.querySelector(`input[name="${name}"]:checked`)?.value || fallback; }
function showToast(message){
    const toast=document.getElementById('bpToast'); if(!toast) return;
    toast.textContent=message; toast.classList.add('show');
    clearTimeout(window.bpToastTimer); window.bpToastTimer=setTimeout(()=>toast.classList.remove('show'),2600);
}
function createBudget(){
    const input=document.getElementById('totalBudgetInput');
    const total=Math.max(0,Number(input?.value)||0);
    const room=getChoice('room','Living Room');
    const style=getChoice('style','Modern');
 
    if(total<=0){
        showToast('Enter a budget before updating the plan.');
        input?.focus();
        return;
    }
 
   const plannedAmount = Math.round(total * 0.90);

buildGeneratedRows(plannedAmount, room, style);

document.getElementById('totalBudgetDisplay').textContent =
    formatRupees(total);

document.getElementById('totalAmount').textContent =
    formatRupees(plannedAmount);

    document.getElementById('generatedSummary').style.display='block';
    document.getElementById('generatedBreakdown').style.display='grid';
    document.getElementById('generatedDetails').style.display='grid';
    ['generatedSummary','generatedBreakdown','generatedDetails'].forEach(id=>document.getElementById(id).classList.add('in'));
    recalculate();
    showToast(`${style} ${room} budget plan is ready.`);
}
 
function buildGeneratedRows(total, room, style){
    const roomItems={
        'Living Room':['Sofa and seating','Wall finish','Layered lighting','Flooring','Curtains and cushions','Decor accents'],
        'Bedroom':['Bed and storage','Wall finish','Bedside lighting','Flooring','Curtains and bedding','Decor accents'],
        'Kitchen':['Cabinet and storage','Wall finish','Task lighting','Countertop and flooring','Hardware and fittings','Decor accents'],
        'Bathroom':['Vanity and storage','Wall and tile finish','Mirror lighting','Flooring and tiles','Fixtures and fittings','Decor accents']
    };
    const names=roomItems[room]||roomItems['Living Room'];
    const categories=['Furniture','Paint & Wall Finish','Lighting','Flooring','Decor','Other'];
    const shares=[0.38,0.15,0.10,0.17,0.07,0.13];
    const tbody=document.getElementById('expenseTableBody');
    tbody.innerHTML='';
    let allocated=0;
    names.forEach((name,index)=>{
        const amount=index===names.length-1?Math.max(0,total-allocated):Math.round(total*shares[index]);
        allocated+=amount;
        const cls=categoryClass(categories[index]);
        const row=document.createElement('tr');
        row.innerHTML=`<td>${index+1}</td><td contenteditable="true">${name} (${style})</td><td><span class="cat-tag ${cls}">${categories[index]}</span></td><td contenteditable="true" class="cost-cell">${amount.toLocaleString('en-IN')}</td><td contenteditable="true" class="qty-cell">1</td><td class="total-cell">${amount.toLocaleString('en-IN')}</td><td><button class="icon-action edit-icon" type="button" title="Edit"><i class="fa-solid fa-pen"></i></button><button class="icon-action delete-icon" type="button" title="Delete"><i class="fa-solid fa-trash"></i></button></td>`;
        tbody.appendChild(row);
        bindRow(row);
    });
}
function updateRowTotal(row){
    if(!row) return;
    const cost=numericText(row.querySelector('.cost-cell')?.textContent);
    const qty=Math.max(1,numericText(row.querySelector('.qty-cell')?.textContent)||1);
    const totalCell=row.querySelector('.total-cell');
    if(totalCell) totalCell.textContent=(cost*qty).toLocaleString('en-IN');
}
function getRows(){ return [...document.querySelectorAll('#expenseTableBody tr')]; }
function renumberRows(){
    getRows().forEach((row,index)=>{ if(row.children[0]) row.children[0].textContent=index+1; });
    const count=document.getElementById('itemCount'); if(count) count.textContent=`${getRows().length} ${getRows().length===1?'item':'items'}`;
}
function categoryData(){
    const result={};
    getRows().forEach(row=>{
        const category=row.querySelector('.cat-tag')?.textContent.trim()||'Other';
        result[category]=(result[category]||0)+numericText(row.querySelector('.total-cell')?.textContent);
    });
    return result;
}
function categoryClass(category){
    const value=category.toLowerCase();
    if(value.includes('furniture')) return 'purple';
    if(value.includes('paint')) return 'pink';
    if(value.includes('light')) return 'yellow';
    if(value.includes('floor')) return 'teal';
    if(value.includes('decor')) return 'orange';
    return 'blue';
}
function updateBreakdown(estimated){
    const data=categoryData(); const entries=Object.entries(data); const total=estimated||1;
    const colors=['purple','pink','yellow','teal','orange','blue'];
    const legend=document.getElementById('expenseBreakdownList');
    if(legend && entries.length){
        legend.innerHTML=entries.map(([name,value],index)=>{
            const percent=Math.round(value/total*100); const cls=categoryClass(name)||colors[index%colors.length];
            return `<li><span class="dot ${cls}"></span><span>${name}</span><b>${formatRupees(value)}</b><em>${percent}%</em></li>`;
        }).join('');
    }
    const donut=document.getElementById('donutChart');
    if(donut && entries.length){
        let start=0; const stops=entries.map(([name,value],index)=>{ const end=start+(value/total*100); const stop=`${BP_COLORS[categoryClass(name)]||BP_COLORS[colors[index%colors.length]]} ${start}% ${end}%`; start=end; return stop; });
        donut.style.background=`conic-gradient(${stops.join(',')})`;
    }
 
    const allocation=document.querySelector('#generatedBreakdown .bp-alloc-list');
    if(allocation && entries.length){
        allocation.innerHTML=entries.map(([name,value],index)=>{
            const percent=Math.round(value/total*100);
            const cls=categoryClass(name)||colors[index%colors.length];
            return `<li><span class="dot ${cls}"></span><span>${name}</span><em>${percent}%</em><div class="bp-alloc-bar"><div class="bp-alloc-fill ${cls}" style="width:${percent}%"></div></div><b>${formatRupees(value)}</b></li>`;
        }).join('');
    }
}
function recalculate(){
    const rows=getRows(); let estimated=0;
    rows.forEach(row=>{ updateRowTotal(row); estimated+=numericText(row.querySelector('.total-cell')?.textContent); });
    const totalBudget=numericText(document.getElementById('totalBudgetDisplay')?.textContent);
    const remaining=Math.max(0,totalBudget-estimated);
    const usedPercent=totalBudget>0?Math.min(100,Math.round(estimated/totalBudget*100)):0;
    document.getElementById('estimatedCostDisplay').textContent=formatRupees(estimated);
    document.getElementById('remainingDisplay').textContent=formatRupees(remaining);
    document.getElementById('usedAmount').textContent=formatRupees(estimated);
    document.getElementById('usedPercent').textContent=usedPercent+'%';
    document.getElementById('usedBar').style.width=usedPercent+'%';
    document.getElementById('donutTotal').textContent=formatRupees(estimated);
    renumberRows(); updateBreakdown(estimated);
    const remainingEl=document.getElementById('remainingDisplay'); if(remainingEl) remainingEl.style.color=estimated>totalBudget?'#f2a899':'#c3d1b3';
}
function bindRow(row){
    row.querySelectorAll('.cost-cell,.qty-cell').forEach(cell=>cell.addEventListener('input',()=>recalculate()));
    row.querySelector('.delete-icon')?.addEventListener('click',()=>{ row.remove(); recalculate(); showToast('Expense removed.'); });
    row.querySelector('.edit-icon')?.addEventListener('click',()=>{ const firstEditable=row.querySelector('[contenteditable="true"]'); firstEditable?.focus(); showToast('You can edit the item directly.'); });
}
function addExpenseRow(){
    const tbody=document.getElementById('expenseTableBody'); if(!tbody) return;
    const row=document.createElement('tr');
    row.innerHTML=`<td></td><td contenteditable="true">New Item</td><td><span class="cat-tag blue">Other</span></td><td contenteditable="true" class="cost-cell">0</td><td contenteditable="true" class="qty-cell">1</td><td class="total-cell">0</td><td><button class="icon-action edit-icon" type="button" title="Edit"><i class="fa-solid fa-pen"></i></button><button class="icon-action delete-icon" type="button" title="Delete"><i class="fa-solid fa-trash"></i></button></td>`;
    tbody.appendChild(row); bindRow(row); renumberRows(); row.querySelector('[contenteditable="true"]')?.focus(); recalculate(); showToast('New expense added.');
}
function saveBudget(){
    const payload={room:getChoice('room','Living Room'),budget:numericText(document.getElementById('totalBudgetDisplay')?.textContent),rows:getRows().map(row=>({item:row.children[1]?.textContent.trim(),category:row.querySelector('.cat-tag')?.textContent.trim(),cost:numericText(row.querySelector('.cost-cell')?.textContent),quantity:numericText(row.querySelector('.qty-cell')?.textContent)||1}))};
    localStorage.setItem('nsDesignBudget',JSON.stringify(payload)); showToast('Budget saved on this device.');
}
function downloadSummary(){
    const lines=['NS DESIGN AI — BUDGET SUMMARY','',`Room: ${getChoice('room','Room')}`,`Total budget: ${document.getElementById('totalBudgetDisplay')?.textContent||'₹0'}`,`Estimated cost: ${document.getElementById('estimatedCostDisplay')?.textContent||'₹0'}`,`Remaining: ${document.getElementById('remainingDisplay')?.textContent||'₹0'}`,'','EXPENSES'];
    getRows().forEach((row,index)=>lines.push(`${index+1}. ${row.children[1]?.textContent.trim()} — ${row.querySelector('.total-cell')?.textContent.trim()||'0'}`));
    const blob=new Blob([lines.join('\n')],{type:'text/plain'}); const link=document.createElement('a'); link.href=URL.createObjectURL(blob); link.download='ns-design-budget-summary.txt'; link.click(); URL.revokeObjectURL(link.href); showToast('Summary downloaded.');
}
document.addEventListener('DOMContentLoaded',()=>{
    const budgetInput=document.getElementById('totalBudgetInput');
    getRows().forEach(bindRow);
    budgetInput?.addEventListener('keydown',event=>{if(event.key==='Enter') createBudget();});
    recalculate();
 
    // scroll reveal (look only)
    const io=new IntersectionObserver(es=>es.forEach(en=>{if(en.isIntersecting){en.target.classList.add('in');io.unobserve(en.target);}}),{threshold:.1});
    document.querySelectorAll('.reveal').forEach(el=>io.observe(el));
});
