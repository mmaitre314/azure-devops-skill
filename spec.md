Create an AI skill to connect to Azure Dev Ops (ADO). Enable things like downloading files from repos, querying diffs from Pull Requests, reading wikis, reading work items, etc. Limit to read-only operations. Do not allow making changes to ADO.

Use the ADO documentation at https://learn.microsoft.com/en-us/rest/api/azure/devops/?view=azure-devops-rest-7.2 to get a list of available operations and their syntax. Also review the list of MCP tools for ADO at https://github.com/microsoft/azure-devops-mcp/blob/main/docs/TOOLSET.md for an (incomplete) list of operations. 

The list of operations is fairly long, so organize the skill in a way that optimizes future AI agent performance and does not unnecessarily pollute agent context.

Use Python as coding language.

Use Azure CLI for authentication. For instance Az CLI allows calling ADO like this:
```bash
az login
az rest --method post --uri "https://vssps.dev.azure.com/{org}/_apis/Tokens/Pats?api-version=6.1-preview" --resource "https://management.core.windows.net/" --body '{"displayName": "DevContainer", "scope": "vso.packaging"}' --headers Content-Type=application/json --query patToken.token --output tsv
```

When writing Python, consider using the `azure-identity` package (`DefaultAzureCredential`, `AzureCliCredential`) instead of running Az CLI directly. Note that it does not cache the access tokens from Az CLI, so consider adding a cache where useful to speed things up.

Authenticate with ADO using Entra/OAuth. Do not use PATs.

Also consider using the `azure-devops-python-api` Python package if helpful. Its documentation is at https://github.com/Microsoft/azure-devops-python-api