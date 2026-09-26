export default async function handler(req,res){
 if(req.method!=='POST') return res.status(405).json({error:'Method not allowed'});
 if(!process.env.STRIPE_SECRET_KEY) return res.status(503).json({message:'Stripe non configuré.'});
 if(!process.env.STRIPE_STARTER_PRICE_ID) return res.status(503).json({message:'STRIPE_STARTER_PRICE_ID non configuré.'});
 try{
  const body=new URLSearchParams({mode:'payment','line_items[0][price]':process.env.STRIPE_STARTER_PRICE_ID,'line_items[0][quantity]':'1',success_url:(process.env.APP_URL||'http://localhost:3000')+'/business/?paid=1',cancel_url:(process.env.APP_URL||'http://localhost:3000')+'/business/?cancelled=1'});
  const r=await fetch('https://api.stripe.com/v1/checkout/sessions',{method:'POST',headers:{Authorization:'Bearer '+process.env.STRIPE_SECRET_KEY,'Content-Type':'application/x-www-form-urlencoded'},body});
  const j=await r.json(); if(!r.ok)return res.status(502).json({message:j.error?.message||'Stripe error'}); return res.status(200).json({url:j.url});
 }catch(e){return res.status(500).json({message:e.message})}
}