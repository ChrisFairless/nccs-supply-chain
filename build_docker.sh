docker build . -f  "Dockerfile" -t correnticscontainers.azurecr.io/nccs:v2.0.0 --label dockerfile-path=Dockerfile
docker push correnticscontainers.azurecr.io/nccs:v2.0.0

kubectl apply -f deployment.yml