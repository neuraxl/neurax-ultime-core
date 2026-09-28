import Stripe from "stripe";
export const config={api:{bodyParser:false}};
export default async function handler(req,res){
  if(req.method!=="POST") return res.status(405).end();
  if(!process.env.STRIPE_SECRET_KEY||!process.env.STRIPE_WEBHOOK_SECRET)
    return res.status(503).json({error:"Stripe is not configured"});
  const stripe=new Stripe(process.env.STRIPE_SECRET_KEY);
  const chunks=[];
  for await(const chunk of req) chunks.push(chunk);
  const raw=Buffer.concat(chunks);
  let event;
  try{event=stripe.webhooks.constructEvent(raw,req.headers["stripe-signature"],process.env.STRIPE_WEBHOOK_SECRET)}
  catch(e){return res.status(400).json({error:"Invalid Stripe signature"})}
  // Persist this event in billing_events using Supabase/Postgres in production.
  return res.status(200).json({received:true,type:event.type});
}