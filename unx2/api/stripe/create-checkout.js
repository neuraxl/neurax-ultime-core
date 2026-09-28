import Stripe from "stripe";
import{requireOrgMember,supabaseFetch}from"../_lib/supabase.js";
export default async function handler(req,res){
  if(req.method!=="POST")return res.status(405).json({error:"Method not allowed"});
  try{
    const{organizationId}=req.body||{}; const{user}=await requireOrgMember(req,organizationId);
    if(!process.env.STRIPE_SECRET_KEY||!process.env.STRIPE_PRICE_ID)return res.status(503).json({error:"Stripe is not configured"});
    const stripe=new Stripe(process.env.STRIPE_SECRET_KEY);
    const session=await stripe.checkout.sessions.create({
      mode:"subscription",customer_email:user.email,client_reference_id:organizationId,
      line_items:[{price:process.env.STRIPE_PRICE_ID,quantity:1}],
      metadata:{organization_id:organizationId,user_id:user.id},
      subscription_data:{metadata:{organization_id:organizationId,user_id:user.id}},
      success_url:(process.env.APP_URL||"")+"/?billing=success",cancel_url:(process.env.APP_URL||"")+"/?billing=cancel"
    });
    await supabaseFetch("telemetry_events",{method:"POST",body:{organization_id:organizationId,event_type:"billing.checkout.created",agent_name:"Stripe",status:"success",payload:{checkout_session_id:session.id}}});
    return res.status(200).json({url:session.url,id:session.id});
  }catch(e){return res.status(/Unauthorized|Forbidden/.test(e.message)?401:500).json({error:e.message})}
}
