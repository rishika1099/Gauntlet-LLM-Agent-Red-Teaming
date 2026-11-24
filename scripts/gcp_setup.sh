#!/usr/bin/env bash
# One-time Google Cloud setup, run by the repo owner (Shreya). Safe to re-run.
#   PROJECT_ID=gauntlet-xyz TEAM="rishika@columbia.edu kshamaa@columbia.edu" ./scripts/gcp_setup.sh
# Needs: gcloud logged in as the project owner, billing (course credits) linked to the project.
set -euo pipefail

PROJECT_ID="${PROJECT_ID:?set PROJECT_ID}"
REGION="${REGION:-us-central1}"
SERVICE="${SERVICE:-gauntlet}"
TEAM="${TEAM:-}"   # teammates' Google account emails, space-separated

gcloud config set project "$PROJECT_ID" >/dev/null
NUM=$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')
RUN_SA="${NUM}-compute@developer.gserviceaccount.com"   # Cloud Run's default runtime identity

echo "== 1. APIs"
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com \
  secretmanager.googleapis.com aiplatform.googleapis.com iam.googleapis.com

echo "== 2. Image repository (the name cloudbuild.yaml expects)"
gcloud artifacts repositories describe cloud-run-source-deploy --location "$REGION" >/dev/null 2>&1 || \
  gcloud artifacts repositories create cloud-run-source-deploy --repository-format=docker --location "$REGION"

echo "== 3. Secrets (prompted; nothing touches disk). Gemini needs no key: it uses Vertex AI."
for name in openai-api-key langfuse-public-key langfuse-secret-key; do
  if gcloud secrets describe "$name" >/dev/null 2>&1; then
    echo "   $name exists (new value: gcloud secrets versions add $name --data-file=-)"
  else
    read -r -s -p "   Value for $name: " value; echo
    printf '%s' "$value" | gcloud secrets create "$name" --data-file=- --replication-policy=automatic >/dev/null
  fi
done

echo "== 4. Runtime identity: call Gemini, read secrets"
gcloud projects add-iam-policy-binding "$PROJECT_ID" --member="serviceAccount:$RUN_SA" --role=roles/aiplatform.user --condition=None >/dev/null
for name in openai-api-key langfuse-public-key langfuse-secret-key; do
  gcloud secrets add-iam-policy-binding "$name" --member="serviceAccount:$RUN_SA" --role=roles/secretmanager.secretAccessor >/dev/null
done

echo "== 5. Build identity: let Cloud Build push images and deploy (covers both default build accounts)"
for sa in "${NUM}@cloudbuild.gserviceaccount.com" "$RUN_SA"; do
  for role in roles/run.admin roles/iam.serviceAccountUser roles/artifactregistry.writer roles/logging.logWriter; do
    gcloud projects add-iam-policy-binding "$PROJECT_ID" --member="serviceAccount:$sa" --role="$role" --condition=None >/dev/null 2>&1 || true
  done
done

echo "== 6. Teammates: run Gemini locally, see deploys and logs, read the shared keys"
for email in $TEAM; do
  for role in roles/aiplatform.user roles/run.developer roles/logging.viewer roles/cloudbuild.builds.viewer roles/serviceusage.serviceUsageConsumer; do
    gcloud projects add-iam-policy-binding "$PROJECT_ID" --member="user:$email" --role="$role" --condition=None >/dev/null
  done
  for name in openai-api-key langfuse-public-key langfuse-secret-key; do
    gcloud secrets add-iam-policy-binding "$name" --member="user:$email" --role=roles/secretmanager.secretAccessor >/dev/null
  done
  echo "   added $email"
done

echo "== 7. First deploy from your machine (creates the service with the right settings)"
# timeout 900: one scan = one SSE request (default 300 s would cut it off)
# min = max = 1: scan history for the re-scan's before/after lives in memory on one instance
gcloud run deploy "$SERVICE" --source . --region "$REGION" --allow-unauthenticated \
  --timeout=900 --min-instances=1 --max-instances=1 --memory=1Gi \
  --set-secrets=OPENAI_API_KEY=openai-api-key:latest,LANGFUSE_PUBLIC_KEY=langfuse-public-key:latest,LANGFUSE_SECRET_KEY=langfuse-secret-key:latest \
  --set-env-vars=VERTEX_PROJECT="$PROJECT_ID",VERTEX_LOCATION=global,GAUNTLET_FAKE_LLM=0

URL=$(gcloud run services describe "$SERVICE" --region "$REGION" --format='value(status.url)')
echo
echo "Deployed: $URL"
echo "Next: put this URL in README.md and submission.json, then connect the GitHub trigger (docs/SETUP.md step 5)."
