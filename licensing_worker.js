export default {
  async fetch(request, env, ctx) {
    // Enable CORS for frontend/client requests
    const corsHeaders = {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET, HEAD, POST, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type",
    };

    if (request.method === "OPTIONS") {
      return new Response(null, { headers: corsHeaders });
    }

    const url = new URL(request.url);
    
    // Activation endpoint
    if (url.pathname === "/activate" && request.method === "POST") {
      try {
        const { regkey, authkey } = await request.json();
        if (!regkey || !authkey) {
          return new Response(JSON.stringify({ success: false, error: "Missing regkey or authkey." }), {
            status: 400,
            headers: { ...corsHeaders, "Content-Type": "application/json" }
          });
        }

        const normalizedRegKey = regkey.trim().toUpperCase();
        const db = env.DB || env.xenohead_data;
        if (!db) {
          return new Response(JSON.stringify({ success: false, error: "Database binding DB or xenohead_data not found." }), {
            status: 500,
            headers: { ...corsHeaders, "Content-Type": "application/json" }
          });
        }

        // Find key in database
        const { results } = await db.prepare("SELECT * FROM XenoScript WHERE Regkey = ?").bind(normalizedRegKey).all();
        
        if (!results || results.length === 0) {
          return new Response(JSON.stringify({ success: false, error: "Registration key not found in D1 database." }), {
            status: 404,
            headers: { ...corsHeaders, "Content-Type": "application/json" }
          });
        }

        const row = results[0];
        if (row.Active !== 'y' && row.Active !== 'Y') {
          return new Response(JSON.stringify({ success: false, error: "This registration key is inactive." }), {
            status: 403,
            headers: { ...corsHeaders, "Content-Type": "application/json" }
          });
        }

        // If Authkey is already set, verify it matches
        if (row.Authkey && row.Authkey.trim() !== "") {
          if (row.Authkey === authkey) {
            return new Response(JSON.stringify({ 
              success: true, 
              message: "License is active on this device.",
              regname: row.RegName,
              regemail: row.RegEmail,
              dateregistered: row.DateRegistered
            }), {
              status: 200,
              headers: { ...corsHeaders, "Content-Type": "application/json" }
            });
          } else {
            return new Response(JSON.stringify({ success: false, error: "This key is already activated on another machine." }), {
              status: 400,
              headers: { ...corsHeaders, "Content-Type": "application/json" }
            });
          }
        }

        // If not set, bind it to this machine
        const dateNow = new Date().toISOString().slice(0, 19).replace('T', ' ');
        await db.prepare("UPDATE XenoScript SET Authkey = ?, DateRegistered = ? WHERE Regkey = ?")
          .bind(authkey, dateNow, normalizedRegKey)
          .run();

        return new Response(JSON.stringify({ 
          success: true, 
          message: "Activation successful! thank you for registering.",
          regname: row.RegName,
          regemail: row.RegEmail,
          dateregistered: dateNow
        }), {
          status: 200,
          headers: { ...corsHeaders, "Content-Type": "application/json" }
        });

      } catch (err) {
        return new Response(JSON.stringify({ success: false, error: err.message }), {
          status: 500,
          headers: { ...corsHeaders, "Content-Type": "application/json" }
        });
      }
    }

    return new Response("Not Found", { status: 404 });
  }
};
