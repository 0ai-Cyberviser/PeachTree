const grid=document.getElementById('datasetGrid');
if(grid){
const datasets=[
{name:'PeachFuzz Corpus',desc:'Crash + repro dataset lane'},
{name:'Hancock Instructions',desc:'Security agent training data'},
{name:'Owned Repo Knowledge',desc:'Docs + code structured records'}
];
datasets.forEach(d=>{
const el=document.createElement('div');
el.innerHTML=`<strong>${d.name}</strong><p>${d.desc}</p>`;
grid.appendChild(el);
});
}
