fusermount -u /mnt/mnt

umount /mnt/cache

podman run --rm -e AZURE_STORAGE_CONNECTION_STRING='DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://10.72.136.66:10000/devstoreaccount1;' mcr.microsoft.com/azure-cli:latest az storage container delete --name testcontainer
{
  "deleted": true
}


podman ps
CONTAINER ID  IMAGE                                           COMMAND               CREATED         STATUS         PORTS                                      NAMES
ed8a437628f3  mcr.microsoft.com/azure-storage/azurite:latest  azurite-blob --bl...  34 minutes ago  Up 34 minutes  0.0.0.0:10000->10000/tcp, 10001-10002/tcp  great_yalow


podman stop ed8a437628f3
