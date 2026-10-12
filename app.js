(() => {
  'use strict';
  const $ = (id) => document.getElementById(id);
  const state = { dataset: null, filters: [], result: null, server: null, username: '', language: localStorage.getItem('fieldnote-language') || 'en', authMode: 'login' };
  const originalText = new WeakMap();
  const hiText = new Map(Object.entries({
    'YOUR WORKSPACE':'आपका कार्यक्षेत्र','YOUR DATA':'आपका डेटा','Add data':'डेटा जोड़ें','Your data stays yours':'आपका डेटा सुरक्षित है','Rows stay on this machine.':'डेटा इसी कंप्यूटर पर रहता है।','Personal workspace':'निजी कार्यक्षेत्र','Workspace':'कार्यस्थान','Overview':'अवलोकन','Local analysis':'स्थानीय विश्लेषण','YOUR DATA, IN PLAIN ENGLISH':'आपका डेटा, आसान भाषा में','Good questions make':'अच्छे सवाल बेहतर','better decisions.':'फ़ैसले लाते हैं।','Bring a CSV. Ask what\'s on your mind. Get a clear answer, backed by a chart you can trust.':'CSV जोड़ें, सवाल पूछें और चार्ट के साथ साफ़ जवाब पाएं।','A quieter way to work with data':'डेटा के साथ काम करने का सरल तरीका','START WITH A FILE':'फ़ाइल से शुरू करें','Bring your data in':'अपना डेटा जोड़ें','Or try a sample':'या नमूना देखें','Drop your CSV here':'अपनी CSV यहाँ छोड़ें','browse files':'फ़ाइल चुनें','on your computer':'अपने कंप्यूटर से','PRIVATE LOCAL SESSION':'निजी स्थानीय सत्र','Preview rows':'पंक्तियाँ देखें','Clean duplicates':'डुप्लिकेट हटाएँ','Remove incomplete':'अधूरी पंक्तियाँ हटाएँ','Undo':'वापस करें','First rows':'पहली पंक्तियाँ','FILTER THIS ANALYSIS':'विश्लेषण फ़िल्टर करें','Choose a column':'कॉलम चुनें','Choose a value':'मान चुनें','ASK A QUESTION':'सवाल पूछें','What would you like to know?':'आप क्या जानना चाहते हैं?','AI wording help':'स्मार्ट सवाल सहायता','Find out':'जवाब देखें','A FEW IDEAS':'कुछ सुझाव','Total revenue':'कुल बिक्री','Best performing region':'सबसे अच्छा क्षेत्र','Revenue over time':'समय के साथ बिक्री','YOUR ANSWER':'आपका जवाब','COMPARISON':'तुलना','TREND':'रुझान','COUNTS':'गिनती','SUMMARY':'सारांश','RELATIONSHIP':'संबंध','SVG':'SVG चार्ट','PNG':'PNG चार्ट','Results':'परिणाम','Report':'रिपोर्ट','What this tells you':'इसका मतलब','Ask another':'एक और सवाल','THE SHORT VERSION':'संक्षेप में','Analysis that shows its work.':'पारदर्शी विश्लेषण।','Fieldnote looks at your columns, works out what you\'re asking, and explains the result in everyday language.':'Fieldnote आपके कॉलम समझकर रोज़मर्रा की भाषा में नतीजा बताता है।','See how your numbers were calculated':'गणना कैसे हुई, देखें','Get a chart that fits the question':'सवाल के अनुसार चार्ट पाएँ','Your file stays right here':'आपकी फ़ाइल यहीं रहती है','AT A GLANCE':'एक नज़र में','Your dataset':'आपका डेटासेट','WAITING':'प्रतीक्षा में','READY':'तैयार','ROWS':'पंक्तियाँ','COLUMNS':'कॉलम','NUMERIC FIELDS':'संख्यात्मक कॉलम','MISSING':'खाली मान','DUPLICATES':'डुप्लिकेट','YOUR RECENT WORK':'हाल का काम','Recent questions':'हाल के सवाल','Clear':'साफ़ करें','Your questions will show up here.':'आपके सवाल यहाँ दिखेंगे।','A little specificity goes a long way.':'सवाल स्पष्ट रखें।','Try naming the thing you want to compare, like “average order value by channel.”':'जिस चीज़ की तुलना करनी है, उसका नाम लिखें।','Made for curious people and the spreadsheets they inherit.':'जिज्ञासु लोगों और उनकी स्प्रेडशीट के लिए।','Runs on this machine':'इसी कंप्यूटर पर चलता है','About Fieldnote':'Fieldnote के बारे में','A NOTE FROM FIELDNOTE':'Fieldnote की ओर से','How it works':'यह कैसे काम करता है','Your file isn’t uploaded anywhere.':'आपकी फ़ाइल कहीं अपलोड नहीं होती।','Sign in':'लॉग इन करें','Sign out':'लॉग आउट','Log out':'लॉग आउट','Username':'यूज़रनेम','Password':'पासवर्ड','Your username':'अपना यूज़रनेम','At least 8 characters':'कम से कम 8 अक्षर','Welcome back.':'वापसी पर स्वागत है।','Create your account.':'अपना खाता बनाएँ।','Sign in to open your private Fieldnote workspace.':'अपने निजी Fieldnote कार्यक्षेत्र में लॉग इन करें।','Choose a username and password for this machine.':'इस कंप्यूटर के लिए यूज़रनेम और पासवर्ड चुनें।','New to Fieldnote?':'Fieldnote पर नए हैं?','Already have an account?':'पहले से खाता है?','Create an account':'खाता बनाएँ','Your workspace and account stay on this machine.':'आपका खाता और कार्यक्षेत्र इसी कंप्यूटर पर रहते हैं।','A QUIETER WAY TO WORK WITH DATA':'डेटा के साथ काम करने का सरल तरीका','FIELDNOTE · LOCAL DATA WORKSPACE':'FIELDNOTE · स्थानीय डेटा कार्यक्षेत्र','Flexible question matching works offline · AI is optional':'सवाल मिलान ऑफ़लाइन चलता है · AI वैकल्पिक है','Local analysis · AI is optional':'स्थानीय विश्लेषण · AI वैकल्पिक है','Try a CSV or use the sample dataset.':'CSV जोड़ें या नमूना डेटा चुनें।','Reading the file…':'फ़ाइल पढ़ी जा रही है…','Choose a CSV or Excel .xlsx file. Older .xls files aren’t supported.':'CSV या Excel .xlsx चुनें। पुरानी .xls फ़ाइल समर्थित नहीं है।','Loading…':'लोड हो रहा है…'
  }));
  hiText.set('Smart wording help','सवाल समझने में मदद');
  hiText.set('Values behind the chart','चार्ट के मान');
  hiText.set('rows considered','पंक्तियाँ शामिल');
  hiText.set('Source rows','स्रोत पंक्तियाँ');
  hiText.set('Measure','माप');
  hiText.set('Rows','पंक्तियाँ');
  hiText.set('Value','मान');
  hiText.set('Based on all rows in your dataset','आपके डेटासेट की सभी पंक्तियों पर आधारित');
  function setLanguage(language, rerun = true) {
    state.language = language === 'hi' ? 'hi' : 'en'; localStorage.setItem('fieldnote-language', state.language); document.documentElement.lang = state.language;
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT); let node;
    while ((node = walker.nextNode())) { if (!originalText.has(node)) originalText.set(node, node.nodeValue); const source=originalText.get(node), trimmed=source.trim(); if (state.language==='hi' && hiText.has(trimmed)) node.nodeValue=source.replace(trimmed,hiText.get(trimmed)); else node.nodeValue=source; }
    for (const id of ['languageToggle','authLanguageToggle']) { const button=document.getElementById(id); if(button)button.textContent=state.language==='hi'?'English':'हिंदी'; }
    const labels={questionInput:'e.g. Which region brought in the most revenue?',authUsername:'Your username',authPassword:'At least 8 characters'};
    for(const [id,english] of Object.entries(labels)){const el=$(id);if(el){const hi={'e.g. Which region brought in the most revenue?':'उदाहरण: किस क्षेत्र की बिक्री सबसे अधिक है?','Your username':'अपना यूज़रनेम','At least 8 characters':'कम से कम 8 अक्षर'}[english];el.placeholder=state.language==='hi'?hi:english;}}
    if(state.dataset) $('questionHelper').textContent=state.language==='hi'?'स्थानीय विश्लेषण · AI वैकल्पिक है':'Flexible question matching works offline · AI is optional';
    if(rerun && state.result && state.dataset) runQuestion($('questionInput').value.trim());
  }
  function setTheme(theme) {
    const value=theme==='dark'?'dark':'light';document.documentElement.dataset.theme=value;localStorage.setItem('fieldnote-theme',value);
    for(const id of ['themeToggle','authThemeToggle']){const button=$(id);if(button){button.textContent=value==='dark'?'☀':'◐';button.title=value==='dark'?'Switch to light mode':'Switch to dark mode';}}
  }
  const sampleCSV = `Order date,Region,Channel,Product,Units sold,Revenue,Cost,Customer rating
2025-01-08,North,Online,Desk lamp,34,2380,1292,4.6
2025-01-17,South,In store,Ceramic mug,58,1160,638,4.2
2025-02-03,West,Online,Notebook set,72,1440,720,4.7
2025-02-21,East,Partner,Desk lamp,19,1330,722,4.1
2025-03-05,North,In store,Ceramic mug,81,1620,810,4.5
2025-03-19,South,Online,Notebook set,94,1880,940,4.8
2025-04-02,West,Partner,Desk lamp,27,1890,1026,4.3
2025-04-18,East,Online,Ceramic mug,63,1260,693,4.4
2025-05-07,North,Partner,Notebook set,41,820,410,4.6
2025-05-22,South,In store,Desk lamp,39,2730,1482,4.2
2025-06-10,West,Online,Ceramic mug,88,1760,968,4.9
2025-06-26,East,Partner,Notebook set,67,1340,670,4.5
2025-07-11,North,Online,Desk lamp,46,3220,1748,4.7
2025-07-28,South,Partner,Ceramic mug,76,1520,836,4.3
2025-08-06,West,In store,Notebook set,83,1660,830,4.6
2025-08-23,East,Online,Desk lamp,31,2170,1178,4.4
2025-09-04,North,In store,Ceramic mug,69,1380,759,4.8
2025-09-20,South,Online,Notebook set,102,2040,1020,4.9
2025-10-09,West,Partner,Desk lamp,36,2520,1368,4.4
2025-10-25,East,In store,Ceramic mug,73,1460,803,4.6
2025-11-12,North,Online,Notebook set,98,1960,980,4.9
2025-11-27,South,Partner,Desk lamp,43,3010,1634,4.5
2025-12-08,West,Online,Ceramic mug,91,1820,1001,4.8
2025-12-21,East,In store,Notebook set,77,1540,770,4.7`;

  async function api(path, options = {}) {
    const response = await fetch(path, options);
    let payload;
    try { payload = await response.json(); } catch { payload = {}; }
    if (!response.ok) throw new Error(payload.error || `The server returned ${response.status}.`);
    return payload;
  }
  function setAuthMode(mode) {
    state.authMode=mode==='register'?'register':'login';const register=state.authMode==='register';
    $('authTitle').textContent=register?'Create your account.':'Welcome back.';$('authIntro').textContent=register?'Choose a username and password for this machine.':'Sign in to open your private Fieldnote workspace.';$('authSubmit').textContent=register?'Create account':'Sign in';$('authSwitchText').textContent=register?'Already have an account?':'New to Fieldnote?';$('authSwitchButton').textContent=register?'Sign in':'Create an account';$('authPassword').autocomplete=register?'new-password':'current-password';$('authError').classList.add('hidden');$('authPassword').value='';setLanguage(state.language,false);
  }
  function showWorkspace(username) {
    state.username=username;$('sideUser').textContent=username;$('authScreen').classList.add('hidden');$('appShell').classList.remove('hidden');renderHistory();setLanguage(state.language,false);loadServerStatus();
  }
  function showLogin() {
    $('appShell').classList.add('hidden');$('authScreen').classList.remove('hidden');setAuthMode('login');
  }
  async function checkAuthentication() {
    try {const user=await api('/api/auth/me');showWorkspace(user.username);}
    catch {showLogin();}
  }
  function esc(value) { return String(value ?? '').replace(/[&<>"']/g, (c) => ({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;' }[c])); }
  function fmt(value) { return Number(value).toLocaleString(undefined, { maximumFractionDigits: Math.abs(Number(value)) >= 100 ? 1 : 2 }); }
  function showToast(message) { const toast = $('toast'); toast.textContent = message; toast.classList.remove('hidden'); clearTimeout(showToast.timer); showToast.timer = setTimeout(() => toast.classList.add('hidden'), 4500); }

  async function loadServerStatus() {
    try { state.server = await api('/api/status'); }
    catch { showToast('Start Fieldnote with “py server.py” to use this version.'); }
  }
  function setBusy(busy) {
    const button = $('askButton'); button.disabled = busy || !state.dataset;
    button.innerHTML = busy ? `${state.language==='hi'?'काम हो रहा है…':'Working…'} <span>↗</span>` : `${state.language==='hi'?'जवाब देखें':'Find out'} <span>→</span>`;
  }
  async function uploadFile(file) {
    if (!file) return;
    if (!/\.(csv|xlsx|xlsm)$/i.test(file.name)) return setError('Choose a CSV or Excel .xlsx file. Older .xls files aren’t supported.');
    if (file.size > 25 * 1024 * 1024) return setError('This file is over 25 MB. Try a smaller export or remove columns you don’t need.');
    setError(''); $('questionHelper').textContent = 'Reading the file…';
    const form = new FormData(); form.append('file', file);
    try { const meta = await api('/api/upload', { method:'POST', body:form }); showDataset(meta); showToast(`Loaded ${meta.fileName}`); }
    catch (error) { setError(error.message); $('questionHelper').textContent = 'Try another file or use the sample dataset.'; }
  }
  function setError(message) { const box = $('fileError'); if (!message) { box.classList.add('hidden'); box.textContent=''; return; } box.textContent=message; box.classList.remove('hidden'); }
  function historyStorageKey(){return `fieldnote-history:${state.username||'guest'}`;}
  function showDataset(meta) {
    state.dataset = meta; state.filters = []; state.result = null;
    $('datasetName').textContent=meta.fileName; $('crumbDataset').textContent=meta.fileName; $('summaryFileName').textContent=meta.fileName; $('summaryMeta').textContent=`${fmt(meta.totalRows)} rows · ${meta.totalColumns} columns`;
    $('columnChips').innerHTML=meta.headers.slice(0,10).map((h)=>`<span class="column-chip ${meta.types[h]==='number'?'numeric':''}">${esc(h)}</span>`).join('')+(meta.headers.length>10?`<span class="column-chip">+${meta.headers.length-10} more</span>`:'');
    $('statRows').textContent=fmt(meta.totalRows); $('statColumns').textContent=meta.totalColumns; $('statNumeric').textContent=meta.numericColumns.join(', ')||'None detected'; $('statMissing').textContent=fmt(meta.missingCells); $('statDuplicates').textContent=fmt(meta.duplicateRows);
    $('datasetSummary').classList.remove('hidden'); $('dropZone').classList.add('hidden'); $('emptyStats').classList.add('hidden'); $('statsGrid').classList.remove('hidden'); $('datasetStatus').textContent='READY'; $('datasetStatus').classList.add('ready'); $('questionInput').disabled=false; $('askButton').disabled=false; $('useAI').disabled=!meta.aiAvailable;
    $('questionHelper').textContent=state.language==='hi'?'स्थानीय विश्लेषण · AI वैकल्पिक है':meta.aiAvailable?`Local analysis · ${meta.aiModel} can help interpret wording`:'Flexible question matching works offline · AI is optional';
    $('useAI').disabled=false;
    $('filterColumn').innerHTML='<option value="">Choose a column</option>'+meta.headers.map((h)=>`<option value="${esc(h)}">${esc(h)}</option>`).join('');
    $('filterColumn').disabled=false; $('filterValue').disabled=true; $('addFilter').disabled=true;
    renderPreview(meta); renderFilters(); setError(''); $('resultPanel').classList.add('hidden');setLanguage(state.language,false);
  }
  function renderPreview(meta) {
    const shown = meta.preview.slice(0,12);
    const head=`<thead><tr>${meta.headers.map((h)=>`<th>${esc(h)}<select class="type-select" data-column-type data-column="${esc(h)}" aria-label="Type for ${esc(h)}"><option value="category" ${meta.types[h]==='category'?'selected':''}>category</option><option value="number" ${meta.types[h]==='number'?'selected':''}>number</option><option value="date" ${meta.types[h]==='date'?'selected':''}>date</option></select></th>`).join('')}</tr></thead>`;
    const body=`<tbody>${shown.map((row)=>`<tr>${meta.headers.map((h)=>`<td class="${!String(row[h]??'').trim()?'missing-cell':''}">${String(row[h]??'').trim()?esc(row[h]):'<span>empty</span>'}</td>`).join('')}</tr>`).join('')}</tbody>`;
    $('previewTable').innerHTML=head+body; $('previewMeta').textContent=`Showing ${shown.length} of ${fmt(meta.totalRows)} rows · column types inferred from values`;
    $('previewTable').querySelectorAll('[data-column-type]').forEach(select=>select.addEventListener('change',async()=>{try{const updated=await api('/api/types',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({datasetId:state.dataset.id,column:select.dataset.column,type:select.value})});showDataset(updated);$('previewArea').classList.remove('hidden');showToast(updated.message);}catch(error){showToast(error.message);}}));
    const labels=[]; if(meta.missingCells) labels.push(`${fmt(meta.missingCells)} empty cells`); if(meta.duplicateRows) labels.push(`${fmt(meta.duplicateRows)} duplicate rows`);
    $('qualitySummary').textContent=labels.length?`Data quality · ${labels.join(' · ')}`:'Data quality · no blank or duplicate cells found';
  }
  function renderFilters() {
    $('activeFilters').innerHTML=state.filters.map((item,index)=>`<button class="filter-chip" data-filter="${index}">${esc(item.column)} = ${esc(item.value)} <span>×</span></button>`).join('');
    $('activeFilters').querySelectorAll('[data-filter]').forEach((button)=>button.addEventListener('click',()=>{state.filters.splice(Number(button.dataset.filter),1);renderFilters();}));
  }
  async function refreshDataset() {
    if (!state.dataset) return;
    const meta=await api(`/api/dataset?id=${encodeURIComponent(state.dataset.id)}`); showDataset(meta);
  }
  async function cleanup(action) {
    if (!state.dataset) return;
    const button = action==='duplicates' ? $('duplicatesButton') : action==='empty' ? $('emptyRowsButton') : $('undoClean'); button.disabled=true;
    try { const meta=await api('/api/clean',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({datasetId:state.dataset.id,action})}); showDataset(meta); $('undoClean').disabled=false; showToast(meta.message); }
    catch(error) { showToast(error.message); }
    finally { button.disabled=false; }
  }
  async function runQuestion(question = $('questionInput').value.trim()) {
    if (!state.dataset || !question) return;
    $('questionInput').value=question; setBusy(true);
    try {
      const result=await api('/api/analyze',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({datasetId:state.dataset.id,question,filters:state.filters,useAI:$('useAI').checked,language:state.language})});
      state.result=result; renderResult(result); saveHistory(question,result); $('resultPanel').classList.remove('hidden'); $('resultPanel').scrollIntoView({behavior:'smooth',block:'nearest'});
    } catch(error) { showToast(error.message); }
    finally { setBusy(false); }
  }
  function renderResult(result) {
    $('resultTitle').textContent=result.title; $('resultType').textContent=result.type; $('chartWrap').innerHTML=renderChart(result);
    $('explanation').textContent=result.explanation; $('methodNote').textContent=result.note; $('resultFootnote').textContent=result.footnote;
    const points=result.type==='RELATIONSHIP'?[]:result.points;
    $('resultTableWrap').innerHTML=points.length?`<div class="result-table-title">Values behind the chart <span>${fmt(result.usedRows)} rows considered</span></div><div class="table-scroll"><table><thead><tr><th>${esc(result.group||'Measure')}</th><th>${result.operation==='count'?'Rows':esc(result.metric||'Value')}</th><th>Source rows</th></tr></thead><tbody>${points.slice(0,20).map((p)=>`<tr><td>${esc(p.label)}</td><td>${fmt(p.value)}</td><td>${fmt(p.rows)}</td></tr>`).join('')}</tbody></table></div>${points.length>20?`<small class="table-note">Showing first 20 of ${points.length} groups. Download results for the complete list.</small>`:''}`:'';
    setLanguage(state.language,false);
  }
  function renderChart(result) {
    const w=650,h=230;
    if(result.type==='RELATIONSHIP'){
      const pts=result.points,left=49,right=12,top=14,bottom=35,cw=w-left-right,ch=h-top-bottom;
      const xs=pts.map(p=>p.x),ys=pts.map(p=>p.y);let xmin=Math.min(...xs),xmax=Math.max(...xs),ymin=Math.min(...ys),ymax=Math.max(...ys);if(xmax===xmin)xmax++;if(ymax===ymin)ymax++;
      let svg=`<svg class="chart-svg" viewBox="0 0 ${w} ${h}" role="img" aria-label="Scatter plot of ${esc(result.title)}"><title>${esc(result.title)} scatter plot</title>`;
      for(let i=0;i<5;i++){let x=left+cw*i/4,y=top+ch-ch*i/4;svg+=`<line class="chart-grid" x1="${x}" y1="${top}" x2="${x}" y2="${top+ch}"/><line class="chart-grid" x1="${left}" y1="${y}" x2="${w-right}" y2="${y}"/><text class="chart-axis" x="${x}" y="${h-14}" text-anchor="middle">${fmt(xmin+(xmax-xmin)*i/4)}</text><text class="chart-axis" x="${left-7}" y="${y+3}" text-anchor="end">${fmt(ymin+(ymax-ymin)*i/4)}</text>`;}
      pts.forEach(p=>{const x=left+(p.x-xmin)/(xmax-xmin)*cw,y=top+ch-(p.y-ymin)/(ymax-ymin)*ch;svg+=`<circle class="chart-dot" cx="${x}" cy="${y}" r="3" opacity=".72"><title>${esc(result.metric)} ${fmt(p.x)}, ${esc(result.second)} ${fmt(p.y)}</title></circle>`;});
      return `${svg}<text class="chart-label" x="${left+cw/2}" y="${h-1}" text-anchor="middle">${esc(result.metric)}</text></svg>`;
    }
    const points=result.points,left=48,right=12,top=17,bottom=40,cw=w-left-right,ch=h-top-bottom,max=Math.max(...points.map(p=>p.value),1),min=Math.min(0,...points.map(p=>p.value)),span=max-min||1,slot=cw/points.length;
    let svg=`<svg class="chart-svg" viewBox="0 0 ${w} ${h}" role="img" aria-label="${esc(result.title)} chart"><title>${esc(result.title)}</title>`;
    for(let i=0;i<=4;i++){const val=min+span*i/4,y=top+ch-(val-min)/span*ch;svg+=`<line class="chart-grid" x1="${left}" y1="${y}" x2="${w-right}" y2="${y}"/><text class="chart-axis" x="${left-7}" y="${y+3}" text-anchor="end">${esc(fmt(val))}</text>`;}
    if(result.type==='TREND'&&points.length>2){const coords=points.map((p,i)=>[left+slot*(i+.5),top+ch-(p.value-min)/span*ch]);const line=coords.map((c,i)=>`${i?'L':'M'}${c[0]},${c[1]}`).join(' ');svg+=`<path class="chart-area" d="${line} L${coords.at(-1)[0]},${top+ch} L${coords[0][0]},${top+ch} Z"/><path class="chart-line" d="${line}"/>`;coords.forEach((c,i)=>{svg+=`<circle class="chart-dot" cx="${c[0]}" cy="${c[1]}" r="3.5"><title>${esc(points[i].label)}: ${fmt(points[i].value)}</title></circle>`;if(points.length<=12||i%Math.ceil(points.length/10)===0)svg+=`<text class="chart-label" x="${c[0]}" y="${h-12}" text-anchor="middle">${esc(points[i].label)}</text>`;});}
    else{const bw=Math.min(36,slot*.55);points.forEach((p,i)=>{const x=left+slot*i+(slot-bw)/2,bh=(p.value-min)/span*ch,y=top+ch-bh;svg+=`<rect class="chart-bar" x="${x}" y="${y}" width="${bw}" height="${Math.max(1,bh)}" rx="3"><title>${esc(p.label)}: ${fmt(p.value)}</title></rect>`;if(points.length<=8)svg+=`<text class="chart-value" x="${x+bw/2}" y="${Math.max(11,y-6)}" text-anchor="middle">${esc(fmt(p.value))}</text>`;svg+=`<text class="chart-label" x="${x+bw/2}" y="${h-12}" text-anchor="middle">${esc(p.label.length>12?p.label.slice(0,11)+'…':p.label)}</text>`;});}
    return `${svg}</svg>`;
  }
  function saveHistory(question,result) {
    const history=JSON.parse(localStorage.getItem(historyStorageKey())||'[]').filter(item=>item.question!==question);
    history.unshift({question,title:result.title,at:new Date().toISOString(),result});
    localStorage.setItem(historyStorageKey(),JSON.stringify(history.slice(0,12))); renderHistory();
  }
  function renderHistory(){
    const history=JSON.parse(localStorage.getItem(historyStorageKey())||'[]');
    $('historyList').innerHTML=history.length?history.slice(0,6).map((item,i)=>`<button class="history-item" data-history="${i}"><span class="history-question">${esc(item.question)}</span><span class="history-result">${esc(item.title)} <span>↗</span></span></button>`).join(''):'<span class="history-empty">Your questions will show up here.</span>';
    $('historyList').querySelectorAll('[data-history]').forEach(button=>button.addEventListener('click',()=>{const item=history[Number(button.dataset.history)];$('questionInput').value=item.question;runQuestion(item.question);}));setLanguage(state.language,false);
  }
  function saveBlob(blob,name){const url=URL.createObjectURL(blob),link=document.createElement('a');link.href=url;link.download=name;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
  function downloadSvg(){const svg=$('chartWrap').querySelector('svg');if(!svg)return;const clone=svg.cloneNode(true);clone.setAttribute('xmlns','http://www.w3.org/2000/svg');clone.setAttribute('width','1300');clone.setAttribute('height','460');saveBlob(new Blob([new XMLSerializer().serializeToString(clone)],{type:'image/svg+xml;charset=utf-8'}),'fieldnote-chart.svg');}
  function downloadPng(){const svg=$('chartWrap').querySelector('svg');if(!svg)return;const clone=svg.cloneNode(true);clone.setAttribute('xmlns','http://www.w3.org/2000/svg');clone.setAttribute('width','1300');clone.setAttribute('height','460');const url=URL.createObjectURL(new Blob([new XMLSerializer().serializeToString(clone)],{type:'image/svg+xml'}));const img=new Image();img.onload=()=>{const canvas=document.createElement('canvas');canvas.width=1300;canvas.height=460;const ctx=canvas.getContext('2d');ctx.fillStyle='#fff';ctx.fillRect(0,0,1300,460);ctx.drawImage(img,0,0,1300,460);canvas.toBlob(blob=>{if(blob)saveBlob(blob,'fieldnote-chart.png');URL.revokeObjectURL(url);});};img.onerror=()=>{URL.revokeObjectURL(url);showToast('Could not export this chart as a PNG. Try SVG instead.');};img.src=url;}
  function downloadCsv(){if(!state.result)return;const rows=state.result.points||[];const q=[['Fieldnote result',state.result.title],['Label',state.result.type==='RELATIONSHIP'?state.result.metric:state.result.group||'Measure'],['Value',state.result.type==='RELATIONSHIP'?state.result.second:state.result.metric||'Rows'],['Source rows','Rows in group'],...rows.map(p=>[p.label,p.value,p.rows])];const csv=q.map(row=>row.map(v=>{let value=v??'';if(typeof value!=='number'&&/^[\s]*[=+@\-\t\r]/.test(String(value)))value="'"+value;return `"${String(value).replace(/"/g,'""')}"`;}).join(',')).join('\r\n');saveBlob(new Blob(['\uFEFF'+csv],{type:'text/csv;charset=utf-8'}),'fieldnote-results.csv');}
  function downloadReport(){if(!state.result)return;const svg=$('chartWrap').querySelector('svg')?.outerHTML||'';const result=state.result;const html=`<!doctype html><meta charset="utf-8"><title>${esc(result.title)} — Fieldnote</title><style>body{font:16px Arial,sans-serif;max-width:900px;margin:50px auto;color:#293b30}h1{font-size:30px}p{line-height:1.6;color:#66746a}svg{width:100%;height:auto}.note{font-size:13px;color:#879087;border-top:1px solid #ddd;padding-top:14px}</style><p>FIELDNOTE · DATA NOTE</p><h1>${esc(result.title)}</h1><p>${esc(result.explanation)}</p>${svg}<p>${esc(result.note)}</p><p class="note">${esc(result.footnote)}<br>Generated ${new Date().toLocaleString()}</p>`;saveBlob(new Blob([html],{type:'text/html'}),'fieldnote-report.html');}
  async function clearDataset(){if(state.dataset){try{await api(`/api/dataset?id=${encodeURIComponent(state.dataset.id)}`,{method:'DELETE'});}catch{}}state.dataset=null;state.filters=[];state.result=null;$('datasetName').textContent='No dataset yet';$('crumbDataset').textContent='Overview';$('datasetSummary').classList.add('hidden');$('dropZone').classList.remove('hidden');$('statsGrid').classList.add('hidden');$('emptyStats').classList.remove('hidden');$('datasetStatus').textContent='WAITING';$('datasetStatus').classList.remove('ready');$('questionInput').value='';$('questionInput').disabled=true;$('askButton').disabled=true;$('useAI').checked=false;$('useAI').disabled=true;$('questionHelper').textContent='Add a file first — your question will find its footing.';$('resultPanel').classList.add('hidden');$('fileInput').value='';}

  const fileInput=$('fileInput'),dropZone=$('dropZone');
  $('browseButton').addEventListener('click',e=>{e.stopPropagation();fileInput.click();});$('sidebarUpload').addEventListener('click',()=>fileInput.click());dropZone.addEventListener('click',e=>{if(e.target!==$('browseButton'))fileInput.click();});dropZone.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();fileInput.click();}});fileInput.addEventListener('change',()=>uploadFile(fileInput.files[0]));
  ['dragenter','dragover'].forEach(event=>dropZone.addEventListener(event,e=>{e.preventDefault();dropZone.classList.add('dragover');}));['dragleave','drop'].forEach(event=>dropZone.addEventListener(event,e=>{e.preventDefault();dropZone.classList.remove('dragover');}));dropZone.addEventListener('drop',e=>uploadFile(e.dataTransfer.files[0]));
  $('sampleButton').addEventListener('click',()=>uploadFile(new File([sampleCSV],'shop-orders-sample.csv',{type:'text/csv'})));$('askButton').addEventListener('click',()=>runQuestion());$('questionInput').addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();runQuestion();}});
  document.querySelectorAll('.suggestion').forEach(button=>button.addEventListener('click',()=>{if(!state.dataset){showToast('Load a file or try the sample first.');return;}runQuestion(button.dataset.question);}));
  $('removeFile').addEventListener('click',clearDataset);$('previewToggle').addEventListener('click',()=>{$('previewArea').classList.toggle('hidden');$('previewToggle').classList.toggle('selected');});$('duplicatesButton').addEventListener('click',()=>cleanup('duplicates'));$('emptyRowsButton').addEventListener('click',()=>cleanup('empty'));$('undoClean').addEventListener('click',()=>cleanup('undo'));
  $('filterColumn').addEventListener('change',()=>{const col=$('filterColumn').value,values=state.dataset?.filterOptions?.[col]||[];$('filterValue').innerHTML='<option value="">Choose a value</option>'+values.map(value=>`<option value="${esc(value)}">${esc(value||'(blank)')}</option>`).join('');$('filterValue').disabled=!col;$('addFilter').disabled=true;});$('filterValue').addEventListener('change',()=>{$('addFilter').disabled=!$('filterValue').value&&$('filterValue').value!=='';});$('addFilter').addEventListener('click',()=>{const column=$('filterColumn').value,value=$('filterValue').value;if(!column)return;state.filters.push({column,value:value||'(blank)'});renderFilters();$('filterValue').selectedIndex=0;});
  $('downloadButton').addEventListener('click',downloadSvg);$('pngButton').addEventListener('click',downloadPng);$('csvButton').addEventListener('click',downloadCsv);$('reportButton').addEventListener('click',downloadReport);$('newQuestion').addEventListener('click',()=>$('questionInput').focus());
  $('clearHistory').addEventListener('click',()=>{localStorage.removeItem(historyStorageKey());renderHistory();});$('helpButton').addEventListener('click',()=>$('helpDialog').showModal());$('closeHelp').addEventListener('click',()=>$('helpDialog').close());$('helpDialog').addEventListener('click',e=>{if(e.target===$('helpDialog'))$('helpDialog').close();});
  $('authForm').addEventListener('submit',async event=>{event.preventDefault();const button=$('authSubmit'),username=$('authUsername').value.trim(),password=$('authPassword').value,mode=state.authMode;button.disabled=true;button.textContent=mode==='register'?'Creating…':'Signing in…';$('authError').classList.add('hidden');try{const user=await api(`/api/auth/${mode}`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username,password})});$('authPassword').value='';showWorkspace(user.username);}catch(error){$('authError').textContent=error.message;$('authError').classList.remove('hidden');}finally{button.disabled=false;button.textContent=mode==='register'?'Create account':'Sign in';setLanguage(state.language,false);}});
  $('authSwitchButton').addEventListener('click',()=>setAuthMode(state.authMode==='login'?'register':'login'));
  $('logoutButton').addEventListener('click',async()=>{try{if(state.dataset)await api(`/api/dataset?id=${encodeURIComponent(state.dataset.id)}`,{method:'DELETE'});await api('/api/auth/logout',{method:'POST'});}catch{}state.dataset=null;state.filters=[];state.result=null;showLogin();});
  const toggleLanguage=()=>setLanguage(state.language==='en'?'hi':'en');$('languageToggle').addEventListener('click',toggleLanguage);$('authLanguageToggle').addEventListener('click',toggleLanguage);
  const toggleTheme=()=>setTheme(document.documentElement.dataset.theme==='dark'?'light':'dark');$('themeToggle').addEventListener('click',toggleTheme);$('authThemeToggle').addEventListener('click',toggleTheme);
  $('questionInput').disabled=true;$('useAI').disabled=true;renderHistory();setTheme(localStorage.getItem('fieldnote-theme')||'light');setAuthMode(state.authMode);checkAuthentication();
})();
