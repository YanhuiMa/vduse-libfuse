import logging
import os
import re
import threading
import time

import six
from avocado.utils import process
from virttest import (
    data_dir,
    error_context,
    utils_disk,
    utils_misc,
    utils_numeric,
    utils_test,
)

from provider.storage_benchmark import generate_instance

LOG_JOB = logging.getLogger("avocado.test")


def format_result(result, base="12", fbase="2"):
    """
    Format the result to a fixed length string.

    :param result: result need to convert
    :param base: the length of converted string
    :param fbase: the decimal digit for float
    """
    if isinstance(result, six.string_types):
        value = "%" + base + "s"
    elif isinstance(result, int):
        value = "%" + base + "d"
    elif isinstance(result, float):
        value = "%" + base + "." + fbase + "f"
    else:
        raise TypeError(f"unexpected result type: {type(result).__name__}")
    return value % result



@error_context.context_aware
def run(test, params, env):
    """
    Block performance test with fio
    Steps:
    1) boot up guest with one data disk on specified backend and pin qemu-kvm
       process to the last numa node on host
    2) pin guest vcpu and vhost threads to cpus of last numa node repectively
    3) format data disk and run fio in guest
    4) collect fio results and host info

    :param test: QEMU test object
    :param params: Dictionary with the test parameters
    :param env: Dictionary with test environment
    """

    def fio_thread():
        """
        run fio command 
        """
        process.system(run_fio_options, timeout=360, shell=True)



    process.system_output("numactl --hardware")

    # get parameter from dictionary
    fio_options = params["fio_options"]
    rw = params["rw"]
    block_size = params["block_size"]
    iodepth = params["iodepth"]
    threads = params["threads"]
    cmd_timeout = int(params.get("cmd_timeout", 1200))
    order_list = params["order_list"]
    driver_format = params.get("drive_format")
    kvm_ver_chk_cmd = params.get("kvm_ver_chk_cmd")
    pattern = params["pattern"]
    guest_result_file = params["guest_result_file"]
    format = params.get("format")
    os_type = params.get("os_type", "linux")
    drop_cache = params.get("drop_cache")
    num_disk = params.get("num_disk")
    driver_verifier_query = params.get("driver_verifier_query")
    verifier_clear_cmd = params.get("verifier_clear_cmd")
    vfsd_ver_chk_cmd = params.get("vfsd_ver_chk_cmd")
    delete_test_file = params.get("delete_test_file", "no")

    result_path = utils_misc.get_path(test.resultsdir, "fio_result.RHS")
    result_file = open(result_path, "w")
    test.log.info("yama_result_file is: %s", result_file)


    host_ver = os.uname()[2]

    result_file.write("### kvm_version : %s\n" % host_ver)



    # get order_list
    order_line = ""
    for order in order_list.split():
        order_line += "%s|" % format_result(order)

    # get result tested by each scenario
    try:
        for io_pattern in rw.split():
            result_file.write("Category:%s\n" % io_pattern)
            result_file.write("%s\n" % order_line.rstrip("|"))
            for bs in block_size.split():
                for io_depth in iodepth.split():
                    for numjobs in threads.split():
                        line = ""
                        line += "%s|" % format_result(bs[:-1])
                        line += "%s|" % format_result(io_depth)
                        line += "%s|" % format_result(numjobs)
                        file_name = None
                        if format == "True" or params.objects("filesystems"):
                            file_name = io_pattern + "_" + bs + "_" + io_depth
                            run_fio_options = fio_options % (
                                io_pattern,
                                bs,
                                io_depth,
                                file_name,
                                numjobs,
                            )

                        test.log.info("run_fio_options are: %s", run_fio_options)
                        process.system_output(drop_cache, shell=True)
                        cpu_file = os.path.join(data_dir.get_tmp_dir(), "cpus")
                        fio_t = threading.Thread(target=fio_thread)
                        fio_t.start()
                        process.system_output("mpstat 1 60 > %s" % cpu_file, shell=True)
                        fio_t.join()
                        if file_name and delete_test_file == "yes":
                            test.log.info("Ready delete: %s", file_name)
                            session.cmd("rm -rf /mnt/%s" % file_name)

                        fio_result_file = os.path.join("/var/tmp/", "fio_result")
                        o = process.system_output(
                            "egrep '(read|write)' %s" % fio_result_file
                        ).decode()
                        results = re.findall(pattern, o)
                        bw = float(utils_numeric.normalize_data_size(results[0][1]))
                        iops = float(
                            utils_numeric.normalize_data_size(
                                results[0][0], order_magnitude="B", factor=1000
                            )
                        )
                        if re.findall("rw", io_pattern):
                            bw = bw + float(
                                utils_numeric.normalize_data_size(results[1][1])
                            )
                            iops = iops + float(
                                utils_numeric.normalize_data_size(
                                    results[1][0], order_magnitude="B", factor=1000
                                )
                            )

                        ret = process.system_output("tail -n 1 %s" % cpu_file)
                        idle = float(ret.split()[-1])
                        iowait = float(ret.split()[5])
                        cpu = 100 - idle - iowait
                        normal = bw / cpu
                        for result in bw, iops, cpu, normal:
                            line += "%s|" % format_result(result)
                        result_file.write("%s\n" % line)
                        process.system("rm -f /mnt/mnt/%s" % file_name)
                        process.system("rm -rf %s" % guest_result_file)

    # del temporary files in guest os
    #process.system("rm -rf %s" % guest_result_file)
    finally:
        result_file.close()
