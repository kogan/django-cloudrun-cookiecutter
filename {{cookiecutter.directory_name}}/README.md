# {{cookiecutter.application_name}}

A repo to kickstart a django project running on GCP (CloudRun).

Heavily inspired from [https://github.com/GoogleCloudPlatform/django-demo-app-unicodex](https://github.com/GoogleCloudPlatform/django-demo-app-unicodex), where we've optimised for our use case.

It's recommended to read the above first to gain an understanding of how the deployment is structured.

## I've cut this project. What now?

1. Create a project (`{{cookiecutter.project_name}}`) via the Google Cloud Console web interface. Take note of the project id, then run the following to set up the account:

```
export PROJECT_ID={{cookiecutter.project_name}}
export REGION={{cookiecutter.gcp_region}}
export SERVICE_NAME={{cookiecutter.application_name}}-app
export CLOUDRUN_SA=${SERVICE_NAME}@${PROJECT_ID}.iam.gserviceaccount.com
export PROJECTNUM=$(gcloud projects describe ${PROJECT_ID} --format 'value(projectNumber)')
export CLOUDBUILD_SA=${PROJECTNUM}@cloudbuild.gserviceaccount.com

export INSTANCE_NAME={{cookiecutter.application_name}}-db
export DATABASE_NAME={{cookiecutter.application_name}}
export DATABASE_INSTANCE=$PROJECT_ID:$REGION:$INSTANCE_NAME
export ROOT_PASSWORD=$(python -c "import secrets; print(secrets.token_urlsafe(50))")
export DBUSERNAME=django
export DBPASSWORD=$(python -c "import secrets; print(secrets.token_urlsafe(50))")
export DATABASE_URL=postgres://$DBUSERNAME:${DBPASSWORD}@//cloudsql/$PROJECT_ID:$REGION:$INSTANCE_NAME/$DATABASE_NAME

export SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(50))")

gcloud config set project $PROJECT_ID
gcloud config set run/platform managed
gcloud config set run/region $REGION
gcloud services enable \
  run.googleapis.com \
  iam.googleapis.com \
  compute.googleapis.com \
  sql-component.googleapis.com \
  sqladmin.googleapis.com \
  cloudbuild.googleapis.com \
  cloudkms.googleapis.com \
  cloudresourcemanager.googleapis.com \
  secretmanager.googleapis.com
gcloud iam service-accounts create $SERVICE_NAME \
  --display-name "$SERVICE_NAME service account"
  
for role in cloudsql.client run.admin; do
  gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member serviceAccount:$CLOUDRUN_SA \
    --role roles/${role}
done

gcloud secrets create SECRET_KEY --replication-policy automatic
gcloud secrets create DATABASE_URL --replication-policy automatic
echo -n "${SECRET_KEY}" | gcloud secrets versions add SECRET_KEY --data-file=-
echo -n "${DATABASE_URL}" | gcloud secrets versions add DATABASE_URL --data-file=-
gcloud secrets add-iam-policy-binding SECRET_KEY \
  --member serviceAccount:$CLOUDRUN_SA \
  --role roles/secretmanager.secretAccessor
  
  gcloud secrets add-iam-policy-binding SECRET_KEY \
  --member serviceAccount:$CLOUDBUILD_SA \
  --role roles/secretmanager.secretAccessor
gcloud secrets add-iam-policy-binding DATABASE_URL \
  --member serviceAccount:$CLOUDRUN_SA \
  --role roles/secretmanager.secretAccessor
  
  gcloud secrets add-iam-policy-binding DATABASE_URL \
  --member serviceAccount:$CLOUDBUILD_SA \
  --role roles/secretmanager.secretAccessor
```

3. Navigate to [https://console.cloud.google.com/sql/create-instance-postgres](https://console.cloud.google.com/sql/create-instance-postgres) to create the instance of desired capacity, then run the following:

```
gcloud sql databases create $DATABASE_NAME \
  --instance=$INSTANCE_NAME

gcloud sql connect $INSTANCE_NAME

CREATE USER "django" WITH PASSWORD '<DBPASSWORD>';
GRANT ALL PRIVILEGES ON DATABASE "{{cookiecutter.application_name}}" TO "django";
```

4. Deploy the application for the first time:

```
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME .
```

5. Navigate to https://console.cloud.google.com/run and follow the prompts.
Be sure to choose the right region and service account, and to connect the DB.

Once provisioned, you’ll need to update the env var CURRENT_HOST to the host it just generated.
You’re done! 

## Ongoing deployment

There's a configuration file in `.cloudbuild/deploy.yaml` which builds, pushes, migrates, and deploys.
Follow the guide in [https://github.com/GoogleCloudPlatform/django-demo-app-unicodex](https://github.com/GoogleCloudPlatform/django-demo-app-unicodex) to learn how to automate this!

## First time setup

```
./dev_setup.sh
```

browse to http://localhost:8317

## Cloud shell

The `cloudshell.py` script allows you to connect to GCP resources from your local machine.
In the old server world, this would be close enough to ssh-ing into your production app.

It works by pulling your docker image from `gcr.io` and runs it with your personal credentials.

-------

Please ensure you have install the google-cloud-sdk first (linux users, dont use the snap)

An environment variable `GOOGLE_APPLICATION_CREDENTIALS` needs to be set pointing to your credentials.
These credentials can be generated with the command:

`gcloud auth application-default login`

Add this to your bash or equivalent .bashrc file:
```
export GOOGLE_APPLICATION_CREDENTIALS=$HOME/.config/gcloud/application_default_credentials.json
```

You'll also need to configure docker to be able to talk to GCR.

`gcloud auth configure-docker`

`cloudshell.py` allows connectivity with a Django shell as well as a PSQL client for production and UAT environments.

`./bin/cloudshell.py [shell|psql]`

