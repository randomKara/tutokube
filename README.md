# Kubernetes Demo Project: Simple Web Application

This project demonstrates basic Kubernetes concepts by deploying a simple web application consisting of a Python/Flask backend API and an Nginx frontend.

## Prerequisites

1.  **Minikube:** Install Minikube to run a local Kubernetes cluster. Follow the official guide: [https://minikube.sigs.k8s.io/docs/start/](https://minikube.sigs.k8s.io/docs/start/)
2.  **Docker:** You need Docker installed as Minikube typically uses it as a driver.
3.  **kubectl alias (Recommended):** To avoid typing `minikube kubectl --` repeatedly, set up an alias in your shell configuration file (like `.bashrc`, `.zshrc`):
    ```bash
    alias kubectl="minikube kubectl --"
    ```
    Remember to reload your shell configuration (`source ~/.bashrc` or open a new terminal) after adding the alias.

## Project Structure

```
howtousekube/
├── backend/
│   ├── app.py           # Flask application
│   ├── Dockerfile       # Docker build file for backend
│   └── requirements.txt # Python dependencies
├── frontend/
│   ├── index.html       # Simple HTML frontend
│   ├── Dockerfile       # Docker build file for frontend
│   └── nginx.conf       # Nginx configuration (reverse proxy)
└── kube/
    ├── backend-deployment.yaml    # Kubernetes Deployment for backend
    ├── backend-service.yaml       # Kubernetes Service for backend
    ├── frontend-deployment.yaml   # Kubernetes Deployment for frontend
    └── frontend-service.yaml      # Kubernetes Service for frontend (LoadBalancer/NodePort)
```

## How to Run

1.  **Start Minikube:**
    ```bash
    minikube start
    ```

2.  **Build Docker Images:**
    Navigate to the project root directory (`howtousekube/`). Build the backend and frontend images using simple local names:
    ```bash
    # Build backend image
    docker build -t kube-demo-backend:latest ./backend

    # Build frontend image
    docker build -t kube-demo-frontend:latest ./frontend
    ```

3.  **Load Images into Minikube:**
    Minikube runs its own Docker environment. You need to load the images you just built from your host's Docker environment into Minikube's environment:
    ```bash
    minikube image load kube-demo-backend:latest
    minikube image load kube-demo-frontend:latest
    ```
    *This step is crucial for Minikube to find the local images.*

4.  **Deploy to Kubernetes:**
    Apply the Kubernetes manifest files located in the `kube/` directory:
    ```bash
    # Apply backend resources
    kubectl apply -f kube/backend-deployment.yaml
    kubectl apply -f kube/backend-service.yaml

    # Apply frontend resources
    kubectl apply -f kube/frontend-deployment.yaml
    kubectl apply -f kube/frontend-service.yaml
    ```

5.  **Verify Deployment:**
    Check if the Pods are running and Services are created:
    ```bash
    kubectl get pods
    kubectl get services
    ```
    Wait until all pods show `STATUS` as `Running`.

6.  **Access the Application:**
    Use the Minikube command to automatically open the application in your browser:
    ```bash
    minikube service frontend-service
    ```
    Alternatively, find the NodePort assigned to `frontend-service` using `kubectl get services` (e.g., `80:32279/TCP`) and access it via `http://$(minikube ip):<NodePort>`.

## How it Works

1.  **User Request:** You access the application via the address provided by `minikube service` or the NodePort.
2.  **Frontend Service:** Kubernetes directs your request to the `frontend-service`. Since it's of type `LoadBalancer` (or could be `NodePort`), Minikube makes it accessible from your host machine.
3.  **Frontend Pod:** The `frontend-service` routes the traffic to one of the `frontend-deployment` pods running Nginx.
4.  **Nginx Serves HTML:** Nginx serves the `index.html` file.
5.  **API Call:** When you click the "Get Message from Backend" button, the JavaScript in `index.html` makes a request to `/api/message`.
6.  **Nginx Proxy:** The Nginx configuration (`nginx.conf`) sees the `/api/` path and proxies the request to `http://backend-service:5000`.
7.  **Backend Service:** Kubernetes DNS resolves `backend-service` to the internal ClusterIP of the `backend-service`. This service load balances the request across the available backend pods.
8.  **Backend Pod:** The `backend-service` routes the request to one of the `backend-deployment` pods running the Flask application on port 5000.
9.  **Flask Response:** The Flask app (`app.py`) handles the `/api/message` route and returns a JSON message.
10. **Response Chain:** The response travels back through the `backend-service`, Nginx proxy, `frontend-service`, and finally to your browser, updating the message display.

This involves several core Kubernetes concepts:
*   **Pods:** The smallest deployable units, running our containers (Flask, Nginx).
*   **Deployments:** Manage Pods, handling scaling (replicas) and updates.
*   **Services:** Provide stable network endpoints (`ClusterIP` for internal communication like `backend-service`, `LoadBalancer`/`NodePort` for external access like `frontend-service`) and basic load balancing.

## Debugging Common Issues

### 1. Pod Status: `ImagePullBackOff` or `ErrImagePull`

*   **Problem:** Kubernetes cannot fetch the container image specified in the Deployment YAML.
*   **Cause (Local Development with Minikube):**
    *   You built the image locally, but didn't load it into Minikube's internal Docker registry (`minikube image load ...`).
    *   Typo in the image name in the Deployment YAML file (`image:` field).
    *   You used the `:latest` tag, rebuilt the image, loaded it, but Kubernetes/Docker still uses a cached older version of `:latest`.
*   **Solutions:**
    *   **Ensure image is loaded:** Always run `minikube image load <image-name>:<tag>` after building.
    *   **Check names:** Double-check the `image:` field in your `*-deployment.yaml` files matches the name used in `docker build`.
    *   **Set `imagePullPolicy`:**
        *   `IfNotPresent` (Default): Only pulls if the image isn't locally present *on the node*. Good, but can be tricky with `:latest` caching. Requires `minikube image load`.
        *   `Always`: Forces Kubernetes to try pulling the image on every pod start. Can sometimes help refresh caches when using `:latest` *if* the image was correctly loaded, but can mask loading issues and slightly slows down pod startup. Still requires `minikube image load`.
    *   **(Best Practice) Use Unique Tags:** Avoid `:latest`. Tag images with unique identifiers (version numbers, timestamps, Git hashes). Example: `docker build -t kube-demo-backend:v1.1 .` then update the `image:` field in the YAML. This makes deployments deterministic and avoids caching issues. When the image tag changes in the YAML, Kubernetes knows it *must* get the new version.

### 2. Pod Status: `CrashLoopBackOff`

*   **Problem:** The container starts, but exits/crashes immediately. Kubernetes tries to restart it, causing a loop.
*   **Cause:** An error within your application code or the container's startup command.
*   **Solution:**
    *   **Check Logs:** Get logs from the crashing pod. This is the most crucial step!
        ```bash
        kubectl logs <pod-name>
        # If it crashes too quickly, check the previous attempt:
        kubectl logs <pod-name> --previous
        ```
    *   **Fix the Error:** Analyze the logs to find the error (e.g., `IndentationError` in Python, missing file, wrong configuration, database connection issue). Fix the code (`app.py`, `nginx.conf`, etc.).
    *   **Rebuild:** Rebuild the Docker image for the component you fixed.
        ```bash
        docker build -t <image-name>:<tag> ./<component-directory>
        ```
    *   **Reload:** Load the new image into Minikube.
        ```bash
        minikube image load <image-name>:<tag>
        ```
    *   **Redeploy:** Kubernetes Deployments will usually automatically roll out the change if you used unique tags. If using `:latest`, you might need to force a rollout or delete the old pods:
        ```bash
        # Option A: Force rollout (good if you didn't change YAML besides maybe code fixes)
        kubectl rollout restart deployment <deployment-name>

        # Option B: Delete pods (Deployment will recreate them)
        kubectl delete pod -l app=<app-label> # e.g., kubectl delete pod -l app=backend

        # Option C: Re-apply YAML (necessary if you changed the YAML, e.g., image tag)
        kubectl apply -f kube/<deployment-file>.yaml
        ```

## Next Steps

This project covers the basics. To explore further, consider:
*   **ConfigMaps:** Externalize configuration from container images.
*   **Secrets:** Manage sensitive data like API keys or passwords.
*   **Volumes/PersistentVolumes:** Add persistent storage (e.g., for a database).
*   **Ingress:** Implement more advanced HTTP routing (hostnames, paths) instead of just `LoadBalancer`/`NodePort`.
*   **Health Checks (Liveness/Readiness Probes):** Help Kubernetes understand if your application is truly healthy.
