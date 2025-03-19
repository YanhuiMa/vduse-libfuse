# compiled the kernel with Eugenio's patch
git clone https://github.com/eugpermar/libfuse/
cd libfuse/
git checkout tags/vduse-20250218 -b vduse-20250218
git branch
git log
mkdir build
cd build/
meson setup /home/libfuse/build /home/libfuse
meson configure
ninja

modprobe vduse

podman run --cpuset-cpus=1 --rm -p 10000:10000 mcr.microsoft.com/azure-storage/azurite azurite-blob --blobHost 0.0.0.0 --blobPort 10000 --inMemoryPersistence --disableProductStyleUrl

#podman run --cpuset-cpus=1 --rm -p 10000:10000 --memory=20g mcr.microsoft.com/azure-storage/azurite azurite-blob --blobHost 0.0.0.0 --blobPort 10000 --disableProductStyleUrl

podman run --privileged --rm -e AZURE_STORAGE_CONNECTION_STRING='DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://10.72.136.66:10000/devstoreaccount1;' -u $(id -u):$(id -g) -v /home/az/:/home/az -e HOME=/home/az -it mcr.microsoft.com/azure-cli:latest az storage container create --name testcontainer

mount -t tmpfs none /mnt/cache/


env AZURE_STORAGE_ACCOUNT_CONTAINER=testcontainer AZURE_STORAGE_ACCOUNT=devstoreaccount1 AZURE_STORAGE_ACCESS_KEY=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw== AZURE_STORAGE_BLOB_ENDPOINT=http://10.72.136.66:10000/devstoreaccount1/ LD_LIBRARY_PATH=/home/libfuse/build/lib taskset --cpu-list 3,5 blobfuse2 mount --tmp-path=/mnt/cache /mnt/mnt/ --foreground

#env AZURE_STORAGE_ACCOUNT_CONTAINER=testcontainer AZURE_STORAGE_ACCOUNT=devstoreaccount1 AZURE_STORAGE_ACCESS_KEY=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw== AZURE_STORAGE_BLOB_ENDPOINT=http://10.72.136.66:10000/devstoreaccount1/ LD_LIBRARY_PATH=/usr/lib64/ taskset --cpu-list 3,5 blobfuse2 mount --tmp-path=/mnt/cache /mnt/mnt/ --foreground


echo '80000000' >  /sys/class/vduse/fsd/vq0/irq_cb_affinity
echo '80000000' >  /sys/class/vduse/fsd/vq1/irq_cb_affinity


fio --randrepeat=1 --time_based=1 --ioengine=io_uring --direct=1 --gtod_reduce=1 --name=test --filename=/mnt/mnt/random_read_write.fio --bs=4k --iodepth=16 --size=256M --readwrite=read --numjobs=2 --runtime=100 --cpus_allowed=7,9 --cpus_allowed_policy=split


screen python3 ConfigTest.py --testcase=fio_perf.single_disk.file_system_block.localfs --guestname=RHEL.9.6.0 --clone=no --nrepeat=4 --machines=q35 --driveformat=virtio_scsi --imageformat=qcow2

sed -i 's/|$//' */fio_result.RHS

python regression.new.libfuse.py qcow2.virtio_scsi.*.x86_64 file /usr/local/autotest/results/1numjob+vanilla+libfuse/ /usr/local/autotest/results/1numjob+vduse+libuse/
