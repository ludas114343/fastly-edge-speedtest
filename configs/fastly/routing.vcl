# Fastly Anycast Global Fronting Architecture (Version 16)
# Service: 8K5HGyXmr8P6XuzRc5UPk0 (ruoyemu.global.ssl.fastly.net)
# Fronting Role: Anycast Inbound Termination -> Real Backend Routing (Netlify / Supabase / Wasmer)

# 1. If subscription requested: route to Netlify real backend
if (req.url ~ "^/clash" || req.url ~ "^/sub") {
    set req.backend = F_backend_netlify;
    set req.http.Host = "gateway-core-net.netlify.app";
    return (pass);
}

# 2. If not websocket: deliver synthetic authentic Nginx disguise page
if (req.http.Upgrade !~ "(?i)websocket") {
    error 700 "Nginx Camouflage";
}

# 3. WebSocket proxy routing by regional path and real backends
if (req.url ~ "^/net" || req.url ~ "(?i)backend=netlify") {
    set req.backend = F_backend_netlify;
    set req.http.Host = "gateway-core-net.netlify.app";
} else if (req.url ~ "^/wasmer" || req.url ~ "^/w-la" || req.url ~ "(?i)backend=wasmer") {
    set req.backend = F_backend_wasmer;
    set req.http.Host = "edgetunnel-us-la.wasmer.app";
} else if (req.url ~ "^/de" || req.url ~ "(?i)country=de") {
    set req.url = "/functions/v1/edgetunnel?forceFunctionRegion=eu-central-1";
    set req.backend = F_backend_sb2;
    set req.http.Host = "gwgiogtgdyrqlexcdjqm.supabase.co";
} else if (req.url ~ "^/fr" || req.url ~ "(?i)country=fr") {
    set req.url = "/functions/v1/edgetunnel?forceFunctionRegion=eu-west-3";
    set req.backend = F_backend_sb2;
    set req.http.Host = "gwgiogtgdyrqlexcdjqm.supabase.co";
} else if (req.url ~ "^/uk" || req.url ~ "^/gb" || req.url ~ "(?i)country=gb") {
    set req.url = "/functions/v1/edgetunnel?forceFunctionRegion=eu-west-2";
    set req.backend = F_backend_sb1;
    set req.http.Host = "theecyezvuzkflwikxwr.supabase.co";
} else if (req.url ~ "^/ch" || req.url ~ "(?i)country=ch") {
    set req.url = "/functions/v1/edgetunnel?forceFunctionRegion=eu-central-2";
    set req.backend = F_backend_sb1;
    set req.http.Host = "theecyezvuzkflwikxwr.supabase.co";
} else if (req.url ~ "^/ie" || req.url ~ "(?i)country=ie") {
    set req.url = "/functions/v1/edgetunnel?forceFunctionRegion=eu-west-1";
    set req.backend = F_backend_sb1;
    set req.http.Host = "theecyezvuzkflwikxwr.supabase.co";
} else if (req.url ~ "^/jp" || req.url ~ "(?i)country=jp") {
    set req.url = "/functions/v1/edgetunnel?forceFunctionRegion=ap-northeast-1";
    set req.backend = F_backend_sb2;
    set req.http.Host = "gwgiogtgdyrqlexcdjqm.supabase.co";
} else if (req.url ~ "^/kr" || req.url ~ "(?i)country=kr") {
    set req.url = "/functions/v1/edgetunnel?forceFunctionRegion=ap-northeast-2";
    set req.backend = F_backend_sb2;
    set req.http.Host = "gwgiogtgdyrqlexcdjqm.supabase.co";
} else if (req.url ~ "^/sg" || req.url ~ "(?i)country=sg") {
    set req.url = "/functions/v1/edgetunnel?forceFunctionRegion=ap-southeast-1";
    set req.backend = F_backend_sb1;
    set req.http.Host = "theecyezvuzkflwikxwr.supabase.co";
} else if (req.url ~ "^/au" || req.url ~ "(?i)country=au") {
    set req.url = "/functions/v1/edgetunnel?forceFunctionRegion=ap-southeast-2";
    set req.backend = F_backend_sb2;
    set req.http.Host = "gwgiogtgdyrqlexcdjqm.supabase.co";
} else if (req.url ~ "^/ca" || req.url ~ "(?i)country=ca") {
    set req.url = "/functions/v1/edgetunnel?forceFunctionRegion=ca-central-1";
    set req.backend = F_backend_sb2;
    set req.http.Host = "gwgiogtgdyrqlexcdjqm.supabase.co";
} else if (req.url ~ "^/usw" || req.url ~ "(?i)country=usw") {
    set req.url = "/functions/v1/edgetunnel?forceFunctionRegion=us-west-1";
    set req.backend = F_backend_sb2;
    set req.http.Host = "gwgiogtgdyrqlexcdjqm.supabase.co";
} else {
    set req.url = "/functions/v1/edgetunnel?forceFunctionRegion=us-east-1";
    set req.backend = F_backend_sb1;
    set req.http.Host = "theecyezvuzkflwikxwr.supabase.co";
}

return (pass);
