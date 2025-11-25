import random
import docker
from docker.errors import ImageNotFound, ContainerError
import os

def evaluate(test_annotation_file, user_submission_file, phase_codename, **kwargs):
    print("Starting Evaluation.....")
    docker_host = os.environ.get('DOCKER_HOST')
    if docker_host and 'http+docker' in docker_host:
        del os.environ['DOCKER_HOST']

    image_name = "hello-world"
    tag = "latest"
    full_image_name = f"{image_name}:{tag}"
    """
    Evaluates the submission for a particular challenge phase and returns score
    Arguments:

        `test_annotations_file`: Path to test_annotation_file on the server
        `user_submission_file`: Path to file submitted by the user
        `phase_codename`: Phase to which submission is made

        `**kwargs`: keyword arguments that contains additional submission
        metadata that challenge hosts can use to send slack notification.
        You can access the submission metadata
        with kwargs['submission_metadata']

        Example: A sample submission metadata can be accessed like this:
        >>> print(kwargs['submission_metadata'])
        {
            'status': u'running',
            'when_made_public': None,
            'participant_team': 5,
            'input_file': 'https://abc.xyz/path/to/submission/file.json',
            'execution_time': u'123',
            'publication_url': u'ABC',
            'challenge_phase': 1,
            'created_by': u'ABC',
            'stdout_file': 'https://abc.xyz/path/to/stdout/file.json',
            'method_name': u'Test',
            'stderr_file': 'https://abc.xyz/path/to/stderr/file.json',
            'participant_team_name': u'Test Team',
            'project_url': u'http://foo.bar',
            'method_description': u'ABC',
            'is_public': False,
            'submission_result_file': 'https://abc.xyz/path/result/file.json',
            'id': 123,
            'submitted_at': u'2017-03-20T19:22:03.880652Z'
        }
    """
    try:
        # 1. Connect to Docker client
        # By default, it looks for the DOCKER_HOST environment variable or
        # common locations like /var/run/docker.sock on Linux or the DOCKER_HOST on Windows/Mac.
        print("Connecting to Docker client...")
        client = docker.from_env()
        
        # 2. Pull the image if not present (or simply to ensure it's up-to-date)
        try:
            print(f"Attempting to pull the image '{full_image_name}'...")
            client.images.pull(image_name, tag=tag)
            print("Image pulled successfully.")
        except ImageNotFound:
            print(f"Image '{full_image_name}' could not be found or pulled.")
            return

        # 3. Run the container
        print(f"Running container from image '{full_image_name}'...")
        
        # client.containers.run() is a convenient method that:
        # - Creates the container.
        # - Starts it.
        # - Waits for it to finish (due to detach=False, the default).
        # - Collects its logs.
        # - Returns the Container object.
        container = client.containers.run(
            image=full_image_name,
            detach=True,  # Run in background to easily manage its lifecycle
            remove=False  # Do not auto-remove yet, so we can inspect logs/status
        )

        print(f"Container started successfully. ID: {container.short_id}")
        
        # Wait for the container to finish and update its status
        container.wait() 
        
        # Reload the container object to get the latest status
        container.reload()

        # 4. Get and decode the logs
        print("\n[INFO] Container Output (Logs):")
        # logs() returns raw bytes, decode them for human readability
        logs = container.logs().decode('utf-8')
        print(logs)

        print(f"[INFO] Container finished execution. Status: {container.status}")
        
        # 5. Clean up: remove the container after completion
        print(f"Removing container {container.short_id}...")
        container.remove()
        print("Container removed.")

    except docker.errors.APIError as e:
        print(f"Docker API Error: Could not connect to the Docker daemon. "
                      f"Ensure Docker is running and configured correctly. Details: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    output = {}
    if phase_codename == "dev":
        print("Evaluating for Dev Phase")
        output["result"] = [
            {
                "train_split": {
                    "Metric1": random.randint(0, 99),
                    "Metric2": random.randint(0, 99),
                    "Metric3": random.randint(0, 99),
                    "Total": random.randint(0, 99),
                }
            }
        ]
        # To display the results in the result file
        output["submission_result"] = output["result"][0]["train_split"]
        print("Completed evaluation for Dev Phase")
    elif phase_codename == "test":
        print("Evaluating for Test Phase")
        output["result"] = [
            {
                "train_split": {
                    "Metric1": random.randint(0, 99),
                    "Metric2": random.randint(0, 99),
                    "Metric3": random.randint(0, 99),
                    "Total": random.randint(0, 99),
                }
            },
            {
                "test_split": {
                    "Metric1": random.randint(0, 99),
                    "Metric2": random.randint(0, 99),
                    "Metric3": random.randint(0, 99),
                    "Total": random.randint(0, 99),
                }
            },
        ]
        # To display the results in the result file
        output["submission_result"] = output["result"][0]
        print("Completed evaluation for Test Phase")
    return output
