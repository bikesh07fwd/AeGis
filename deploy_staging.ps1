param (
    [string]$ProjectId,
    [string]$Region = "us-central1"
)

if (-not $ProjectId) {
    Write-Error "Please provide a ProjectId: .\deploy_staging.ps1 -ProjectId 'my-project'"
    exit 1
}

$ImageTag = "$Region-docker.pkg.dev/$ProjectId/aegis-staging/aegis:latest"

Write-Host "Building Docker Image..."
docker build -t $ImageTag .

Write-Host "Pushing to Artifact Registry..."
# Assumes gcloud auth configure-docker $Region-docker.pkg.dev has been run
docker push $ImageTag

Write-Host "Deploying Migration Job to Cloud Run..."
gcloud run jobs deploy aegis-migration-staging `
    --image $ImageTag `
    --region $Region `
    --project $ProjectId `
    --service-account "aegis-cloudrun-sa@$ProjectId.iam.gserviceaccount.com" `
    --command "python" `
    --args "database/migration.py" `
    --set-env-vars "ENVIRONMENT=production,GCP_PROJECT_ID=$ProjectId,DATABASE_URL_SECRET_NAME=DATABASE_URL_staging"

Write-Host "Running Migration Job..."
gcloud run jobs execute aegis-migration-staging --region $Region --project $ProjectId --wait

Write-Host "Updating Cloud Run Service (Applying Terraform output indirectly, or forcing a new revision)..."
gcloud run services update aegis-api-staging `
    --image $ImageTag `
    --region $Region `
    --project $ProjectId

Write-Host "Deployment Complete."
