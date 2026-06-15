---
name: deploy-to-azure
description: 'Deploy a containerized application to Azure App Service with UHG enterprise policy compliance (HTTPS-only, VNet integration, NAT Gateway, route-all). USE FOR: deploying to Azure cloud, Azure App Service, container deployment, ACR build, Azure VNet setup, Azure subscription deployment. Trigger phrases: "deploy to Azure", "Azure deployment", "push to Azure", "Azure cloud", "Azure App Service", "deploy container Azure".'
argument-hint: '<subscription-id> <sp-client-id> <sp-secret>'
---

# Deploy to Azure (UHG Enterprise)

Deploy a containerized app to Azure App Service with full UHG policy compliance.

## UHG Tenant ID (constant)

```
db05faca-c82a-4b9d-b9c5-0f64b6755421
```

This is the same across all UHG subscriptions. Never ask the user for it.

## Required inputs from user

| Input | Example |
|-------|---------||
| Subscription ID | `2cafef01-f9aa-401c-a276-2d03d894c44e` |
| Service Principal Client ID | `1a7e11ff-...` |
| Service Principal Secret | `un68Q~...` |

## Derived defaults (override if user specifies)

| Setting | Default |
|---------|---------|
| Region | `centralus` |
| Resource Group | `rg-<app-name>` |
| ACR Name | `acr<app-name-no-hyphens>` |
| App Service Plan | `asp-<app-name>` (B2 Linux) |
| VNet / Subnet | `vnet-<app>` / `snet-webapp` |
| NAT Gateway | `nat-<app>` + `pip-<app>-nat` |

## Execution checklist

### 1. Prerequisites check
```bash
az --version   # need ≥ 2.50
docker --version || podman --version
```

### 2. Azure login
```bash
az login --service-principal -u "$SP_CLIENT_ID" -p "$SP_SECRET" --tenant "db05faca-c82a-4b9d-b9c5-0f64b6755421"
az account set --subscription "$SUBSCRIPTION_ID"
```

### 3. Build app locally
```bash
npm install
npm run build --workspace=apps/frontend
npm run build --workspace=apps/backend
```

### 4. Create Azure resources (centralus — UHG allowed region)
```bash
# Resource Group
az group create --name rg-$APP --location centralus

# Container Registry
az acr create --name acr$APP --resource-group rg-$APP --sku Basic --admin-enabled true --location centralus

# VNet + Subnet (delegated to App Service)
az network vnet create --name vnet-$APP --resource-group rg-$APP --location centralus --address-prefix 10.0.0.0/16 --subnet-name snet-webapp --subnet-prefix 10.0.1.0/24
az network vnet subnet update --name snet-webapp --resource-group rg-$APP --vnet-name vnet-$APP --delegations Microsoft.Web/serverFarms

# NAT Gateway (required for outbound internet through VNet)
az network public-ip create --name pip-$APP-nat --resource-group rg-$APP --location centralus --sku Standard --allocation-method Static
az network nat gateway create --name nat-$APP --resource-group rg-$APP --location centralus --public-ip-addresses pip-$APP-nat
az network vnet subnet update --name snet-webapp --resource-group rg-$APP --vnet-name vnet-$APP --nat-gateway nat-$APP

# App Service Plan (B2 Linux — enough for Playwright)
az appservice plan create --name asp-$APP --resource-group rg-$APP --location centralus --sku B2 --is-linux
```

### 5. Build & push image via ACR Build
```bash
az acr build --registry acr$APP --image $APP:latest --file Dockerfile.azure --platform linux/amd64 .
```

**Key Dockerfile requirements:**
- Override `.npmrc` to use public npm registry: `echo "registry=https://registry.npmjs.org/" > .npmrc`
- Fix lockfile private registry URLs: `sed -i 's|private-registry-url|https://registry.npmjs.org/|g' package-lock.json`
- `.dockerignore` must allow `!apps/backend/dist` and `!apps/frontend/dist`

### 6. Deploy via ARM template

Use ARM template because `az webapp create` cannot set `vnetRouteAllEnabled` at creation time, which UHG policy requires.

```json
{
  "type": "Microsoft.Web/sites",
  "properties": {
    "httpsOnly": true,
    "virtualNetworkSubnetId": "<subnet-resource-id>",
    "vnetRouteAllEnabled": true,
    "siteConfig": {
      "linuxFxVersion": "DOCKER|<acr>.azurecr.io/<image>:latest",
      "vnetRouteAllEnabled": true,
      "alwaysOn": true,
      "appSettings": [
        { "name": "WEBSITES_PORT", "value": "8080" },
        { "name": "DOCKER_REGISTRY_SERVER_URL", "value": "https://<acr>.azurecr.io" },
        { "name": "DOCKER_REGISTRY_SERVER_USERNAME", "value": "<acr>" },
        { "name": "DOCKER_REGISTRY_SERVER_PASSWORD", "value": "<password>" }
      ]
    }
  }
}
```

Deploy:
```bash
ACR_PASSWORD=$(az acr credential show --name acr$APP --query 'passwords[0].value' -o tsv)
az deployment group create --resource-group rg-$APP --template-file azure-deploy.json --parameters acrPassword="$ACR_PASSWORD"
```

### 7. Post-deploy config
```bash
az webapp config set --name $APP --resource-group rg-$APP --web-sockets-enabled true
az webapp restart --name $APP --resource-group rg-$APP
```

### 8. Verify
```bash
curl -s -o /dev/null -w "HTTP %{http_code}" https://$APP.azurewebsites.net/
curl -s -o /dev/null -w "HTTP %{http_code}" https://$APP.azurewebsites.net/api/sessions
```

## UHG policy gotchas

| Policy | Requirement | Solution |
|--------|-------------|----------|
| `pcam-enabled-regions` | Only `centralus` allowed | Use `--location centralus` everywhere |
| `appservicewebappsredirecthttps-v1` | HTTPS required | `httpsOnly: true` in ARM template |
| `appserviceappsshouldenable1918traffictovnet-v1` | VNet + route-all | ARM template with `vnetRouteAllEnabled: true` + subnet ID |
| `containerinstancegroupsshoulddeployintovnet-v1` | ACI must use VNet | Use App Service instead of ACI |
| VNet outbound failure | No internet from VNet | NAT Gateway on the subnet |

## Cleanup
```bash
az group delete --name rg-$APP --yes --no-wait
```
