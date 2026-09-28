import Stripe from "stripe";
import{adminRest}from"./_lib/supabase.js";
export const config={api:{bodyParser:false}};
function isoFromUnix(v){return v?new Date(v*1000).toISOString():null}
export default async function handler(req,res){
  if(req.method!=="POST")return res.status(405).end();
  if(!process.env.STRIPE_SECRET_KEY||!process.env.STRIPE_WEBHOOK_SECRET)return res.status(503).json({error:"Stripe is not configured"});
  const stripe=new Stripe(process.env.STRIPE_SECRET_KEY),chunks=[];for await(const chunk of req)chunks.push(chunk);
  let event;try{event=stripe.webhooks.constructEvent(Buffer.concat(chunks),req.headers["stripe-signature"],process.env.STRIPE_WEBHOOK_SECRET)}catch{return res.status(400).json({error:"Invalid Stripe signature"})}
  const object=event.data.object||{},metadata=object.metadata||{},organizationId=metadata.organization_id||object.client_reference_id||null;
  if(!organizationId)return res.status(200).json({received:true,type:event.type,ignored:"missing organization_id"});
  const existing=await adminRest("billing_events?provider=eq.stripe&external_id=eq."+encodeURIComponent(event.id)+"&select=id");
  if(existing.length)return res.status(200).json({received:true,duplicate:true});
  await adminRest("billing_events",{method:"POST",body:{organization_id:organizationId,provider:"stripe",external_id:event.id,event_type:event.type,payload:event}});
  if(event.type==="checkout.session.completed"){
    const subscriptionId=typeof object.subscription==="string"?object.subscription:null,customerId=typeof object.customer==="string"?object.customer:null;
    const current=await adminRest("subscriptions?organization_id=eq."+encodeURIComponent(organizationId)+"&select=id");
    const row={stripe_customer_id:customerId,stripe_subscription_id:subscriptionId,status:"active",updated_at:new Date().toISOString()};
    if(current.length)await adminRest("subscriptions?organization_id=eq."+encodeURIComponent(organizationId),{method:"PATCH",body:row});
    else await adminRest("subscriptions",{method:"POST",body:{organization_id:organizationId,...row}});
  }
  if(["customer.subscription.created","customer.subscription.updated","customer.subscription.deleted"].includes(event.type)){
    const row={stripe_customer_id:typeof object.customer==="string"?object.customer:null,stripe_subscription_id:object.id,
      stripe_price_id:object.items?.data?.[0]?.price?.id||null,status:object.status||"inactive",
      current_period_end:isoFromUnix(object.current_period_end),cancel_at_period_end:!!object.cancel_at_period_end,updated_at:new Date().toISOString()};
    const org=metadata.organization_id;
    if(org){
      const current=await adminRest("subscriptions?organization_id=eq."+encodeURIComponent(org)+"&select=id");
      if(current.length)await adminRest("subscriptions?organization_id=eq."+encodeURIComponent(org),{method:"PATCH",body:row});
      else await adminRest("subscriptions",{method:"POST",body:{organization_id:org,...row}});
    }
  }
  return res.status(200).json({received:true,type:event.type});
}
