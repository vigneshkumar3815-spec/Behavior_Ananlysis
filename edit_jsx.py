import re

with open("d:/HackNex/SentinelVision/src/App.jsx", "r", encoding="utf-8") as f:
    code = f.read()

# State injection
state_code = """
  const [hasSource, setHasSource] = useState(false);
  
  // Gemini States
  const [customRule, setCustomRule] = useState("");
  const [geminiApiKey, setGeminiApiKey] = useState("");
  const [ruleLoading, setRuleLoading] = useState(false);

  const applyCustomRule = async () => {
    setRuleLoading(true);
    try {
      await fetch("http://localhost:8002/api/custom_rule", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ rule: customRule, api_key: geminiApiKey })
      });
    } catch(e) { console.error(e); }
    setRuleLoading(false);
  };
"""
code = code.replace("  const [hasSource, setHasSource] = useState(false);", state_code)

# Sidebar injection
sidebar_injection = """            <div ref={logsEndRef} />
          </div>
          
          {/* Custom Rule UI */}
          <div className="p-4 border-t border-slate-800 bg-slate-950 flex flex-col gap-3">
             <h3 className="text-sm font-bold text-slate-300">Zero-Shot AI Anomaly Rule</h3>
             <input type="text" placeholder="e.g. looking at a phone" className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white" value={customRule} onChange={e => setCustomRule(e.target.value)} />
             <input type="password" placeholder="Gemini API Key (optional if env set)" className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white" value={geminiApiKey} onChange={e => setGeminiApiKey(e.target.value)} />
             <button onClick={applyCustomRule} className="w-full bg-purple-600 hover:bg-purple-500 text-white font-semibold py-2 rounded-lg text-sm transition-colors cursor-pointer">
               {ruleLoading ? "Applying..." : "Activate AI Vision"}
             </button>
          </div>
        </div>
      </main>"""
code = code.replace("            <div ref={logsEndRef} />\n          </div>\n        </div>\n      </main>", sidebar_injection)

# Add custom alert colors
color_inject = """    if (type.includes("NORMAL") || type.includes("RECOVER")) return "bg-green-500/10 border-green-500/30 text-green-400";
    if (type.includes("CUSTOM_ALERT")) return "bg-purple-500/10 border-purple-500/30 text-purple-400";"""
code = code.replace("    if (type.includes(\"NORMAL\") || type.includes(\"RECOVER\")) return \"bg-green-500/10 border-green-500/30 text-green-400\";", color_inject)

with open("d:/HackNex/SentinelVision/src/App.jsx", "w", encoding="utf-8") as f:
    f.write(code)
print("Done editing App.jsx")
