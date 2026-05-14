# bb-recon — Reconnaissance Methodology

Full recon playbook: what to run, in what order, and how to feed results into bb-huge.

> Referenced by: `bb-orchestrator.md`, `bb-operator.md`
> Mentions: `bb-eligible-vulnerabilities.md` (what to look for in recon output)

---

## Recon Philosophy

Recon is not just enumeration — it's building a mental model of the target.
The goal is to find **attack surface that others missed**, not to run the same
tools as everyone else on the same scope.

Log everything into bb-huge as you go. A recon note today becomes
a confirmed finding next week.

---

## Phase 1 — Passive Recon (no direct interaction)

### Subdomain Discovery
```bash
# Certificate transparency
curl "https://crt.sh/?q=%.example.com&output=json" | jq '.[].name_value' | sort -u

# DNS brute force
subfinder -d example.com -all -recursive -o subs.txt
amass enum -passive -d example.com -o amass_subs.txt

# Combine and deduplicate
cat subs.txt amass_subs.txt | sort -u > all_subs.txt
```

### Historical URLs & Parameters
```bash
# Wayback Machine
waybackurls example.com | sort -u > wayback_urls.txt
gau example.com --o gau_urls.txt

# Extract parameters
cat wayback_urls.txt gau_urls.txt | grep "?" | sort -u > params.txt
```

### GitHub / Code Recon
```bash
# Search for secrets, endpoints, credentials
# Queries to use on GitHub:
# org:targetcompany password
# org:targetcompany api_key
# org:targetcompany "example.com" filename:.env
# "example.com" extension:js
```

### ASN / IP Range Discovery
```bash
# Find IP ranges owned by the company
curl "https://api.bgpview.io/search?query_term=TargetCompany" | jq '.data.asns'
# Then enumerate IPs in those ranges
```

---

## Phase 2 — Active Recon

### HTTP Probing (resolve which subdomains are alive)
```bash
cat all_subs.txt | httpx -silent -status-code -title -tech-detect -o live_hosts.txt
```

### Port Scanning (if in scope)
```bash
nmap -iL live_hosts.txt -p 80,443,8080,8443,8888,3000,4000,5000,9000 --open -oN ports.txt
# Full port scan on interesting hosts:
nmap -sV -sC -p- <target_ip> -oN full_scan.txt
```

### Technology Fingerprinting
```bash
# Wappalyzer CLI or whatweb
whatweb -i live_hosts.txt -a 3 --log-brief=tech.txt

# Check response headers manually for:
# X-Powered-By, Server, X-Framework, X-Generator
# Set-Cookie names (JSESSIONID=Java, PHPSESSID=PHP, etc.)
```

### JavaScript Analysis
```bash
# Extract JS files
cat live_hosts.txt | getJS --complete > js_files.txt

# Extract endpoints and secrets from JS
cat js_files.txt | xargs -I{} bash -c 'curl -s {} | grep -oE "(api|endpoint|path)[\"'\'']\s*:\s*[\"'\''][^\"'\'']+[\"'\'']"'

# Secrets scanner
trufflehog filesystem ./downloaded_js/ --only-verified
```

### Directory & Endpoint Discovery
```bash
# Wordlist-based discovery
ffuf -u https://example.com/FUZZ -w /usr/share/seclists/Discovery/Web-Content/raft-large-words.txt \
  -mc 200,301,302,403 -o dirs.json

# API endpoint discovery
ffuf -u https://api.example.com/v1/FUZZ -w /usr/share/seclists/Discovery/Web-Content/api/api-endpoints.txt \
  -H "Authorization: Bearer <your_token>" -mc 200,201,401,403

# Parameter discovery
arjun -u https://example.com/endpoint -oJ params.json
```

---

## Phase 3 — Authentication Surface Mapping

For each auth endpoint, note:
- Login mechanism (password, OTP, SSO, OAuth, magic link)
- Password reset flow — does it use email link? security questions? OTP?
- Registration — email verification required? username enumeration?
- OAuth providers — which? redirect_uri validation?
- MFA — TOTP? SMS? Can it be bypassed?
- Session management — cookie or JWT? expiry?

---

## Recon Output → bb-huge

Create one finding per major recon category:

```json
{
  "title": "Recon: <target> — Attack Surface Map",
  "target": "<target>",
  "severity": "informational",
  "status": "debugging",
  "agent": "<your-agent>",
  "description": "## Subdomains Found\n<list>\n\n## Live Hosts\n<list>\n\n## Technologies\n<list>\n\n## Interesting Endpoints\n<list>\n\n## Auth Surface\n<list>"
}
```

Attach recon files:
```
bb_upload_attachment: subs.txt, live_hosts.txt, params.txt, js_files.txt
```

---

## Recon Red Flags → Immediate Action

When you see these in recon output, stop and test immediately:

| Signal | Action |
|--------|--------|
| `staging.`, `dev.`, `test.` subdomain | Check for relaxed security, debug endpoints |
| `admin.`, `dashboard.`, `internal.` | Check for exposed admin without auth |
| `api.` with swagger/openapi docs | Load docs, enumerate all endpoints |
| Port 8080/8443 open | Often dev server with no auth |
| `X-Powered-By: PHP/5.x` | Old version, check for known CVEs |
| `.git`, `.env`, `.DS_Store` accessible | Source code / credential exposure |
| AWS S3 bucket in subdomains | Check for public access / takeover |
| GitHub repos with company name | Code recon for secrets and endpoints |
| `debug=true` accepted | May expose stack traces, internal paths |

---

## Tools Quick Reference

| Tool | Purpose | Install |
|------|---------|---------|
| subfinder | Subdomain enumeration | `go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest` |
| amass | Subdomain + ASN enumeration | `go install github.com/owasp-amass/amass/v4/...@master` |
| httpx | HTTP probing | `go install github.com/projectdiscovery/httpx/cmd/httpx@latest` |
| ffuf | Directory/parameter fuzzing | `go install github.com/ffuf/ffuf/v2@latest` |
| nuclei | Template-based scanning | `go install github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest` |
| gau | Historical URLs | `go install github.com/lc/gau/v2/cmd/gau@latest` |
| waybackurls | Wayback Machine URLs | `go install github.com/tomnomnom/waybackurls@latest` |
| arjun | Parameter discovery | `pip install arjun` |
| getJS | JavaScript file discovery | `npm i -g getjs` |
| trufflehog | Secret scanning | `brew install trufflehog` |
| interactsh | OOB interaction server | `go install github.com/projectdiscovery/interactsh/cmd/interactsh-client@latest` |
