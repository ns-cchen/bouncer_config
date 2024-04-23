import subprocess
import time

from kubernetes import client, config
from kubernetes.stream import stream

mp = input("Enter the mp: ")
base_path = "/Users/cchen/.kube/"
mp_dict = {
    "am2": f"{base_path}c4-am2.yaml",
    "dfw3": f"{base_path}stork-dfw3-mp-prod-dfw3-nc1.yaml",
    "fr4": f"{base_path}c4-fr4.yaml",
    "fra2": f"{base_path}stork-fra2-mp-prod-fra2-nc1.yaml",
    "lon3": f"{base_path}stork-lon3-mp-prod-lon3-nc1.yaml",
    "mel2": f"{base_path}stork-mel2-mp-mel2-nc1.yaml",
    "ruh1": f"{base_path}stork-ruh1-mp-prod-ruh1-nc1.yaml",
    "sin2": f"{base_path}stork-sin2-mp-prod-sin2-nc1.yaml",
    "sjc1": f"{base_path}c4-sjc1.yaml",
    "sjc2": f"{base_path}stork-sjc2-mp-prod-sjc2-nc1.yaml",
    "sv5": f"{base_path}c1-sv5.yaml",
    "zur2": f"{base_path}stork-zur2-mp-prod-zur2-nc1.yaml",
    "qa.local": f"{base_path}c1-iad0-qa.yaml"
}
kubeconfig_path = mp_dict[mp]

config.load_kube_config(config_file=kubeconfig_path)
core_v1 = client.CoreV1Api()
namespace = "queryservice"
pod_prefix = "bouncer"

print(f"Available pods starting with '{pod_prefix}':")
pods = [pod for pod in core_v1.list_namespaced_pod(namespace=namespace).items if
        pod.metadata.name.startswith(pod_prefix)]
for i, pod in enumerate(pods, start=1):
    print(f"{i}. {pod.metadata.name}")

pod_name = None
while True:
    try:
        pod_choice = int(input("Enter the number of the pod you want to use: "))
        if 1 <= pod_choice <= len(pods):
            pod_name = pods[pod_choice - 1].metadata.name
            break
        else:
            print("Invalid choice. Please try again.")
    except ValueError:
        print("Invalid input. Please enter a number.")

print(f"Available options:")
print("1. Modify bouncer_config.yaml")
print("2. Restart bouncer")
option = input("Enter the option: ")

if option == "1":
    step = 1
    while True:
        if step == 1:
            # Step 1
            print("Step 1: Creating a test folder in /tmp")
            command = ["/bin/bash", "-c", "mkdir /tmp/test"]

            resp = core_v1.read_namespaced_pod(name=pod_name, namespace=namespace)
            resp = stream(core_v1.connect_get_namespaced_pod_exec,
                          pod_name,
                          namespace,
                          command=command,
                          stderr=True, stdin=False,
                          stdout=True, tty=False)

            next_step = input("Step 1 completed. Type 'y' to proceed to the next step: ")
            if next_step.lower() != 'y':
                break
            step += 1

        elif step == 2:
            # Step 2
            print("Step 2: Downloading bouncer_config.yaml in /tmp/test")
            command = ["/bin/bash", "-c",
                       "curl 'http://cfgpusher:8887/file/opt/ns/cfg/bouncer_config.yaml' > /tmp/test/bouncer_config.yaml"]
            resp = core_v1.read_namespaced_pod(name=pod_name, namespace=namespace)
            resp = stream(core_v1.connect_get_namespaced_pod_exec,
                          pod_name,
                          namespace,
                          command=command,
                          stderr=True, stdin=False,
                          stdout=True, tty=False)

            next_step = input("Step 2 completed. Type 'y' to proceed to the next step: ")
            if next_step.lower() != 'y':
                break
            step += 1

        elif step == 3:
            # Step 3
            print("Step 3: Downloading bouncer_config.yaml from the pod")
            remote_path = "/tmp/test/bouncer_config.yaml"
            local_path = input("Enter the local path to save the file (e.g., /path/to/local/file.txt): ")
            try:
                command = f"kubectl --kubeconfig {kubeconfig_path} --namespace {namespace} cp {pod_name}:{remote_path} {local_path}"
                subprocess.run(command.split())
            except Exception as e:
                print(f"Error downloading file: {e}")
            next_step = input(
                f"Step 3 completed. Please modify bouncer_config.yaml in {local_path} and type 'y' to proceed to the next step:")
            if next_step.lower() != 'y':
                break
            step += 1
        elif step == 4:
            # Step4
            print(f"Step 4: Uploading a file to the pod {pod_name}")
            local_path = input("Enter the local path of the file to upload (e.g., /path/to/local/file.txt): ")
            remote_path = "/tmp/test/bouncer_config.yaml"

            # Upload the file to the pod
            try:
                command = f"kubectl --kubeconfig {kubeconfig_path} --namespace {namespace} cp {local_path} {pod_name}:{remote_path}"
                subprocess.run(command.split())

                print(f"File uploaded from {local_path} to {remote_path} in the pod {pod_name}")
            except Exception as e:
                print(f"Error uploading file: {e}")

            next_step = input("Step 4 completed. Type 'y' to proceed to the next step: ")
            if next_step.lower() != 'y':
                break
            step += 1
        elif step == 5:
            # Step 5
            print("Step 5: Diff config between /tmp/test/bouncer_config.yaml and /opt/ns/cfg/bouncer_config.yaml")
            command = ["/bin/bash", "-c",
                       "diff /tmp/test/bouncer_config.yaml /opt/ns/cfg/bouncer_config.yaml"]
            resp = core_v1.read_namespaced_pod(name=pod_name, namespace=namespace)
            resp = stream(core_v1.connect_get_namespaced_pod_exec,
                          pod_name,
                          namespace,
                          command=command,
                          stderr=True, stdin=False,
                          stdout=True, tty=False)

            for line in resp:
                print(line, end='')

            next_step = input(
                "Step 5 completed. Type 'y' to proceed to the next step: ")
            if next_step.lower() != 'y':
                break
            step += 1
        elif step == 6:
            # Step 6
            print("Step 6: Uploading /tmp/test/bouncer_config.yaml")
            command = ["/bin/bash", "-c",
                       "curl --data-binary @/tmp/test/bouncer_config.yaml -XPUT 'http://cfgpusher:8887/file/opt/ns/cfg/bouncer_config.yaml'"]
            resp = core_v1.read_namespaced_pod(name=pod_name, namespace=namespace)
            resp = stream(core_v1.connect_get_namespaced_pod_exec,
                          pod_name,
                          namespace,
                          command=command,
                          stderr=True, stdin=False,
                          stdout=True, tty=False)

            next_step = input("Step 6 completed. Type 'y' to proceed to the next step: ")
            if next_step.lower() != 'y':
                break
            step += 1
        elif step == 7:
            # Step 7
            print("Step 7: Diff config between /tmp/test/bouncer_config.yaml and /opt/ns/cfg/bouncer_config.yaml")
            command = ["/bin/bash", "-c", "diff /tmp/test/bouncer_config.yaml /opt/ns/cfg/bouncer_config.yaml"]
            resp = core_v1.read_namespaced_pod(name=pod_name, namespace=namespace)
            resp = stream(core_v1.connect_get_namespaced_pod_exec,
                          pod_name,
                          namespace,
                          command=command,
                          stderr=True, stdin=False,
                          stdout=True, tty=False)

            for line in resp:
                print(line, end='')

            next_step = input(
                "Step 7 completed. Type 'y' to proceed to the next step: ")
            if next_step.lower() != 'y':
                break
            step += 1
        else:
            print("All steps completed.")
            break
elif option == "2":
    step = 1
    while True:
        if step == 1:
            print(f"Step 1: Finding and killing a process in pod {pod_name}")

            try:
                find_proc_cmd = f"kubectl exec {pod_name} -n {namespace} -c bouncer -- ps aux | grep /app/bouncer | grep -v grep"
                proc_output = subprocess.check_output(find_proc_cmd, shell=True, universal_newlines=True)

                print(proc_output)
                pid = input("Enter the PID of the process you want to kill: ")
                # Kill the process
                kill_proc_cmd = f"kubectl exec {pod_name} -n {namespace} -c bouncer -- kill {pid}"
                subprocess.run(kill_proc_cmd, shell=True, check=True)
                print(f"Process with PID {pid} killed successfully.")

            except subprocess.CalledProcessError as e:
                print(f"Error executing command: {e}")

            next_step = input("Step 1 completed. Type 'y' to proceed to the next step: ")
            if next_step.lower() != 'y':
                break

            step += 1
        elif step == 2:
            print(f"Step 2: Waiting for pod {pod_name} to become ready...")
            pod_ready = False
            while not pod_ready:
                pod = core_v1.read_namespaced_pod(name=pod_name, namespace=namespace)
                pod_ready = all(container.ready for container in pod.status.container_statuses)
                time.sleep(5)

            print(f"Pod {pod_name} is ready.")
        else:
            print("All steps completed.")
            break
