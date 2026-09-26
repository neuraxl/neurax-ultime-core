export default function handler(req,res){
 if(req.method!=='GET') return res.status(405).json({error:'GET requis'});
 res.status(200).json({supabaseUrl:process.env.SUPABASE_URL||'',supabasePublishableKey:process.env.SUPABASE_PUBLISHABLE_KEY||process.env.SUPABASE_ANON_KEY||''});
}