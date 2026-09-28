export default function handler(req,res){
  res.status(200).json({
    service:"UNX2",
    version:"0.1.0",
    layer:"LÉVIATHAN CORE",
    status:"operational",
    mode:process.env.OPENAI_API_KEY||process.env.ANTHROPIC_API_KEY||process.env.GOOGLE_GENERATIVE_AI_API_KEY?"connected":"demo",
    timestamp:new Date().toISOString()
  });
}