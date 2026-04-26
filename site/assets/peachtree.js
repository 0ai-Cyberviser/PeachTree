const grid=document.getElementById('datasetGrid');

async function loadDatasets(){
  try{
    const res=await fetch('../data/site/dataset-lanes.json');
    const data=await res.json();

    data.forEach(d=>{
      const el=document.createElement('div');
      el.style.background='#111827';
      el.style.padding='12px';
      el.style.borderRadius='8px';

      el.innerHTML=`
        <strong>${d.name}</strong>
        <p>Status: ${d.status}</p>
        <p><small>Source: ${d.source}</small></p>
        <p><small>Outputs: ${d.outputs.join(', ')}</small></p>
      `;

      grid.appendChild(el);
    });

  }catch(e){
    grid.innerHTML='<p>Dataset manifest not found yet.</p>';
  }
}

if(grid){
  loadDatasets();
}
