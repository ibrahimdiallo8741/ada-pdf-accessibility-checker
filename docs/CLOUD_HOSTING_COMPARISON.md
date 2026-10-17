# Cloud Hosting Comparison & Provider Trade-Off Analysis

This document provides an objective, multi-vendor architectural assessment for hosting the ADA PDF Accessibility Checker container backend (`web/app.py` and `core/checker.py`) under free-tier constraints (<1,000 requests/month, 25 MB PDF payload support, native C PyMuPDF binaries).

---

## 1. Architectural Comparison Matrix

| Provider & Platform | Cost Model & Free Allowance | Compute Specs | Egress / Bandwidth Limits | Cold Start & Latency | Maintenance Overhead | Key Risk / Friction Point |
|---|---|---|---|---|---|---|
| **Oracle Cloud (OCI)<br>Always Free VPS** | **Forever Free**<br>(No expiration) | **Up to 4 OCPUs, 24 GB RAM** (Ampere A1 ARM) or **1/8 OCPU, 1 GB RAM** (AMD x86) | **10 TB / month** free outbound | **0s (Always running)** | **High**<br>(Linux OS patches, Docker, iptables, systemd) | **Idle Reclamation:** Halted if CPU/RAM < 20% for 7 days. "Out of capacity" signup blocks. |
| **Google Cloud Run** | **Always Free Tier**<br>(Monthly refresh) | 1–4 vCPU, 512 MB–8 GB RAM (Dynamically allocated per request) | **1 GB / month** free egress to North America; then **$0.12 / GB** | **1–3s** from scale-to-zero | **Zero**<br>(Fully managed container serverless) | **Egress Trap:** 1 GB free egress is tiny; large PDF testing can quietly trigger billing. |
| **AWS Lambda + API Gateway** | **Always Free Tier**<br>(Monthly refresh) | Up to 10 GB RAM, vCPU proportional to RAM | 100 GB / month free egress | **1–4s** container cold start | **Low**<br>(Requires ASGI adapter like Mangum) | **Payload Limit:** API Gateway hard-caps request payloads at **10 MB** (breaks 25 MB PDF requirement). |
| **AWS App Runner** | **No Forever Free Tier** | 1 vCPU, 2 GB RAM minimum | Standard AWS egress rates | 0s or paused | Low | **Billing:** Only 12-month trial; minimum ~$5/month idle memory fee. |
| **Azure Container Apps** | **Always Free Tier**<br>(Monthly refresh) | 180k vCPU-s, 360k GiB-s, 2M requests / month | 15 GB / month free outbound | **4–10s** from scale-to-zero | **Low**<br>(Fully managed Kubernetes/KEDA) | **Registry Cost:** Azure Container Registry (ACR) has no free tier (~$5/mo); must pull from GitHub GHCR. |
| **Cloudflare Workers** | **Always Free Tier**<br>(100k requests/day) | V8 / Pyodide WASM sandbox | **Unlimited** bandwidth (zero egress fees) | **< 5ms** (Near zero) | **Zero** | **C-Extension Blocker:** Cannot execute native compiled C wheels (`pymupdf`). |
| **Render Web Service** | **Always Free Tier**<br>(750 hours/month) | 0.1 CPU, 512 MB RAM | 100 GB / month bandwidth | **50+ seconds** spinning up from idle sleep | **Zero**<br>(Git push to deploy) | **Aggressive Sleep:** Spins down after 15 min idle; evaluators experience 50s timeouts. |

---

## 2. In-Depth Vendor Nuance & Trade-Offs

### 2.1 Oracle Cloud Infrastructure (OCI) Always Free VPS
* **Where It Dominates:**
  - **Raw Compute & RAM:** The Ampere A1 shape (4 OCPUs / 24 GB RAM) is by far the most generous free compute in the cloud industry ([Oracle Compute Shapes](https://docs.oracle.com/iaas/Content/Compute/References/computeshapes.htm#arm)).
  - **Bandwidth:** 10 TB/month free egress means you can upload/download 25 MB PDFs thousands of times without paying bandwidth fees ([OCI Data Transfer Pricing](https://www.oracle.com/cloud/networking/pricing/)).
  - **Zero Cold Starts:** Because it is a persistent VM, background processing and web responses are instant.
* **Where It Hurts:**
  - **Reclamation Reaper:** [Oracle's Idle Instance Policy](https://docs.oracle.com/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm#compute__idleinstances) monitors instances. If CPU, network, and RAM (for A1) stay under 20% for 7 consecutive days, Oracle halts the VM.
  - **Out of Capacity:** The A1 ARM shapes are often fully booked in major regions (Ashburn, Phoenix, Frankfurt), forcing fallback to the small 1 GB AMD shape (`VM.Standard.E2.1.Micro`).
  - **Operational Burden:** You must manage Linux OS updates, Docker restart policies, and OS firewalls yourself.

---

### 2.2 Google Cloud Run
* **Where It Dominates:**
  - **Pure Developer Velocity:** Point Cloud Run to your `Dockerfile` and it handles routing, SSL, autoscaling, and zero-maintenance container lifecycle ([Cloud Run Free Tier](https://cloud.google.com/run/pricing#free-tier)).
  - **Scale-to-Zero:** When nobody is testing the student prototype, 0 instances are running. It will never be terminated or flagged for being idle.
* **Where It Hurts:**
  - **The Egress Trap:** Google's free tier only gives **1 GB of egress per month** ([Google Cloud Free Tier Limits](https://cloud.google.com/free/docs/free-cloud-features#cloud-run)). If an evaluator repeatedly downloads 20 MB scanned PDFs or large JSON accessibility reports, you will quickly blow past 1 GB and be billed $0.12/GB.
  - **Cold Starts:** When cold, taking 2 to 4 seconds to spin up Python 3.13 and load PyMuPDF C libraries can make the initial page load feel sluggish.

---

### 2.3 Amazon Web Services (AWS)
* **The AWS Friction Points:**
  - **No True Serverless Container Free Tier:** AWS App Runner has no perpetual free tier. AWS Fargate has no perpetual free tier.
  - **EC2 `t2.micro` is a 12-Month Trap:** EC2 micro instances are only free for the **first 12 months** of a new AWS account, after which they bill ~$9/month ([AWS Free Tier Types](https://aws.amazon.com/free/)).
  - **AWS Lambda 6 MB Limit:** While Lambda has a generous permanent free tier (1M requests/mo), AWS Lambda synchronous invocations have a hard payload limit of **6 MB**, and API Gateway has a **10 MB limit** ([AWS Lambda Quotas](https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html)). This directly violates project requirement **REQ-02** (supporting up to 25 MB PDF files).

---

### 2.4 Microsoft Azure
* **Azure Container Apps:**
  - Offers a generous permanent free tier (2 million requests and 360,000 GiB-seconds per month) scaling to zero ([Azure Container Apps Pricing](https://azure.microsoft.com/en-us/pricing/details/container-apps/)).
  - **Friction Point:** Azure Container Registry (ACR) charges ~$5/month with no free tier. To keep it 100% free, you must push Docker containers to GitHub Packages (GHCR) or Docker Hub and authenticate Azure to the external registry.
* **Azure App Service (F1 Tier):**
  - Caps CPU execution at **60 minutes per day** across the entire app ([App Service Limits](https://learn.microsoft.com/en-us/azure/azure-resource-manager/management/azure-subscription-service-limits#app-service-limits)). Unusable for ongoing evaluation.

---

### 2.5 Cloudflare + Edge Platforms
* **Why Edge Workers Cannot Run Backend Alone:**
  - Cloudflare Workers Python runs in **Pyodide (WebAssembly)** ([Cloudflare Python Workers](https://developers.cloudflare.com/workers/languages/python/)). Pyodide cannot load compiled C shared libraries (`.so` files) that haven't been ported to Emscripten. PyMuPDF bundles native MuPDF C code and cannot run on Workers.
* **The Sweet Spot (Hybrid):**
  - Using **Cloudflare at the Edge** (DNS, SSL, CDN caching, DDoS protection, Cloudflare Tunnel) combined with compute behind it gives you **unlimited edge bandwidth and zero egress fees**, neutralizing the egress limitations of cloud hosts.

---

## 3. Technical Recommendation for this Project

1. **If Priority is Maximum Free Resources (RAM/Bandwidth) & Zero Cold Starts:**
   - **Oracle Cloud Always Free VPS (AMD or ARM)** + **Cloudflare Tunnel (`cloudflared`)**.
   - *Requirement:* Run a small cron keep-alive to avoid the 7-day idle reclamation rule, or use a "Pay-As-You-Go" upgraded account status (which remains free within tier limits and officially exempts instances from idle reclamation).
2. **If Priority is Zero Maintenance, No Linux Sysadmin, & No Idle Deletion:**
   - **Google Cloud Run** or **Azure Container Apps** fronted by **Cloudflare Free CDN**.
   - *Requirement:* Put Cloudflare in front as a proxy/cache so large static assets and reports don't exhaust Cloud Run's 1 GB monthly egress allowance.
