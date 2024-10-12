# Deployment with GCP

## Utilization Cloud Run
- Prequests:
    - Need to push image to a registry, like docker hub 
        - e.g., `docker buildx build --platform linux/amd64 -t linkchecker .` # this is important for building on a M1/M2 processor 
        - e.g., `docker tag linkchecker hants/linkchecker`
        - e.g., `docker push hants/linkchecker`
    - In the current iteration, have pushed image to docker hub (docker.io/hants/sdoh-demo)

- Steps:
    - Create a new service in Cloud Run
    - Select the image from the registry
    - Set the port in the image to match the port in the Cloud Run service, which currently is 5009