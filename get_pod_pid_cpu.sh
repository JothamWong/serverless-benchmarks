#!/bin/sh
#!/bin/sh

set -e
POD_NAME=$1
NAMESPACE=${2:-openwhisk}

# Check if POD_NAME is provided
if [ -z "$POD_NAME" ]; then
    echo "Usage: $0 <pod_name> [namespace]"
    exit 1
fi

# Get the name of the container running in the pod
CONTAINER_NAME=$(kubectl get pod "$POD_NAME" -n "$NAMESPACE" -o jsonpath="{.spec.containers[0].name}")

# Get the PID of the main process inside the container
PID=$(kubectl exec -n "$NAMESPACE" "$POD_NAME" -c "$CONTAINER_NAME" -- sh -c 'echo $$')

# Check if PID was found
if [ -z "$PID" ]; then
    echo "No process found for pod name $POD_NAME in namespace $NAMESPACE"
    exit 1
fi

# Get the CPU affinity of the PID
CPU=$(kubectl exec -n "$NAMESPACE" "$POD_NAME" -c "$CONTAINER_NAME" -- taskset -cp "$PID" | awk -F": " '{print $2}')

# Print the CPU affinity (for debugging purposes)
echo "Process in pod $POD_NAME (PID: $PID) is running on CPU: $CPU"
